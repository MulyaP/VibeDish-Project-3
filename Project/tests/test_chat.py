import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi import HTTPException
from app.routers.chat import send_message, get_history_route, list_sessions, create_session_route, update_session_route, delete_session_route, SendRequest, CreateSessionRequest, UpdateSessionRequest


@pytest.fixture
def mock_user():
    return {"id": "user123"}


@pytest.fixture
def send_request():
    return SendRequest(session_id="session123", message="Hello", context={})


@patch("app.routers.chat.session_belongs_to_user")
@patch("app.routers.chat.append_message")
@patch("app.routers.chat.get_history")
@patch("app.routers.chat.generate_reply_with_groq")
@pytest.mark.asyncio
async def test_send_message_existing_session(mock_groq, mock_history, mock_append, mock_belongs, mock_user, send_request):
    mock_belongs.return_value = True
    mock_history.return_value = [{"role": "user", "content": "Hi"}]
    mock_groq.return_value = {"reply": "Hello!", "provider_info": {"usage": {"completion_tokens": 10}}}
    mock_append.return_value = "msg123"

    result = await send_message(send_request, mock_user)

    assert result.session_id == "session123"
    assert result.reply == "Hello!"


@patch("app.routers.chat.create_session")
@patch("app.routers.chat.append_message")
@patch("app.routers.chat.get_history")
@patch("app.routers.chat.generate_reply_with_groq")
@patch("app.routers.chat.generate_title_with_groq")
@patch("app.routers.chat.update_session_title")
@pytest.mark.asyncio
async def test_send_message_new_session(mock_update_title, mock_gen_title, mock_groq, mock_history, mock_append, mock_create, mock_user):
    mock_create.return_value = "new_session"
    mock_history.return_value = []
    mock_groq.return_value = {"reply": "Hi there!", "provider_info": {}}
    mock_gen_title.return_value = {"title": "New Chat", "provider_info": {}}
    mock_append.return_value = "msg456"

    request = SendRequest(message="Hello")
    result = await send_message(request, mock_user)

    assert result.session_id == "new_session"
    assert result.reply == "Hi there!"


@patch("app.routers.chat.session_belongs_to_user")
@pytest.mark.asyncio
async def test_send_message_unauthorized(mock_belongs, mock_user, send_request):
    mock_belongs.return_value = False

    with pytest.raises(HTTPException) as exc:
        await send_message(send_request, mock_user)
    assert exc.value.status_code == 403


@patch("app.routers.chat.session_belongs_to_user")
@patch("app.routers.chat.append_message")
@patch("app.routers.chat.get_history")
@patch("app.routers.chat.generate_reply_with_groq")
@pytest.mark.asyncio
async def test_send_message_provider_failure(mock_groq, mock_history, mock_append, mock_belongs, mock_user, send_request):
    mock_belongs.return_value = True
    mock_history.return_value = []
    mock_groq.side_effect = Exception("Provider error")

    with pytest.raises(HTTPException) as exc:
        await send_message(send_request, mock_user)
    assert exc.value.status_code == 502


@patch("app.routers.chat.session_belongs_to_user")
@patch("app.services.chat_persistence.get_history")
@pytest.mark.asyncio
async def test_get_history_success(mock_history, mock_belongs, mock_user):
    mock_belongs.return_value = True
    mock_history.return_value = [{"role": "user", "content": "Test"}]

    result = await get_history_route("session123", mock_user)

    assert result["session_id"] == "session123"
    assert len(result["messages"]) == 1


@patch("app.routers.chat.session_belongs_to_user")
@pytest.mark.asyncio
async def test_get_history_unauthorized(mock_belongs, mock_user):
    mock_belongs.return_value = False

    with pytest.raises(HTTPException) as exc:
        await get_history_route("session123", mock_user)
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_get_history_no_session(mock_user):
    result = await get_history_route(None, mock_user)

    assert result["session_id"] is None
    assert result["messages"] == []


@patch("app.routers.chat.get_sessions_for_user")
@pytest.mark.asyncio
async def test_list_sessions(mock_get_sessions, mock_user):
    mock_get_sessions.return_value = [{"id": "s1", "title": "Chat 1"}]

    result = await list_sessions(50, 0, mock_user)

    assert len(result["sessions"]) == 1


@patch("app.routers.chat.create_session")
@pytest.mark.asyncio
async def test_create_session(mock_create, mock_user):
    mock_create.return_value = "new_session_id"

    request = CreateSessionRequest(title="New Chat")
    result = await create_session_route(request, mock_user)

    assert result["session_id"] == "new_session_id"


@patch("app.routers.chat.session_belongs_to_user")
@patch("app.routers.chat.update_session_title")
@pytest.mark.asyncio
async def test_update_session_success(mock_update, mock_belongs, mock_user):
    mock_belongs.return_value = True
    mock_update.return_value = True

    request = UpdateSessionRequest(title="Updated Title")
    result = await update_session_route("session123", request, mock_user)

    assert result["session_id"] == "session123"
    assert result["title"] == "Updated Title"


@patch("app.routers.chat.session_belongs_to_user")
@pytest.mark.asyncio
async def test_update_session_unauthorized(mock_belongs, mock_user):
    mock_belongs.return_value = False

    request = UpdateSessionRequest(title="Updated")
    with pytest.raises(HTTPException) as exc:
        await update_session_route("session123", request, mock_user)
    assert exc.value.status_code == 403


@patch("app.routers.chat.session_belongs_to_user")
@patch("app.routers.chat.delete_session")
@pytest.mark.asyncio
async def test_delete_session_success(mock_delete, mock_belongs, mock_user):
    mock_belongs.return_value = True
    mock_delete.return_value = True

    result = await delete_session_route("session123", mock_user)

    assert result["deleted"] is True


@patch("app.routers.chat.session_belongs_to_user")
@pytest.mark.asyncio
async def test_delete_session_unauthorized(mock_belongs, mock_user):
    mock_belongs.return_value = False

    with pytest.raises(HTTPException) as exc:
        await delete_session_route("session123", mock_user)
    assert exc.value.status_code == 403
