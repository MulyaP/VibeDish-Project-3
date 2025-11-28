import json
import pytest
from fastapi.testclient import TestClient

import app.main as main_app
import app.routers.chat as chat_router_module


@pytest.fixture(autouse=True)
def override_current_user():
    # Default override returns a test user dict
    main_app.app.dependency_overrides[chat_router_module.current_user] = lambda: {"id": "test-user", "email": "x@test"}
    yield
    main_app.app.dependency_overrides.clear()


def test_send_message_creates_session_and_returns_reply(monkeypatch):
    client = TestClient(main_app.app)

    # Patch persistence and provider functions on the router module (they are imported there)
    monkeypatch.setattr(chat_router_module, "create_session", lambda user_id=None: "sess-123")
    monkeypatch.setattr(chat_router_module, "append_message", lambda session_id, role, content, provider_info=None, token_count=None: "msg-{}-{}".format(role, "1"))
    monkeypatch.setattr(chat_router_module, "get_history", lambda session_id, limit=200: [])
    monkeypatch.setattr(chat_router_module, "session_belongs_to_user", lambda s, u: True)

    async def fake_generate(history, message, context):
        return {
            "reply": "Hello from bot",
            "provider_info": {"usage": {"completion_tokens": 2, "prompt_tokens": 1, "total_tokens": 3}, "model": "grok-test"},
        }

    monkeypatch.setattr(chat_router_module, "generate_reply_with_groq", fake_generate)

    resp = client.post("/chat/messages", json={"session_id": None, "message": "Hi there"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["session_id"] == "sess-123"
    assert data["reply"] == "Hello from bot"
    assert "provider_info" in data


def test_send_message_session_mismatch_returns_403(monkeypatch):
    client = TestClient(main_app.app)

    # If session_belongs_to_user returns False, router should reject
    monkeypatch.setattr(chat_router_module, "session_belongs_to_user", lambda s, u: False)

    resp = client.post("/chat/messages", json={"session_id": "some-session", "message": "Hi"})
    assert resp.status_code == 403


def test_get_history_returns_messages(monkeypatch):
    client = TestClient(main_app.app)

    sample = [{"id": "m1", "role": "user", "content": "hi"}, {"id": "m2", "role": "assistant", "content": "hello"}]
    monkeypatch.setattr(chat_router_module, "session_belongs_to_user", lambda s, u: True)
    # The router imports get_history inside the handler, so patch the persistence module
    monkeypatch.setattr("app.services.chat_persistence.get_history", lambda session_id: sample)

    resp = client.get("/chat/history", params={"session_id": "sess-1"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["session_id"] == "sess-1"
    assert data["messages"] == sample


def test_list_sessions_returns_user_sessions(monkeypatch):
    client = TestClient(main_app.app)

    sample_sessions = [
        {"id": "s1", "user_id": "test-user", "title": "First", "metadata": {}, "created_at": "t1", "last_message": {"id": "m1", "content": "hello"}},
        {"id": "s2", "user_id": "test-user", "title": "Second", "metadata": {}, "created_at": "t2", "last_message": None},
    ]

    # Router imports get_sessions_for_user at module import time, patch the router's reference
    monkeypatch.setattr(chat_router_module, "get_sessions_for_user", lambda user_id, limit=50, offset=0: sample_sessions)

    resp = client.get("/chat/sessions")
    assert resp.status_code == 200
    data = resp.json()
    assert "sessions" in data
    assert data["sessions"] == sample_sessions
