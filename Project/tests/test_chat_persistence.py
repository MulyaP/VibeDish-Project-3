import pytest
from unittest.mock import MagicMock

from app.services import chat_persistence
import app.db as app_db


def test_create_session_inserts_row(monkeypatch):
    # Arrange: fix uuid so we can assert the returned id
    monkeypatch.setattr(chat_persistence, "uuid4", lambda: "fixed-session-id")

    # Ensure the supabase mock is available
    supabase = app_db.supabase

    # Reset call history
    supabase.table.reset_mock()
    supabase.table.return_value.insert.reset_mock()

    # Act
    sid = chat_persistence.create_session(user_id="user-123", title="My Session")

    # Assert
    assert sid == "fixed-session-id"
    supabase.table.assert_called_with("chat_sessions")
    # Inspect the payload inserted
    insert_call_args = supabase.table.return_value.insert.call_args[0][0]
    assert insert_call_args["id"] == "fixed-session-id"
    assert insert_call_args["user_id"] == "user-123"
    assert insert_call_args["title"] == "My Session"


def test_append_message_inserts_row(monkeypatch):
    monkeypatch.setattr(chat_persistence, "uuid4", lambda: "fixed-msg-id")
    supabase = app_db.supabase
    supabase.table.reset_mock()
    supabase.table.return_value.insert.reset_mock()

    mid = chat_persistence.append_message("sess-1", "user", "hello", provider_info={"a": 1}, token_count=7)

    assert mid == "fixed-msg-id"
    supabase.table.assert_called_with("chat_messages")
    payload = supabase.table.return_value.insert.call_args[0][0]
    assert payload["id"] == "fixed-msg-id"
    assert payload["session_id"] == "sess-1"
    assert payload["role"] == "user"
    assert payload["content"] == "hello"
    assert payload["provider_info"] == {"a": 1}
    assert payload["token_count"] == 7


def test_get_history_returns_rows(monkeypatch):
    supabase = app_db.supabase
    # Set the execute return data
    sample = [{"id": "m1", "role": "user", "content": "hi", "created_at": "t", "provider_info": {}, "token_count": 1}]
    supabase.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = MagicMock(data=sample)

    rows = chat_persistence.get_history("sess-1", limit=10)
    assert rows == sample


def test_session_belongs_to_user_cases(monkeypatch):
    supabase = app_db.supabase

    # Case: session row missing -> False
    supabase.table.return_value.select.return_value.limit.return_value.execute.return_value = MagicMock(data=[])
    assert chat_persistence.session_belongs_to_user("x", "u") is False

    # Case: session owned by user
    supabase.table.return_value.select.return_value.limit.return_value.execute.return_value = MagicMock(data=[{"user_id": "u1"}])
    assert chat_persistence.session_belongs_to_user("s1", "u1") is True
    assert chat_persistence.session_belongs_to_user("s1", "other") is False

    # Case: anonymous session (user_id is None)
    supabase.table.return_value.select.return_value.limit.return_value.execute.return_value = MagicMock(data=[{"user_id": None}])
    assert chat_persistence.session_belongs_to_user("anon", None) is True
    assert chat_persistence.session_belongs_to_user("anon", "u1") is False
