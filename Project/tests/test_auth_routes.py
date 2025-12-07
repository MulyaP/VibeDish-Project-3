import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi import HTTPException
from app.routers.auth_routes import signup, owner_signup, login, refresh_token, logout, delete_me, ensure_app_user, _extract_bearer_token, SignupRequest, OwnerSignupRequest, LoginRequest, RefreshRequest


@pytest.fixture
def mock_user():
    return {"id": "user123", "email": "test@example.com"}


@patch("app.routers.auth_routes.get_db")
def test_ensure_app_user_existing(mock_get_db):
    mock_supabase = Mock()
    mock_get_db.return_value = mock_supabase
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [{"id": "user123"}]

    ensure_app_user(user_id="user123", email="test@example.com", name="Test")

    mock_supabase.table.return_value.update.assert_called()


@patch("app.routers.auth_routes.get_db")
def test_ensure_app_user_new(mock_get_db):
    mock_supabase = Mock()
    mock_get_db.return_value = mock_supabase
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []

    ensure_app_user(user_id="user123", email="test@example.com", name="Test")

    mock_supabase.table.return_value.insert.assert_called()


def test_extract_bearer_token_valid():
    token = _extract_bearer_token("Bearer abc123")
    assert token == "abc123"


def test_extract_bearer_token_missing():
    with pytest.raises(HTTPException) as exc:
        _extract_bearer_token(None)
    assert exc.value.status_code == 401


def test_extract_bearer_token_invalid():
    with pytest.raises(HTTPException) as exc:
        _extract_bearer_token("Invalid token")
    assert exc.value.status_code == 401


@patch("app.routers.auth_routes.httpx.AsyncClient")
@patch("app.routers.auth_routes.get_db")
@pytest.mark.asyncio
async def test_signup_success(mock_get_db, mock_client):
    mock_supabase = Mock()
    mock_get_db.return_value = mock_supabase
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
    
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"id": "user123", "email": "test@example.com"}
    
    mock_client_instance = AsyncMock()
    mock_client_instance.post.return_value = mock_response
    mock_client.return_value.__aenter__.return_value = mock_client_instance

    request = SignupRequest(email="test@example.com", password="pass123", name="Test", role="customer")
    result = await signup(request)

    assert result["id"] == "user123"
    assert result["email"] == "test@example.com"


@patch("app.routers.auth_routes.httpx.AsyncClient")
@pytest.mark.asyncio
async def test_signup_failure(mock_client):
    mock_response = Mock()
    mock_response.status_code = 400
    mock_response.json.return_value = {"message": "Email already exists"}
    
    mock_client_instance = AsyncMock()
    mock_client_instance.post.return_value = mock_response
    mock_client.return_value.__aenter__.return_value = mock_client_instance

    request = SignupRequest(email="test@example.com", password="pass123", name="Test", role="customer")
    with pytest.raises(HTTPException) as exc:
        await signup(request)
    assert exc.value.status_code == 400


@patch("app.routers.auth_routes.httpx.AsyncClient")
@patch("app.routers.auth_routes.get_db")
@pytest.mark.asyncio
async def test_owner_signup_success(mock_get_db, mock_client):
    mock_supabase = Mock()
    mock_get_db.return_value = mock_supabase
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
    mock_supabase.table.return_value.insert.return_value.execute.return_value.data = [{"id": "rest123"}]
    
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"id": "owner123", "email": "owner@example.com"}
    
    mock_client_instance = AsyncMock()
    mock_client_instance.post.return_value = mock_response
    mock_client.return_value.__aenter__.return_value = mock_client_instance

    request = OwnerSignupRequest(
        email="owner@example.com",
        password="pass123",
        name="Owner",
        restaurant_name="Test Restaurant",
        restaurant_address="123 Main St",
        latitude=40.7128,
        longitude=-74.0060
    )
    result = await owner_signup(request)

    assert result["id"] == "owner123"
    assert result["restaurant_id"] == "rest123"


