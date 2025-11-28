from typing import Any, Dict, List, Optional
from uuid import uuid4

from ..db import get_db


def create_session(user_id: Optional[str] = None, title: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> str:
    """Create a new chat session and return its id.

    Uses the Supabase client already configured in `app.db`.
    """
    supabase = get_db()
    session_id = str(uuid4())
    payload = {"id": session_id, "user_id": user_id, "title": title, "metadata": metadata or {}}
    supabase.table("chat_sessions").insert(payload).execute()
    return session_id


def append_message(
    session_id: str,
    role: str,
    content: str,
    provider_info: Optional[Dict[str, Any]] = None,
    token_count: Optional[int] = None,
) -> str:
    """Append a message to a session and return the message id."""
    supabase = get_db()
    message_id = str(uuid4())
    payload = {
        "id": message_id,
        "session_id": session_id,
        "role": role,
        "content": content,
        "provider_info": provider_info or {},
        "token_count": token_count,
    }
    supabase.table("chat_messages").insert(payload).execute()
    return message_id


def get_history(session_id: str, limit: int = 100) -> List[Dict[str, Any]]:
    """Return a list of messages for the session ordered by created_at asc.

    If the DB has no created_at ordering, this returns rows in insertion order.
    """
    supabase = get_db()
    # supabase-py order() expects a 'desc' keyword boolean rather than an options dict
    r = (
        supabase
        .table("chat_messages")
        .select("id,role,content,created_at,provider_info,token_count")
        .eq("session_id", session_id)
        .order("created_at", desc=False)
        .limit(limit)
        .execute()
    )
    # supabase returns {'data': [...]} on success
    return r.data or []


def session_belongs_to_user(session_id: str, user_id: Optional[str]) -> bool:
    """Return True if the session is owned by the given user_id.

    If the session row has a NULL/None user_id, this will only return True
    when the provided user_id is also None. Otherwise returns False.
    """
    supabase = get_db()
    r = supabase.table("chat_sessions").select("user_id").eq("id", session_id).limit(1).execute()
    data = r.data or []
    if not data:
        return False
    row = data[0]
    session_user_id = row.get("user_id")
    # Normalize types to string or None
    if session_user_id is None and user_id is None:
        return True
    if session_user_id is None and user_id is not None:
        return False
    return str(session_user_id) == str(user_id)


def get_sessions_for_user(user_id: str, limit: int = 50, offset: int = 0):
    """Return a list of sessions for the given user with a last_message preview.

    Each session dict contains: id, user_id, title, metadata, created_at, last_message
    where last_message is either a message dict or None.
    """
    supabase = get_db()
    # 1) fetch sessions for user
    r = (
        supabase
        .table("chat_sessions")
        .select("id,user_id,title,metadata,created_at")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    sessions = r.data or []

    # 2) for each session, fetch latest message preview
    out = []
    for s in sessions[offset:]:
        sid = s.get("id")
        last = (
            supabase
            .table("chat_messages")
            .select("id,role,content,created_at,provider_info,token_count")
            .eq("session_id", sid)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        last_rows = last.data or []
        last_msg = last_rows[0] if last_rows else None
        out.append({
            "id": sid,
            "user_id": s.get("user_id"),
            "title": s.get("title"),
            "metadata": s.get("metadata"),
            "created_at": s.get("created_at"),
            "last_message": last_msg,
        })

    return out


__all__ = ["create_session", "append_message", "get_history", "session_belongs_to_user", "get_sessions_for_user"]
