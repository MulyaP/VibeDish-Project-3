import os
from typing import Any, Dict, List, Optional

from fastapi.concurrency import run_in_threadpool

try:
    from groq import Groq
except Exception as exc:  # pragma: no cover - runtime import
    Groq = None  # type: ignore


GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "grok-latest")


def _serialize(obj: Any) -> Any:
    """Serialize SDK objects into primitives for JSON responses.

    Converts dicts/lists recursively, and falls back to str() for unknown types.
    """
    if obj is None:
        return None
    if isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, dict):
        return {k: _serialize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_serialize(v) for v in obj]
    # fallback: try __dict__ then str
    try:
        return _serialize(vars(obj))
    except Exception:
        return str(obj)


def _call_groq_sync(messages: List[Dict[str, Any]], model: str, tools: Optional[List[Dict]] = None):
    if Groq is None:
        raise RuntimeError("groq SDK is not installed; please install the 'groq' package")
    client = Groq(api_key=GROQ_API_KEY)

    # The SDK method used in examples: client.chat.completions.create(...)
    completion = client.chat.completions.create(model=model, messages=messages, tools=tools or None)
    return completion


async def generate_reply_with_groq(
    session_messages: List[Dict[str, Any]],
    user_message: str,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Generate a reply using the Groq SDK in a threadpool to avoid blocking.

    Returns a dict {reply: str, provider_info: dict} where provider_info is
    a JSON-serializable representation of the SDK response.
    """
    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY must be set in the environment")

    # Build messages payload (append user message to session history)
    messages = (session_messages or []) + [{"role": "user", "content": user_message}]

    # Tools may be added here if you use MCP; keep None for now
    tools = None

    try:
        completion = await run_in_threadpool(_call_groq_sync, messages, GROQ_MODEL, tools)
    except Exception as exc:
        raise RuntimeError(f"GROQ SDK error: {exc}") from exc

    # Try to extract a text reply from the SDK response
    reply_text = None
    try:
        # common shapes: completion.choices[0].message or .choices[0].text
        choices = getattr(completion, "choices", None)
        if choices:
            first = choices[0]
            # message can be object or dict
            msg = getattr(first, "message", None) or getattr(first, "text", None)
            if isinstance(msg, dict):
                # e.g. {"content": "..."}
                reply_text = msg.get("content") or msg.get("text")
            elif hasattr(msg, "get"):
                reply_text = msg.get("content") or msg.get("text")
            else:
                reply_text = str(msg)
    except Exception:
        reply_text = None

    if not reply_text:
        # last-resort: stringify the whole completion
        reply_text = str(completion)

    provider_info = _serialize(completion)

    return {"reply": reply_text, "provider_info": provider_info}


__all__ = ["generate_reply_with_groq"]