@patch("app.routers.auth_routes.httpx.AsyncClient")
@patch("app.routers.auth_routes.ensure_app_user")
@pytest.mark.asyncio
async def test_login_success(mock_ensure, mock_client):
    mock_token_response = Mock()
    mock_token_response.status_code = 200
    mock_token_response.json.return_value = {"access_token": "token123", "refresh_token": "refresh123"}
    
    mock_user_response = Mock()
    mock_user_response.status_code = 200
    mock_user_response.json.return_value = {"id": "user123", "email": "test@example.com", "user_metadata": {"name": "Test"}}
    
    mock_client_instance = AsyncMock()
    mock_client_instance.post.return_value = mock_token_response
    mock_client_instance.get.return_value = mock_user_response
    mock_client.return_value.__aenter__.return_value = mock_client_instance

    request = LoginRequest(email="test@example.com", password="pass123")
    result = await login(request)

    assert result["access_token"] == "token123"
    assert result["user"]["id"] == "user123"


@patch("app.routers.auth_routes.httpx.AsyncClient")
@pytest.mark.asyncio
async def test_login_invalid_credentials(mock_client):
    mock_response = Mock()
    mock_response.status_code = 400
    
    mock_client_instance = AsyncMock()
    mock_client_instance.post.return_value = mock_response
    mock_client.return_value.__aenter__.return_value = mock_client_instance

    request = LoginRequest(email="test@example.com", password="wrong")
    with pytest.raises(HTTPException) as exc:
        await login(request)
    assert exc.value.status_code == 400


@patch("app.routers.auth_routes.httpx.AsyncClient")
@pytest.mark.asyncio
async def test_refresh_token_success(mock_client):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"access_token": "new_token"}
    
    mock_client_instance = AsyncMock()
    mock_client_instance.post.return_value = mock_response
    mock_client.return_value.__aenter__.return_value = mock_client_instance

    request = RefreshRequest(refresh_token="refresh123")
    result = await refresh_token(request)

    assert result["access_token"] == "new_token"


@patch("app.routers.auth_routes.httpx.AsyncClient")
@pytest.mark.asyncio
async def test_refresh_token_failure(mock_client):
    mock_response = Mock()
    mock_response.status_code = 401
    mock_response.json.return_value = {"message": "Invalid refresh token"}
    
    mock_client_instance = AsyncMock()
    mock_client_instance.post.return_value = mock_response
    mock_client.return_value.__aenter__.return_value = mock_client_instance

    request = RefreshRequest(refresh_token="invalid")
    with pytest.raises(HTTPException) as exc:
        await refresh_token(request)
    assert exc.value.status_code == 401


@patch("app.routers.auth_routes.httpx.AsyncClient")
@pytest.mark.asyncio
async def test_logout_success(mock_client):
    mock_response = Mock()
    mock_response.status_code = 200
    
    mock_client_instance = AsyncMock()
    mock_client_instance.post.return_value = mock_response
    mock_client.return_value.__aenter__.return_value = mock_client_instance

    result = await logout("Bearer token123")

    assert result["ok"] is True


@patch("app.routers.auth_routes.httpx.AsyncClient")
@patch("app.routers.auth_routes.get_db")
@patch("app.routers.auth_routes.settings")
@pytest.mark.asyncio
async def test_delete_me_success(mock_settings, mock_get_db, mock_client, mock_user):
    mock_settings.SUPABASE_SERVICE_ROLE_KEY = "service_key"
    mock_supabase = Mock()
    mock_get_db.return_value = mock_supabase
    
    mock_response = Mock()
    mock_response.status_code = 200
    
    mock_client_instance = AsyncMock()
    mock_client_instance.delete.return_value = mock_response
    mock_client.return_value.__aenter__.return_value = mock_client_instance

    result = await delete_me(mock_user)

    assert result["deleted_in_app_db"] is True
    assert result["deleted_in_supabase"] is True


@patch("app.routers.auth_routes.get_db")
@patch("app.routers.auth_routes.settings")
@pytest.mark.asyncio
async def test_delete_me_no_service_key(mock_settings, mock_get_db, mock_user):
    mock_settings.SUPABASE_SERVICE_ROLE_KEY = None
    mock_supabase = Mock()
    mock_get_db.return_value = mock_supabase

    result = await delete_me(mock_user)

    assert result["deleted_in_app_db"] is True
    assert result["deleted_in_supabase"] is False
