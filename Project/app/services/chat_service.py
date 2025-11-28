import os
import re
import json
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


def _sanitize_text(text: Optional[str]) -> Optional[str]:
    """Sanitize provider text for presentation.

    This mirrors the sanitization used for descriptions/replies but is
    available at module scope so titles can be cleaned the same way.
    """
    if not text:
        return text
    try:
        # If provider returned a python object repr like ChatCompletionMessage(...),
        # try to extract the inner content field.
        m = re.search(r"ChatCompletionMessage\(content=(?P<q>[\'\"])(?P<c>.*?)(?P=q),", text, re.DOTALL)
        if m:
            text = m.group("c")
    except Exception:
        pass

    # Unescape literal escaped newlines/tabs (e.g. "\\n") into real newlines
    text = text.replace("\\n", "\n").replace("\\t", "\t")

    # Remove common markdown formatting we don't want to show (bold, headings, code ticks)
    try:
        # **bold** -> bold
        text = re.sub(r"\*\*(.*?)\*\*", r"\1", text, flags=re.DOTALL)
        # # or ## headings -> remove leading #'s
        text = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)
        # Remove backticks
        text = text.replace("`", "")
        # Remove list bullets at start of lines like '- ' or '* '
        text = re.sub(r"^[\-\*]\s*", "", text, flags=re.MULTILINE)
        # Convert '- **Label:** value' to 'Label: value' (remove markdown bold and dash)
        text = re.sub(r"^[\-\*]\s*\*\*(.*?)\*\*:\s*", r"\1: ", text, flags=re.MULTILINE)
        # Remove remaining inline markdown bold markers if any
        text = text.replace("**", "")
        # Collapse large gaps
        text = re.sub(r"\n{3,}", "\n\n", text)
    except Exception:
        text = text.replace("**", "").replace("`", "").replace("\\n", "\n")

    # Trim whitespace and any surrounding quotes
    text = text.strip()
    if (text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'")):
        text = text[1:-1].strip()

    return text


def _extract_text_from_completion(completion: Any) -> Optional[str]:
    """Try many common shapes to extract a textual output from SDK completion objects.

    The Groq SDK may return nested objects/dicts where the assistant text lives in
    choices[0].message.content, choices[0].text, or even as a list of content
    blocks. This helper attempts several heuristics and returns the first string
    it can reasonably find.
    """
    try:
        # Normalize choices
        choices = getattr(completion, "choices", None)
        if choices is None and isinstance(completion, dict):
            choices = completion.get("choices")
        if not choices:
            return None

        first = choices[0]

        # Candidate message containers
        candidates = []

        # If dict-like
        if isinstance(first, dict):
            candidates.append(first.get("message"))
            candidates.append(first.get("text"))
            candidates.append(first.get("content"))
        else:
            # object-like
            candidates.append(getattr(first, "message", None))
            candidates.append(getattr(first, "text", None))
            candidates.append(getattr(first, "content", None))

        # Helper to drill into candidate and return a string when found
        def _drill(obj: Any) -> Optional[str]:
            if obj is None:
                return None
            if isinstance(obj, str):
                return obj
            if isinstance(obj, dict):
                # common keys in nested dicts
                for k in ("content", "text", "body", "message"):
                    if k in obj and obj[k]:
                        v = obj[k]
                        if isinstance(v, str):
                            return v
                        if isinstance(v, list):
                            # prefer first string element or nested dict
                            for item in v:
                                if isinstance(item, str):
                                    return item
                                if isinstance(item, dict):
                                    for kk in ("text", "content", "body"):
                                        if kk in item and isinstance(item[kk], str):
                                            return item[kk]
                # if nothing found, try to stringify shallow dict values
                for v in obj.values():
                    if isinstance(v, str):
                        return v
                return None
            # If it's a list, search for first string or dict with string
            if isinstance(obj, list):
                for item in obj:
                    s = _drill(item)
                    if s:
                        return s
                return None
            # Fallback: try vars() then str()
            try:
                d = vars(obj)
                if isinstance(d, dict):
                    return _drill(d)
            except Exception:
                pass
            try:
                return str(obj)
            except Exception:
                return None

        for c in candidates:
            s = _drill(c)
            if s:
                return s

        # Last-resort: stringify the whole completion
        try:
            return str(completion)
        except Exception:
            return None
    except Exception:
        return None


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

    # Build messages payload. Always include a conversational system prompt so
    # the assistant replies like a natural, helpful conversational agent.
    # If the caller sets `context['meal_suggestions'] = True`, prepend an
    # additional instruction that constrains output to meal-name suggestions
    # formatted as single-line items with a short description.
    convo_system_msg = {
        "role": "system",
        "content": (
            "You are a friendly, helpful conversational assistant. Reply in a natural,")
        + (
            " engaging tone appropriate for a chat. Keep replies concise when possible,"
        )
        + (
            " and follow any format instructions provided by the user or a secondary system message."
        ),
    }

    messages = [convo_system_msg]

    # Optional: specialized format instruction for meal suggestions
    if isinstance(context, dict) and context.get("meal_suggestions"):
        # Strong system instruction for the food-delivery chatbot context.
        meal_system_msg = {
            "role": "system",
            "content": (
                "You are the back-end assistant for a food delivery app chatbot. When the user asks for meal suggestions,"
                " ONLY return up to 5 meal suggestions formatted exactly as lines with this pipe-separated pattern:\n\n"
                "Dish| Short description\n\n"
                "Do NOT include any headers, table columns, bullets, numbering, markdown, surrounding quotes, explanatory text,"
                " extra columns, prep tips, ingredients, or any other fields. For example, do NOT output a header row like"
                " 'Cuisine | Dish | Why It\'s Spicy & Delicious | Quick Prep Idea'. Keep each description to one short sentence (<= ~20 words)."
                " If the user requests an exact number, return exactly that many (max 5). Otherwise return between 1 and 5 suggestions (prefer 3-5)."
            ),
        }
        messages.append(meal_system_msg)

    # Append conversation history (roles should be 'user'/'assistant') then the new user message
    messages = messages + (session_messages or []) + [{"role": "user", "content": user_message}]

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

    # Sanitize the reply_text to make it presentation-ready for the UI.
    reply_text = _sanitize_text(reply_text)
    # If this request asked specifically for meal suggestions, try to parse
    # the reply into a structured list of {'name': ..., 'description': ...}.
    structured_suggestions = None
    try:
        if isinstance(context, dict) and context.get("meal_suggestions"):
            # Helper: attempt to parse JSON first (model instructed to reply JSON)
            def _parse_suggestions(text: str):
                # Trim surrounding whitespace and any leading/trailing punctuation
                t = text.strip()
                # Try JSON parse
                try:
                    parsed = json.loads(t)
                    if isinstance(parsed, list):
                        out = []
                        for item in parsed:
                            if isinstance(item, dict):
                                # Only keep name and short description — ignore extra fields like cuisine/ingredients
                                name = item.get("name") or item.get("title") or item.get("meal")
                                desc = item.get("description") or item.get("desc") or item.get("short_description")
                                if name:
                                    out.append({
                                        "name": str(name).strip(),
                                        "description": (str(desc).strip() if desc else ""),
                                    })
                        return out if out else None
                except Exception:
                    pass

                # Fallback: parse line-based suggestions. Prefer the exact pipe format
                # 'Dish| Short description| Cuisine(optional)' per product requirement, then other separators.
                lines = [l.rstrip() for l in t.splitlines() if l.strip()]
                # If the first line looks like a header row (contains header words and pipes), drop it.
                if lines:
                    first_low = lines[0].lower()
                    header_indicators = ("cuisine", "dish", "dish name", "meal", "why", "prep", "quick", "description", "why it")
                    if ("|" in lines[0] and any(k in first_low for k in header_indicators)) or re.match(r"^\|?\s*-{3,}\s*\|?", lines[0]):
                        lines = lines[1:]

                out = []
                for ln in lines:
                    # Remove list numbering like '1.' or headings '##'
                    ln = re.sub(r"^\d+\.\s*", "", ln)
                    ln = re.sub(r"^#{1,6}\s*", "", ln)
                    # Remove leading bullets
                    ln = re.sub(r"^[\-\*]\s*", "", ln)

                    # 1) Pipe-separated format: 'Dish| Description| Cuisine(optional)' (preferred)
                    if "|" in ln:
                        # skip pure separator lines like '| --- | --- |'
                        if re.match(r"^[\s\|:-]+$", ln):
                            continue
                        parts = [p.strip() for p in ln.split("|")]
                        # Strictly map to name and short description only; ignore any extra columns
                        name = parts[0] if len(parts) > 0 else ""
                        desc = parts[1] if len(parts) > 1 else ""
                        out.append({"name": name, "description": desc})
                        continue

                    # 2) Try separators — em-dash, en-dash, hyphen, colon
                    m = re.split(r"\s[\u2014\u2013\-:]\s|\s-\s|\s—\s", ln, maxsplit=1)
                    if len(m) == 2:
                        name, desc = m[0].strip(), m[1].strip()
                        out.append({"name": name, "description": desc})
                    else:
                        # If no separator, treat entire line as name with empty description
                        out.append({"name": ln, "description": ""})
                return out if out else None

            parsed = _parse_suggestions(reply_text or "")
            if parsed:
                # honor optional num_suggestions hint; otherwise cap to at most 5 suggestions
                num = None
                try:
                    num = int(context.get("num_suggestions")) if context.get("num_suggestions") else None
                except Exception:
                    num = None
                if num:
                    parsed = parsed[:num]
                else:
                    parsed = parsed[:5]
                structured_suggestions = parsed
                # If we have structured suggestions, rebuild a clean reply_text for UI
                # Format reply lines exactly as 'Dish| Short description'
                pretty_lines = []
                for s in parsed:
                    # ensure description is one short sentence and truncate to ~20 words
                    desc = s.get('description', '') or ''
                    # keep only first sentence if multiple
                    if '.' in desc:
                        desc = desc.split('.', 1)[0].strip()
                    # truncate to ~20 words
                    words = desc.split()
                    if len(words) > 20:
                        desc = ' '.join(words[:20]).rstrip() + '...'
                    line = f"{s.get('name','')}| {desc}".rstrip()
                    pretty_lines.append(line.rstrip("| "))
                reply_text = "\n".join(pretty_lines)
                # Also reduce structured_suggestions objects to only 'name' and 'description'
                structured_suggestions = [{"name": s.get('name',''), "description": (s.get('description','') or '').split('.',1)[0].split()[:20] and ' '.join((s.get('description','') or '').split('.',1)[0].split()[:20]) or ''} for s in parsed]
    except Exception:
        # parsing failed — leave reply_text sanitized and suggestions as None
        structured_suggestions = None

    result = {"reply": reply_text, "provider_info": provider_info}
    if structured_suggestions is not None:
        result["suggestions"] = structured_suggestions

    return result


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
            f"title no longer than {max_words} words and {max_chars} characters. Reply with the title only, "
            "without surrounding quotes or additional commentary."
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

    # Robustly extract the textual title from the SDK response using helper
    title = _extract_text_from_completion(completion)

    # Final sanitization and truncation rules
    if title:
        # normalize and sanitize provider text
        title = _sanitize_text(str(title))

        # If the model returned a JSON blob like {"title": "..."} or ["..."], try to extract
        try:
            parsed = json.loads(title)
            if isinstance(parsed, dict):
                # common field names
                title_candidate = parsed.get("title") or parsed.get("name") or parsed.get("text")
                if title_candidate:
                    title = _sanitize_text(str(title_candidate))
            elif isinstance(parsed, list) and parsed:
                # If it's a list, prefer the first string element
                if isinstance(parsed[0], str):
                    title = _sanitize_text(parsed[0])
        except Exception:
            # not JSON — continue
            pass

        # Remove common label prefixes like 'Title:' or 'title -'
        title = re.sub(r"^(Title|title)\s*[:\-–—]\s*", "", title).strip()

        # keep only first line
        if "\n" in title:
            title = title.split("\n")[0].strip()
        # truncate by words
        words = title.split()
        if len(words) > max_words:
            title = " ".join(words[:max_words]).strip()
        # truncate by characters
        if len(title) > max_chars:
            title = title[: max_chars - 1].rstrip() + "…"

    # If provider returned nothing useful, fall back to heuristic
    if not title:
        title = _fallback_title_from_messages(session_messages)

    return {"title": title, "provider_info": provider_info}


__all__ = ["generate_reply_with_groq", "generate_title_with_groq"]
