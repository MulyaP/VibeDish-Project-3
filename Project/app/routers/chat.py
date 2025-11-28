from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
import uuid

from ..services.chat_service import generate_reply_with_groq, generate_title_with_groq
from ..services.chat_persistence import (
    create_session,
    append_message,
    get_history,
    session_belongs_to_user,
    get_sessions_for_user,
    update_session_title,
    delete_session,
)
from ..auth import current_user

router = APIRouter()


class SendRequest(BaseModel):
    session_id: Optional[str] = None
    message: str
    context: Optional[dict] = None


class SendResponse(BaseModel):
    session_id: str
    message_id: str
    reply: str
    provider_info: Optional[dict] = None
    title: Optional[str] = None
    title_provider_info: Optional[dict] = None


@router.post("/messages", response_model=SendResponse)
async def send_message(req: SendRequest, user: dict = Depends(current_user)):
    """Send a message to the configured provider (GROQ).

    This will call the `GroqProvider` service. For the MVP the provider
    takes the last user message as the prompt; we'll expand history handling
    and persistence in subsequent steps.
    """
    session_id = req.session_id or str(uuid.uuid4())
    message_id = str(uuid.uuid4())

    # Track whether this request created a brand-new session so we can try to
    # auto-generate a short title immediately from the user's initial message.
    new_session = False

    # 1) Ensure session exists and is owned by the authenticated user
    if not req.session_id:
        req.session_id = create_session(user_id=user.get("id"))
        session_id = req.session_id
        new_session = True
    else:
        # if session_id provided, ensure it belongs to this user
        if not session_belongs_to_user(req.session_id, user.get("id")):
            raise HTTPException(status_code=403, detail="Session does not belong to the authenticated user")
        session_id = req.session_id

    # 2) Persist the incoming user message
    user_msg_id = append_message(session_id, "user", req.message)

    # 3) Fetch recent history and format for provider
    raw_history = get_history(session_id, limit=200)
    session_messages = []
    for m in raw_history:
        session_messages.append({"role": m.get("role"), "content": m.get("content")})

    # If this is a newly-created session, try to generate a short title now
    # from the available messages (which include the user's initial message we
    # just persisted). This ensures the session heading is available immediately
    # in the UI instead of waiting until after the assistant reply.
    if new_session:
        try:
            try:
                result = await generate_title_with_groq(session_messages)
            except Exception:
                result = {"title": None, "provider_info": None}
            title_pre = result.get("title") if isinstance(result, dict) else None
            if title_pre:
                try:
                    update_session_title(session_id, title_pre)
                except Exception:
                    # ignore DB failures for title update
                    pass
        except Exception:
            # swallow all title-generation failures to avoid impacting the
            # primary send flow
            pass

    # 4) Call provider with history
    try:
        result = await generate_reply_with_groq(session_messages, req.message, req.context)
    except Exception as exc:
        # provider failed: leave user message persisted, return 502
        raise HTTPException(status_code=502, detail=str(exc))

    reply_text = result.get("reply")
    provider_info = result.get("provider_info")

    # 5) Persist assistant reply (store provider_info)
    # try to extract completion token count if available
    token_count = None
    try:
        usage = provider_info.get("usage") if isinstance(provider_info, dict) else None
        if usage:
            token_count = int(usage.get("completion_tokens") or usage.get("total_tokens") or 0)
    except Exception:
        token_count = None

    assistant_msg_id = append_message(session_id, "assistant", reply_text, provider_info=provider_info, token_count=token_count)

    # Try to auto-generate a short session title when the session was newly created.
    # We do this after persisting the assistant reply so we have content to summarize.
    title_post = None
    title_provider_info = None
    try:
        # Build a compact history to pass to the title generator (include recent messages)
        try:
            # pass raw_history plus the latest assistant reply for context
            messages_for_title = session_messages + [{"role": "assistant", "content": reply_text}]
            result = await generate_title_with_groq(messages_for_title)
        except Exception:
            result = {"title": None, "provider_info": None}

        if isinstance(result, dict):
            title_post = result.get("title")
            title_provider_info = result.get("provider_info")

        if title_post:
            # best-effort: update DB title (ignore failures)
            try:
                update_session_title(session_id, title_post)
            except Exception:
                pass
    except Exception:
        # swallow errors to avoid impacting main flow
        pass

    return SendResponse(
        session_id=session_id,
        message_id=assistant_msg_id,
        reply=reply_text,
        provider_info=provider_info,
        title=(title_post or (locals().get('title_pre') if 'title_pre' in locals() else None)),
        title_provider_info=title_provider_info,
    )


@router.get("/history")
async def get_history_route(session_id: Optional[str] = None, user: dict = Depends(current_user)):
    """Return persisted history for a session (reads from Supabase).

    Use `session_id` query param to fetch messages for a given session.
    """
    if not session_id:
        return {"session_id": None, "messages": []}

    # Ensure the requesting user owns the session
    if not session_belongs_to_user(session_id, user.get("id")):
        raise HTTPException(status_code=403, detail="Session does not belong to the authenticated user")

    try:
        from ..services.chat_persistence import get_history as _get_history

        messages = _get_history(session_id)
        return {"session_id": session_id, "messages": messages}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/sessions")
async def list_sessions(limit: int = 50, offset: int = 0, user: dict = Depends(current_user)):
    """List chat sessions for the authenticated user.

    Returns sessions ordered by created_at desc with a `last_message` preview.
    Pagination via `limit` and `offset`.
    """
    try:
        sessions = get_sessions_for_user(user.get("id"), limit=limit, offset=offset)
        return {"sessions": sessions}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


class CreateSessionRequest(BaseModel):
    title: Optional[str] = None


@router.post("/sessions")
async def create_session_route(req: CreateSessionRequest, user: dict = Depends(current_user)):
    """Create a new chat session for the authenticated user."""
    try:
        sid = create_session(user_id=user.get("id"), title=req.title)
        return {"session_id": sid}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


class UpdateSessionRequest(BaseModel):
    title: Optional[str] = None


@router.patch("/sessions/{session_id}")
async def update_session_route(session_id: str, req: UpdateSessionRequest, user: dict = Depends(current_user)):
    """Update session metadata (title) — owner only."""
    if not session_belongs_to_user(session_id, user.get("id")):
        raise HTTPException(status_code=403, detail="Session does not belong to the authenticated user")
    try:
        ok = update_session_title(session_id, req.title)
        if not ok:
            raise HTTPException(status_code=500, detail="Failed to update session")
        return {"session_id": session_id, "title": req.title}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.delete("/sessions/{session_id}")
async def delete_session_route(session_id: str, user: dict = Depends(current_user)):
    """Delete a session and its messages — owner only."""
    if not session_belongs_to_user(session_id, user.get("id")):
        raise HTTPException(status_code=403, detail="Session does not belong to the authenticated user")
    try:
        ok = delete_session(session_id)
        if not ok:
            raise HTTPException(status_code=500, detail="Failed to delete session")
        return {"deleted": True}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
