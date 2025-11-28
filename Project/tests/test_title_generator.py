import json
import re
import os

import pytest

from app.services import chat_service


class FakeChoice:
    def __init__(self, message=None, text=None):
        # message can be dict or object; keep simple
        self.message = message
        self.text = text


class FakeCompletion:
    def __init__(self, choices):
        self.choices = choices


def run_async(coro):
    import asyncio

    return asyncio.get_event_loop().run_until_complete(coro)


def test_parse_json_content(monkeypatch):
    # Ensure env var present so code uses provider path
    monkeypatch.setenv("GROQ_API_KEY", "dummy-key")
    # module-level constant may have been read at import time; ensure it's set on the module
    chat_service.GROQ_API_KEY = "dummy-key"

    # Simulate a provider returning a JSON string in message.content
    fake_comp = FakeCompletion([FakeChoice(message={"content": json.dumps({"title": "Charred Brussels", "content": "roast with balsamic"})})])

    # Make run_in_threadpool an async function that returns our fake completion
    async def _fake_run_in_threadpool(fn, *a, **k):
        return fake_comp

    monkeypatch.setattr(chat_service, "run_in_threadpool", _fake_run_in_threadpool)

    res = run_async(chat_service.generate_title_with_groq([{"role": "user", "content": "Roast brussels..."}]))
    assert isinstance(res, dict)
    assert res.get("title") == "Charred Brussels"
    assert isinstance(res.get("provider_info"), dict)


def test_parse_plain_text(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "dummy-key")
    chat_service.GROQ_API_KEY = "dummy-key"

    fake_comp = FakeCompletion([FakeChoice(message={"content": "Charred Balsamic Garlic Brussels Sprouts"})])
    async def _fake_run_in_threadpool(fn, *a, **k):
        return fake_comp

    monkeypatch.setattr(chat_service, "run_in_threadpool", _fake_run_in_threadpool)

    res = run_async(chat_service.generate_title_with_groq([{"role": "user", "content": "Roast brussels"}]))
    assert res.get("title") == "Charred Balsamic Garlic Brussels Sprouts"


def test_fallback_when_provider_missing(monkeypatch):
    # Remove API key to force fallback
    monkeypatch.delenv("GROQ_API_KEY", raising=False)

    msgs = [
        {"role": "user", "content": "I like to roast brussels with lots of garlic and balsamic; prefer some char."},
    ]
    res = run_async(chat_service.generate_title_with_groq(msgs))
    # Fallback should produce a non-empty title derived from the user message
    assert isinstance(res, dict)
    assert res.get("title") is not None
    assert len(res.get("title")) > 0
