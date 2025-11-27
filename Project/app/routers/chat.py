from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import uuid

from ..services.chat_service import generate_reply_with_groq

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


@router.post("/messages", response_model=SendResponse)
async def send_message(req: SendRequest):
    """Send a message to the configured provider (GROQ).

    This will call the `GroqProvider` service. For the MVP the provider
    takes the last user message as the prompt; we'll expand history handling
    and persistence in subsequent steps.
    """
    session_id = req.session_id or str(uuid.uuid4())
    message_id = str(uuid.uuid4())

    session_messages = [{"role": "user", "content": req.message}]

    try:
        result = await generate_reply_with_groq(session_messages, req.message, req.context)
    except Exception as exc:
        # bubble up a clear error so the developer can diagnose missing env vars or provider errors
        raise HTTPException(status_code=502, detail=str(exc))

    reply_text = result.get("reply")
    provider_info = result.get("provider_info")

    return SendResponse(
        session_id=session_id,
        message_id=message_id,
        reply=reply_text,
        provider_info=provider_info,
    )


@router.get("/history")
async def get_history(session_id: Optional[str] = None):
    """Return an empty history for now (placeholder)."""
    return {"session_id": session_id, "messages": []}
