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


def session_belongs_to_user(session_id: str, user_id: str) -> bool:
    """Return True if the session with `session_id` belongs to `user_id`.

    Uses Supabase to check ownership. Returns False if session not found or not owned.
    """
    supabase = get_db()
    r = supabase.table("chat_sessions").select("id").eq("id", session_id).eq("user_id", user_id).limit(1).execute()
    data = r.data or []
    return len(data) > 0


__all__ = ["create_session", "append_message", "get_history"]
