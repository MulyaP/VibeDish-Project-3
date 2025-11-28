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


async def generate_title_with_groq(
    session_messages: List[Dict[str, Any]], max_words: int = 6, max_chars: int = 60
) -> Dict[str, Any]:
    """Generate a short title for a conversation using the Groq model.

    Returns a dict {"title": Optional[str], "provider_info": Optional[dict]}.
    The title will be truncated to at most `max_words` words and `max_chars` characters.
    """
    def _fallback_title_from_messages(msgs: List[Dict[str, Any]]) -> Optional[str]:
        # Prefer the last user message content, otherwise earliest message.
        text = None
        for m in reversed(msgs or []):
            if m.get("role") == "user" and m.get("content"):
                text = m.get("content")
                break
        if not text:
            # fallback to any content
            for m in reversed(msgs or []):
                if m.get("content"):
                    text = m.get("content")
                    break
        if not text:
            return None
        # Use first sentence if present
        if "." in text:
            first = text.split(".", 1)[0]
        else:
            first = text
        # Trim by words then chars
        words = first.split()
        title = " ".join(words[:max_words]).strip()
        if len(title) > max_chars:
            title = title[: max_chars - 1].rstrip() + "…"
        return title or None

    if not GROQ_API_KEY:
        # No provider configured — return a heuristic title rather than raising.
        return {"title": _fallback_title_from_messages(session_messages), "provider_info": None}

    # Build a compact system + user prompt instructing the model to return only a short title
    system_msg = {
        "role": "system",
        "content": (
            "You are a concise title generator. Given the conversation, produce a short, descriptive "
            f"title no longer than {max_words} words and {max_chars} characters. Reply with a JSON object "
            "ONLY, with exactly two keys: \"title\" (the short heading) and \"content\" (a short summary). "
            "Example: {\"title\": \"Charred Brussels Sprouts\", \"content\": \"Roasted with garlic and balsamic\"}. "
            "Do not wrap the JSON in markdown or backticks and do not include any extra text."
        ),
    }

    # Combine recent messages into a single user message for brevity
    convo_text_parts = []
    for m in (session_messages or []):
        role = m.get("role")
        content = m.get("content")
        if role and content:
            # Keep messages short when building prompt
            convo_text_parts.append(f"{role}: {content}")
    user_msg = {"role": "user", "content": "\n".join(convo_text_parts) or ""}

    try:
        completion = await run_in_threadpool(_call_groq_sync, [system_msg, user_msg], GROQ_MODEL, None)
    except Exception as exc:
        # provider failed — fall back to heuristic title but include no provider_info
        return {"title": _fallback_title_from_messages(session_messages), "provider_info": None}

    provider_info = _serialize(completion)

    # Robustly extract the JSON payload (title + content) from the SDK response.
    title = None
    content = None
    try:
        choices = getattr(completion, "choices", None)
        raw_text = None
        if choices and len(choices) > 0:
            first = choices[0]
            # Try common accessors
            if hasattr(first, "message"):
                msg = getattr(first, "message")
                if isinstance(msg, dict):
                    raw_text = msg.get("content") or msg.get("text")
                elif isinstance(msg, str):
                    raw_text = msg
            elif hasattr(first, "text"):
                txt = getattr(first, "text")
                raw_text = txt if isinstance(txt, str) else None
            elif isinstance(first, str):
                raw_text = first

        # If we have a raw_text string, try to parse JSON from it
        if raw_text:
            raw_text = str(raw_text).strip()
            # Extract a JSON object substring if extra text is present
            import re, json

            json_obj = None
            try:
                # direct parse if the whole string is JSON
                json_obj = json.loads(raw_text)
            except Exception:
                # try to find a {...} substring
                m = re.search(r"\{[^\}]*\}", raw_text)
                if m:
                    candidate = m.group(0)
                    try:
                        json_obj = json.loads(candidate)
                    except Exception:
                        json_obj = None

            if isinstance(json_obj, dict):
                title = json_obj.get("title")
                content = json_obj.get("content")
            else:
                # If not JSON, treat the whole text as a title string
                title = raw_text
    except Exception:
        title = None

    # Final sanitization and truncation rules for title
    if title:
        title = str(title).strip()
        if "\n" in title:
            title = title.split("\n")[0].strip()
        words = title.split()
        if len(words) > max_words:
            title = " ".join(words[:max_words]).strip()
        if len(title) > max_chars:
            title = title[: max_chars - 1].rstrip() + "…"

    # If provider returned nothing useful, fall back to heuristic
    if not title:
        title = _fallback_title_from_messages(session_messages)

    return {"title": title, "content": content, "provider_info": provider_info}


__all__ = ["generate_reply_with_groq"]
