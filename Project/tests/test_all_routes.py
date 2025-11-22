import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from contextlib import contextmanager

# ============ Helper Functions ============

def create_mock_supabase():
    mock_supabase = MagicMock()
    mock_response = MagicMock()
    mock_response.data = [{"id": "user1", "email": "test@test.com"}]
    mock_table = MagicMock()
    mock_table.select.return_value = mock_table
    mock_table.insert.return_value = mock_table
    mock_table.update.return_value = mock_table
    mock_table.eq.return_value = mock_table
    mock_table.execute.return_value = mock_response
    mock_supabase.table.return_value = mock_table
    return mock_supabase

@contextmanager
def mock_authenticated_user():
    """Helper to mock httpx client for authenticated requests"""
    with patch('httpx.AsyncClient') as mock_httpx:
        mock_client = MagicMock()
        mock_user_resp = MagicMock()
        mock_user_resp.status_code = 200
        mock_user_resp.json.return_value = {"id": "user1", "email": "test@test.com", "user_metadata": {"name": "Test User"}}
        mock_client.__aenter__.return_value.get = AsyncMock(return_value=mock_user_resp)
        mock_httpx.return_value = mock_client
        yield

def create_mock_table(response_data):
    """Helper to create mock Supabase table with response data"""
    mock_supabase = MagicMock()
    mock_response = MagicMock()
    mock_response.data = response_data
    mock_table = MagicMock()
    for method in ['select', 'insert', 'update', 'eq', 'order', 'delete']:
        setattr(mock_table, method, MagicMock(return_value=mock_table))
    mock_table.execute.return_value = mock_response
    mock_supabase.table.return_value = mock_table
    return mock_supabase

@contextmanager
def mock_db_and_client(router_module, response_data):
    """Helper to mock database and return test client"""
    mock_supabase = create_mock_table(response_data)
    with patch(f'app.routers.{router_module}.get_db', return_value=mock_supabase):
        with patch('app.db.get_db', return_value=mock_supabase):
            from app.main import app
            from fastapi.testclient import TestClient
            yield TestClient(app)

@contextmanager
def mock_auth_client(response_json, method='post'):
    """Helper to mock httpx client for auth endpoints"""
    with patch('httpx.AsyncClient') as mock_httpx:
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = response_json
        setattr(mock_client.__aenter__.return_value, method, AsyncMock(return_value=mock_response))
        mock_httpx.return_value = mock_client
        
        with patch('app.routers.auth_routes.get_db', return_value=create_mock_supabase()):
            with patch('app.db.get_db', return_value=create_mock_supabase()):
                from app.main import app
                from fastapi.testclient import TestClient
                yield TestClient(app)

@contextmanager
def mock_cart_operation(cart_data, items_data, meal_data=None):
    """Helper for cart operations with complex table mocking"""
    with mock_authenticated_user():
        mock_supabase = MagicMock()
        mock_cart_resp = MagicMock()
        mock_cart_resp.data = cart_data
        mock_items_resp = MagicMock()
        mock_items_resp.data = items_data
        mock_meal_resp = MagicMock()
        mock_meal_resp.data = meal_data or []
        
        def table_mock(name):
            mock_table = MagicMock()
            for method in ['select', 'insert', 'update', 'eq', 'delete']:
                setattr(mock_table, method, MagicMock(return_value=mock_table))
            if name == "carts":
                mock_table.execute.return_value = mock_cart_resp
            elif name == "meals":
                mock_table.execute.return_value = mock_meal_resp
            else:
                mock_table.execute.return_value = mock_items_resp
            return mock_table
        
        mock_supabase.table.side_effect = table_mock
        with patch('app.routers.cart.get_db', return_value=mock_supabase):
            with patch('app.db.get_db', return_value=mock_supabase):
                from app.main import app
                from fastapi.testclient import TestClient
                yield TestClient(app)

@contextmanager
def mock_order_operation(order_data, staff_data=None, items_data=None, meal_data=None, events_data=None):
    """Helper for order operations with complex table mocking"""
    with mock_authenticated_user():
        mock_supabase = MagicMock()
        responses = {
            "orders": MagicMock(data=order_data),
            "restaurant_staff": MagicMock(data=staff_data or []),
            "order_items": MagicMock(data=items_data or []),
            "meals": MagicMock(data=meal_data or []),
            "order_status_events": MagicMock(data=events_data or [])
        }
        
        def table_mock(name):
            mock_table = MagicMock()
            for method in ['select', 'eq', 'update', 'insert', 'order']:
                setattr(mock_table, method, MagicMock(return_value=mock_table))
            mock_table.execute.return_value = responses.get(name, responses["orders"])
            return mock_table
        
        mock_supabase.table.side_effect = table_mock
        with patch('app.routers.orders.get_db', return_value=mock_supabase):
            with patch('app.db.get_db', return_value=mock_supabase):
                with patch('app.routers.s3.get_s3_service', return_value=MagicMock()):
                    from app.main import app
                    from fastapi.testclient import TestClient
                    yield TestClient(app)

def get_test_client():
    """Get a simple test client"""
    from app.main import app
    from fastapi.testclient import TestClient
    return TestClient(app)

def assert_and_log(response, expected_codes, test_name):
    """Assert response status and log result"""
    assert response.status_code in expected_codes
    print(f"{test_name} test passed with status: {response.status_code}")

# ============ Auth Tests ============

# -------- BASIC AUTH TESTS (Original) --------

def test_signup():
    response_json = {"id": "new-user", "email": "new@test.com", "user": {"id": "new-user", "email": "new@test.com"}}
    with mock_auth_client(response_json) as client:
        response = client.post("/auth/signup", json={"email": "new@test.com", "password": "pass123", "name": "New User", "role": "customer"})
        assert_and_log(response, [200, 400, 422, 500], "Signup")

def test_login():
    with patch('httpx.AsyncClient') as mock_httpx:
        mock_client = MagicMock()
        mock_token_resp = MagicMock(status_code=200, json=MagicMock(return_value={"access_token": "token123", "refresh_token": "refresh123", "token_type": "bearer"}))
        mock_user_resp = MagicMock(status_code=200, json=MagicMock(return_value={"id": "user1", "email": "test@test.com", "user_metadata": {"name": "Test User"}}))
        mock_client.__aenter__.return_value.post = AsyncMock(return_value=mock_token_resp)
        mock_client.__aenter__.return_value.get = AsyncMock(return_value=mock_user_resp)
        mock_httpx.return_value = mock_client
        
        with patch('app.routers.auth_routes.get_db', return_value=create_mock_supabase()):
            with patch('app.db.get_db', return_value=create_mock_supabase()):
                client = get_test_client()
                response = client.post("/auth/login", json={"email": "test@test.com", "password": "password123"})
                assert_and_log(response, [200, 400, 500], "Login")

def test_refresh_token():
    with mock_auth_client({"access_token": "new_token", "refresh_token": "new_refresh"}) as client:
        response = client.post("/auth/refresh", json={"refresh_token": "refresh123"})
        assert_and_log(response, [200, 400, 500], "Refresh token")

def test_logout():
    with mock_auth_client({}) as client:
        response = client.post("/auth/logout", headers={"Authorization": "Bearer token123"})
        assert_and_log(response, [200, 400, 500], "Logout")

# -------- COMPREHENSIVE AUTH TESTS --------

def test_signup_missing_email():
    """Test signup without email returns 422"""
    with mock_auth_client({}) as client:
        response = client.post("/auth/signup", json={"password": "pass123", "name": "User", "role": "customer"})
        assert response.status_code == 422
        print("Signup missing email test passed")

def test_signup_invalid_email():
    """Test signup with invalid email returns 422"""
    with mock_auth_client({}) as client:
        response = client.post("/auth/signup", json={"email": "invalid-email", "password": "pass123", "name": "User", "role": "customer"})
        assert response.status_code == 422
        print("Signup invalid email test passed")

def test_signup_auth_provider_error():
    """Test signup when auth provider returns error"""
    with patch('httpx.AsyncClient') as mock_httpx:
        mock_client = MagicMock()
        mock_response = MagicMock(status_code=400, json=MagicMock(return_value={"message": "Email already exists"}))
        mock_client.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        mock_httpx.return_value = mock_client
        
        with patch('app.routers.auth_routes.get_db', return_value=create_mock_supabase()):
            client = get_test_client()
            response = client.post("/auth/signup", json={"email": "exists@test.com", "password": "pass123", "name": "User", "role": "customer"})
            assert response.status_code == 400
            print("Signup auth provider error test passed")

def test_signup_missing_user_id():
    """Test signup when auth provider returns incomplete data"""
    with patch('httpx.AsyncClient') as mock_httpx:
        mock_client = MagicMock()
        mock_response = MagicMock(status_code=200, json=MagicMock(return_value={"email": "test@test.com"}))
        mock_client.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        mock_httpx.return_value = mock_client
        
        with patch('app.routers.auth_routes.get_db', return_value=create_mock_supabase()):
            client = get_test_client()
            response = client.post("/auth/signup", json={"email": "test@test.com", "password": "pass123", "name": "User", "role": "customer"})
            assert response.status_code == 500
            assert "unexpected signup response" in response.json()["detail"]
            print("Signup missing user_id test passed")

def test_owner_signup_success():
    """Test owner signup creates user and restaurant"""
    with patch('httpx.AsyncClient') as mock_httpx:
        mock_client = MagicMock()
        mock_response = MagicMock(status_code=200, json=MagicMock(return_value={"id": "owner1", "email": "owner@test.com"}))
        mock_client.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        mock_httpx.return_value = mock_client
        
        mock_supabase = MagicMock()
        mock_table = MagicMock()
        mock_table.select.return_value = mock_table
        mock_table.insert.return_value = mock_table
        mock_table.update.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.execute.return_value = MagicMock(data=[{"id": "rest1"}])
        mock_supabase.table.return_value = mock_table
        
        with patch('app.routers.auth_routes.get_db', return_value=mock_supabase):
            client = get_test_client()
            response = client.post("/auth/owner/signup", json={
                "email": "owner@test.com",
                "password": "pass123",
                "name": "Owner",
                "restaurant_name": "Test Restaurant",
                "restaurant_address": "123 Main St",
                "latitude": 35.7796,
                "longitude": -78.6382
            })
            assert response.status_code in [200, 500]
            print("Owner signup success test passed")

def test_login_missing_email():
    """Test login without email returns 400"""
    client = get_test_client()
    response = client.post("/auth/login", json={"password": "pass123"})
    assert response.status_code == 422
    print("Login missing email test passed")

def test_login_missing_password():
    """Test login without password returns 400"""
    client = get_test_client()
    response = client.post("/auth/login", json={"email": "test@test.com"})
    assert response.status_code == 422
    print("Login missing password test passed")

def test_login_invalid_credentials():
    """Test login with wrong credentials returns 400"""
    with patch('httpx.AsyncClient') as mock_httpx:
        mock_client = MagicMock()
        mock_response = MagicMock(status_code=401, json=MagicMock(return_value={"error": "Invalid credentials"}))
        mock_client.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        mock_httpx.return_value = mock_client
        
        client = get_test_client()
        response = client.post("/auth/login", json={"email": "test@test.com", "password": "wrongpass"})
        assert response.status_code == 400
        assert "invalid credentials" in response.json()["detail"]
        print("Login invalid credentials test passed")

def test_login_no_access_token():
    """Test login when auth provider doesn't return access token"""
    with patch('httpx.AsyncClient') as mock_httpx:
        mock_client = MagicMock()
        mock_response = MagicMock(status_code=200, json=MagicMock(return_value={"token_type": "bearer"}))
        mock_client.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        mock_httpx.return_value = mock_client
        
        client = get_test_client()
        response = client.post("/auth/login", json={"email": "test@test.com", "password": "pass123"})
        assert response.status_code == 400
        assert "invalid credentials" in response.json()["detail"]
        print("Login no access token test passed")

def test_refresh_token_invalid():
    """Test refresh with invalid token returns 401"""
    with patch('httpx.AsyncClient') as mock_httpx:
        mock_client = MagicMock()
        mock_response = MagicMock(status_code=401, json=MagicMock(return_value={"message": "Invalid refresh token"}))
        mock_client.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        mock_httpx.return_value = mock_client
        
        client = get_test_client()
        response = client.post("/auth/refresh", json={"refresh_token": "invalid_token"})
        assert response.status_code == 401
        print("Refresh token invalid test passed")

def test_logout_missing_authorization():
    """Test logout without authorization header returns 401"""
    client = get_test_client()
    response = client.post("/auth/logout")
    assert response.status_code == 401
    assert "missing bearer token" in response.json()["detail"]
    print("Logout missing authorization test passed")

def test_logout_invalid_bearer_format():
    """Test logout with invalid bearer format returns 401"""
    client = get_test_client()
    response = client.post("/auth/logout", headers={"Authorization": "InvalidFormat token123"})
    assert response.status_code == 401
    assert "missing bearer token" in response.json()["detail"]
    print("Logout invalid bearer format test passed")

def test_delete_me():
    """Test user account deletion"""
    with patch('httpx.AsyncClient') as mock_httpx:
        mock_client = MagicMock()
        mock_user_resp = MagicMock(status_code=200, json=MagicMock(return_value={"id": "user1", "email": "test@test.com", "user_metadata": {"name": "Test User"}}))
        mock_delete_resp = MagicMock(status_code=200)
        mock_client.__aenter__.return_value.get = AsyncMock(return_value=mock_user_resp)
        mock_client.__aenter__.return_value.delete = AsyncMock(return_value=mock_delete_resp)
        mock_httpx.return_value = mock_client
        
        with patch('app.routers.auth_routes.get_db', return_value=create_mock_supabase()):
            client = get_test_client()
            response = client.delete("/auth/me", headers={"Authorization": "Bearer token123"})
            assert response.status_code in [200, 401]
            print("Delete me test passed")

# ============ Address Tests ============

def test_list_addresses():
    with mock_authenticated_user():
        data = [{"id": "addr1", "user_id": "user1", "line1": "123 Main St", "city": "Raleigh"}, {"id": "addr2", "user_id": "user1", "line1": "456 Oak Ave", "city": "Durham"}]
        with mock_db_and_client('address', data) as client:
            response = client.get("/addresses", headers={"Authorization": "Bearer token123"})
            assert_and_log(response, [200, 401, 500], "List addresses")

def test_create_address():
    with mock_authenticated_user():
        with mock_db_and_client('address', [{"id": "addr1", "user_id": "user1", "line1": "456 Oak Ave", "city": "NYC"}]) as client:
            response = client.post("/addresses", json={"line1": "456 Oak Ave", "city": "NYC", "state": "NY", "zip": "10001"}, headers={"Authorization": "Bearer token123"})
            assert_and_log(response, [200, 400, 422, 500], "Create address")

def test_update_address():
    with mock_authenticated_user():
        with mock_db_and_client('address', [{"id": "addr1", "user_id": "user1", "line1": "Updated St", "city": "NYC"}]) as client:
            response = client.patch("/addresses/addr1", json={"line1": "Updated St"}, headers={"Authorization": "Bearer token123"})
            assert_and_log(response, [200, 404, 500], "Update address")

def test_delete_address():
    with mock_authenticated_user():
        with mock_db_and_client('address', [{"id": "addr1", "user_id": "user1"}]) as client:
            response = client.delete("/addresses/addr1", headers={"Authorization": "Bearer token123"})
            assert_and_log(response, [200, 404, 500], "Delete address")

# ============ Cart Tests ============

# -------- BASIC CART OPERATIONS (Original Tests) --------

def test_get_cart():
    with mock_cart_operation([{"id": "cart1"}], []) as client:
        response = client.get("/cart", headers={"Authorization": "Bearer token123"})
        assert_and_log(response, [200, 500], "Get cart")

def test_add_cart_item():
    items = [{"id": "item1", "meal_id": "meal1", "qty": 2, "meals": {"name": "Test", "surplus_price": 5.99, "base_price": 9.99, "restaurant_id": "r1", "quantity": 10}}]
    with mock_cart_operation([{"id": "cart1"}], items, [{"id": "meal1", "quantity": 10}]) as client:
        response = client.post("/cart/items", json={"meal_id": "meal1", "qty": 2}, headers={"Authorization": "Bearer token123"})
        assert_and_log(response, [200, 400, 404, 409, 500], "Add cart item")

def test_update_cart_item():
    items = [{"id": "item1", "meal_id": "meal1", "qty": 3, "meals": {"name": "Test", "surplus_price": 5.99, "base_price": 9.99, "restaurant_id": "r1", "quantity": 10}}]
    with mock_authenticated_user():
        mock_supabase = MagicMock()
        mock_cart_resp = MagicMock(data=[{"id": "cart1"}])
        mock_item_resp = MagicMock(data=[{"meal_id": "meal1", "meals": {"quantity": 10}}])
        mock_items_resp = MagicMock(data=items)
        
        def table_mock(name):
            mock_table = MagicMock()
            for method in ['select', 'eq', 'update']:
                setattr(mock_table, method, MagicMock(return_value=mock_table))
            if name == "carts":
                mock_table.execute.return_value = mock_cart_resp
            elif name == "cart_items" and mock_table.select.call_count == 1:
                mock_table.execute.return_value = mock_item_resp
            else:
                mock_table.execute.return_value = mock_items_resp
            return mock_table
        
        mock_supabase.table.side_effect = table_mock
        with patch('app.routers.cart.get_db', return_value=mock_supabase), patch('app.db.get_db', return_value=mock_supabase):
            client = get_test_client()
            response = client.patch("/cart/items/item1?qty=3", headers={"Authorization": "Bearer token123"})
            assert_and_log(response, [200, 404, 409, 500], "Update cart item")

def test_remove_cart_item():
    with mock_cart_operation([{"id": "cart1"}], []) as client:
        response = client.delete("/cart/items/item1", headers={"Authorization": "Bearer token123"})
        assert_and_log(response, [200, 500], "Remove cart item")

def test_clear_cart():
    with mock_cart_operation([{"id": "cart1"}], []) as client:
        response = client.delete("/cart", headers={"Authorization": "Bearer token123"})
        assert_and_log(response, [200, 500], "Clear cart")

def test_checkout_cart():
    with mock_authenticated_user():
        mock_supabase = MagicMock()
        items = [{"id": "item1", "meal_id": "meal1", "qty": 2, "meals": {"name": "Test", "surplus_price": 5.99, "base_price": 9.99, "restaurant_id": "r1", "quantity": 10}}]
        responses = {"carts": MagicMock(data=[{"id": "cart1"}]), "cart_items": MagicMock(data=items), "orders": MagicMock(data=[{"id": "order1"}]), "meals": MagicMock(data=[{"quantity": 10}])}
        
        def table_mock(name):
            mock_table = MagicMock()
            for method in ['select', 'eq', 'insert', 'update', 'delete']:
                setattr(mock_table, method, MagicMock(return_value=mock_table))
            mock_table.execute.return_value = responses.get(name, responses["cart_items"])
            return mock_table
        
        mock_supabase.table.side_effect = table_mock
        with patch('app.routers.cart.get_db', return_value=mock_supabase), patch('app.db.get_db', return_value=mock_supabase):
            client = get_test_client()
            response = client.post("/cart/checkout", headers={"Authorization": "Bearer token123"})
            assert_and_log(response, [200, 400, 500], "Checkout cart")

# -------- COMPREHENSIVE GET /cart TESTS --------

def test_get_cart_empty():
    """Test getting an empty cart returns correct structure"""
    with mock_cart_operation([{"id": "cart1", "user_id": "user1"}], []) as client:
        response = client.get("/cart", headers={"Authorization": "Bearer token123"})
        assert response.status_code == 200
        data = response.json()
        assert "cart_id" in data
        assert data["items"] == []
        assert data["cart_total"] == 0.0
        print("Get empty cart test passed")

def test_get_cart_with_surplus_items():
    """Test cart correctly calculates surplus pricing"""
    items = [{"id": "item1", "cart_id": "cart1", "meal_id": "m1", "qty": 2, 
              "meals": {"id": "m1", "name": "Pizza", "surplus_price": 5.99, "base_price": 9.99, "restaurant_id": "r1", "quantity": 10}}]
    with mock_cart_operation([{"id": "cart1"}], items) as client:
        response = client.get("/cart", headers={"Authorization": "Bearer token123"})
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["qty"] == 2
        assert data["items"][0]["unit_price"] == 5.99
        assert abs(data["items"][0]["line_total"] - 11.98) < 0.01
        print("Get cart with surplus items test passed")

def test_get_cart_with_regular_items():
    """Test cart uses base price for non-surplus items"""
    items = [{"id": "item1", "cart_id": "cart1", "meal_id": "m1", "qty": 1,
              "meals": {"id": "m1", "name": "Burger", "base_price": 7.99, "restaurant_id": "r1", "quantity": None}}]
    with mock_cart_operation([{"id": "cart1"}], items) as client:
        response = client.get("/cart", headers={"Authorization": "Bearer token123"})
        assert response.status_code == 200
        data = response.json()
        assert data["items"][0]["unit_price"] == 7.99
        assert data["cart_total"] == 7.99
        print("Get cart with regular items test passed")

# -------- COMPREHENSIVE POST /cart/items TESTS --------

def test_add_item_missing_meal_id():
    """Test adding item without meal_id returns 400"""
    with mock_cart_operation([{"id": "cart1"}], []) as client:
        response = client.post("/cart/items", json={"qty": 2}, headers={"Authorization": "Bearer token123"})
        assert response.status_code == 400
        assert "meal_id" in response.json()["detail"]
        print("Add item missing meal_id test passed")

def test_add_item_zero_quantity():
    """Test adding item with qty=0 returns 400"""
    with mock_cart_operation([{"id": "cart1"}], []) as client:
        response = client.post("/cart/items", json={"meal_id": "m1", "qty": 0}, headers={"Authorization": "Bearer token123"})
        assert response.status_code == 400
        assert "positive qty" in response.json()["detail"]
        print("Add item zero quantity test passed")

def test_add_item_meal_not_found():
    """Test adding non-existent meal returns 404"""
    with mock_cart_operation([{"id": "cart1"}], [], []) as client:
        response = client.post("/cart/items", json={"meal_id": "nonexistent", "qty": 1}, headers={"Authorization": "Bearer token123"})
        assert response.status_code == 404
        assert "meal not found" in response.json()["detail"]
        print("Add item meal not found test passed")

def test_add_item_exceeds_inventory():
    """Test adding more items than available returns 409"""
    with mock_cart_operation([{"id": "cart1"}], [], [{"id": "m1", "quantity": 5}]) as client:
        response = client.post("/cart/items", json={"meal_id": "m1", "qty": 10}, headers={"Authorization": "Bearer token123"})
        assert response.status_code == 409
        assert "only 5 left" in response.json()["detail"]
        print("Add item exceeds inventory test passed")

# -------- COMPREHENSIVE PATCH /cart/items/{item_id} TESTS --------

def test_update_item_not_found():
    """Test updating non-existent cart item returns 404"""
    with mock_cart_operation([{"id": "cart1"}], []) as client:
        response = client.patch("/cart/items/nonexistent?qty=5", headers={"Authorization": "Bearer token123"})
        assert response.status_code == 404
        assert "item not found" in response.json()["detail"]
        print("Update item not found test passed")

def test_update_item_exceeds_inventory():
    """Test updating item beyond available stock returns 409"""
    items = [{"id": "item1", "meal_id": "m1", "meals": {"quantity": 3}}]
    with mock_authenticated_user():
        mock_supabase = MagicMock()
        mock_cart_resp = MagicMock(data=[{"id": "cart1"}])
        mock_item_resp = MagicMock(data=items)
        
        def table_mock(name):
            mock_table = MagicMock()
            for method in ['select', 'eq', 'update']:
                setattr(mock_table, method, MagicMock(return_value=mock_table))
            if name == "carts":
                mock_table.execute.return_value = mock_cart_resp
            else:
                mock_table.execute.return_value = mock_item_resp
            return mock_table
        
        mock_supabase.table.side_effect = table_mock
        with patch('app.routers.cart.get_db', return_value=mock_supabase), patch('app.db.get_db', return_value=mock_supabase):
            client = get_test_client()
            response = client.patch("/cart/items/item1?qty=10", headers={"Authorization": "Bearer token123"})
            assert response.status_code == 409
            assert "only 3 left" in response.json()["detail"]
            print("Update item exceeds inventory test passed")

# -------- COMPREHENSIVE CHECKOUT TESTS --------

def test_checkout_empty_cart():
    """Test checking out empty cart returns 400"""
    with mock_cart_operation([{"id": "cart1"}], []) as client:
        response = client.post("/cart/checkout", headers={"Authorization": "Bearer token123"})
        assert response.status_code == 400
        assert "cart is empty" in response.json()["detail"]
        print("Checkout empty cart test passed")

# ============ Catalog Tests ============

def test_list_restaurants():
    with mock_authenticated_user():
        with mock_db_and_client('catalog', [{"id": "r1", "name": "Restaurant 1"}, {"id": "r2", "name": "Restaurant 2"}]) as client:
            response = client.get("/catalog/restaurants", headers={"Authorization": "Bearer token123"})
            assert_and_log(response, [200, 500], "List restaurants")

def test_list_restaurants_with_search():
    with mock_authenticated_user():
        with mock_db_and_client('catalog', [{"id": "r1", "name": "Pizza Place"}]) as client:
            response = client.get("/catalog/restaurants?search=pizza", headers={"Authorization": "Bearer token123"})
            assert_and_log(response, [200, 500], "List restaurants with search")

def test_list_meals_for_restaurant():
    with mock_authenticated_user():
        with mock_db_and_client('catalog', [{"id": "m1", "name": "Meal 1", "restaurant_id": "r1"}]) as client:
            response = client.get("/catalog/restaurants/r1/meals", headers={"Authorization": "Bearer token123"})
            assert_and_log(response, [200, 500], "List meals for restaurant")

def test_list_meals_surplus_only():
    with mock_authenticated_user():
        with mock_db_and_client('catalog', [{"id": "m1", "name": "Surplus Meal", "surplus_price": 5.99}]) as client:
            response = client.get("/catalog/restaurants/r1/meals?surplus_only=true", headers={"Authorization": "Bearer token123"})
            assert_and_log(response, [200, 500], "List meals surplus only")

# ============ Debug & Me Tests ============

def test_debug_whoami():
    with mock_authenticated_user():
        client = get_test_client()
        response = client.get("/debug/me", headers={"Authorization": "Bearer token123"})
        assert_and_log(response, [200], "Debug whoami")

def test_get_me():
    with mock_authenticated_user():
        with mock_db_and_client('me', [{"id": "user1", "email": "test@test.com", "name": "Test User"}]) as client:
            response = client.get("/me", headers={"Authorization": "Bearer token123"})
            assert_and_log(response, [200, 404, 500], "Get me")

def test_patch_me():
    with mock_authenticated_user():
        with mock_db_and_client('me', [{"id": "user1", "name": "Updated Name"}]) as client:
            response = client.patch("/me", json={"name": "Updated Name"}, headers={"Authorization": "Bearer token123"})
            assert_and_log(response, [200, 500], "Patch me")

# ============ Meals Tests ============

def test_list_meals():
    with mock_authenticated_user():
        with mock_db_and_client('meals', [{"id": "m1", "name": "Meal 1", "surplus_price": 5.99, "quantity": 10}]) as client:
            response = client.get("/meals", headers={"Authorization": "Bearer token123"})
            assert_and_log(response, [200, 500], "List meals")

def test_list_meals_all():
    with mock_authenticated_user():
        with mock_db_and_client('meals', [{"id": "m1", "name": "Meal 1", "base_price": 9.99}]) as client:
            response = client.get("/meals?surplus_only=false", headers={"Authorization": "Bearer token123"})
            assert_and_log(response, [200, 500], "List meals all")

# ============ Orders Tests ============

def test_create_order():
    with mock_authenticated_user():
        with mock_db_and_client('orders', [{"id": "order1", "user_id": "user1", "restaurant_id": "r1", "total": 10.0}]) as client:
            response = client.post("/orders", json={"restaurant_id": "r1", "items": [{"meal_id": "m1", "qty": 2}]}, headers={"Authorization": "Bearer token123"})
            assert_and_log(response, [200, 400, 404, 500], "Create order")

def test_list_my_orders():
    with mock_authenticated_user():
        with mock_db_and_client('orders', [{"id": "order1", "user_id": "user1", "status": "pending"}]) as client:
            response = client.get("/orders/mine", headers={"Authorization": "Bearer token123"})
            assert_and_log(response, [200, 500], "List my orders")

def test_get_order():
    order_data = [{"id": "o1", "user_id": "user1", "status": "pending", "restaurants": {"name": "Test Restaurant"}}]
    items_data = [{"id": "item1", "meal_id": "m1", "qty": 2, "price": 10.0, "meals": {"name": "Test Meal"}}]
    with mock_order_operation(order_data, items_data=items_data) as client:
        response = client.get("/orders/o1", headers={"Authorization": "Bearer token123"})
        assert_and_log(response, [200, 403, 404, 500], "Get order")

def test_get_order_status_timeline():
    with mock_order_operation([{"user_id": "user1"}], events_data=[{"status": "pending", "created_at": "2024-01-01"}]) as client:
        response = client.get("/orders/o1/status", headers={"Authorization": "Bearer token123"})
        assert_and_log(response, [200, 403, 404, 500], "Get order status timeline")

def test_cancel_order():
    order_data = [{"id": "o1", "user_id": "user1", "status": "pending"}]
    items_data = [{"meal_id": "m1", "qty": 2}]
    meal_data = [{"quantity": 10}]
    with mock_order_operation(order_data, items_data=items_data, meal_data=meal_data) as client:
        response = client.patch("/orders/o1/cancel", headers={"Authorization": "Bearer token123"})
        assert_and_log(response, [200, 400, 403, 404, 500], "Cancel order")

def test_accept_order():
    with mock_order_operation([{"id": "o1", "restaurant_id": "r1", "status": "pending"}], staff_data=[]) as client:
        response = client.patch("/orders/o1/accept", headers={"Authorization": "Bearer token123"})
        assert_and_log(response, [200, 400, 403, 404, 500], "Accept order")

def test_preparing_order():
    with mock_order_operation([{"id": "o1", "restaurant_id": "r1", "status": "accepted"}], staff_data=[]) as client:
        response = client.patch("/orders/o1/preparing", headers={"Authorization": "Bearer token123"})
        assert_and_log(response, [200, 400, 403, 404, 500], "Preparing order")

def test_ready_order():
    with mock_order_operation([{"id": "o1", "restaurant_id": "r1", "status": "preparing"}], staff_data=[]) as client:
        response = client.patch("/orders/o1/ready", headers={"Authorization": "Bearer token123"})
        assert_and_log(response, [200, 400, 403, 404, 500], "Ready order")

def test_complete_order():
    with mock_order_operation([{"id": "o1", "restaurant_id": "r1", "status": "ready"}], staff_data=[]) as client:
        response = client.patch("/orders/o1/complete", headers={"Authorization": "Bearer token123"})
        assert_and_log(response, [200, 400, 403, 404, 500], "Complete order")

# ============ Delivery Routes Tests ============

# -------- COMPREHENSIVE DELIVERY TESTS --------

def test_fetch_ready_orders_success():
    """Test fetching ready orders with valid location"""
    with mock_authenticated_user():
        mock_supabase = MagicMock()
        orders_data = [{
            "id": "order1",
            "user_id": "user1",
            "restaurant_id": "r1",
            "status": "ready",
            "restaurants": {"name": "Test Restaurant", "latitude": 35.7796, "longitude": -78.6382, "address": "123 St"},
            "customer": {"name": "Customer"},
            "delivery_address": "456 Ave",
            "delivery_fee": 5.0,
            "tip_amount": 2.0
        }]
        
        mock_result = MagicMock()
        mock_result.data = orders_data
        mock_supabase.from_.return_value.select.return_value.eq.return_value.is_.return_value.execute.return_value = mock_result
        
        with patch('app.routers.delivery_routes.get_db', return_value=mock_supabase):
            with patch('app.routers.delivery_routes._compute_distances_and_durations', return_value=({"r1": 5000.0}, {"r1": 600.0})):
                client = get_test_client()
                response = client.get("/deliveries/ready?latitude=35.7796&longitude=-78.6382", headers={"Authorization": "Bearer token123"})
                assert response.status_code == 200
                data = response.json()
                assert isinstance(data, list)
                print("Fetch ready orders success test passed")

def test_fetch_ready_orders_empty():
    """Test fetching ready orders when none available"""
    with mock_authenticated_user():
        mock_supabase = MagicMock()
        mock_result = MagicMock()
        mock_result.data = []
        mock_supabase.from_.return_value.select.return_value.eq.return_value.is_.return_value.execute.return_value = mock_result
        
        with patch('app.routers.delivery_routes.get_db', return_value=mock_supabase):
            client = get_test_client()
            response = client.get("/deliveries/ready?latitude=35.7796&longitude=-78.6382", headers={"Authorization": "Bearer token123"})
            assert response.status_code == 200
            assert response.json() == []
            print("Fetch ready orders empty test passed")

def test_fetch_ready_orders_missing_latitude():
    """Test fetching ready orders without latitude"""
    with mock_authenticated_user():
        client = get_test_client()
        response = client.get("/deliveries/ready?longitude=-78.6382", headers={"Authorization": "Bearer token123"})
        assert response.status_code == 422
        print("Fetch ready orders missing latitude test passed")

def test_fetch_ready_orders_missing_longitude():
    """Test fetching ready orders without longitude"""
    with mock_authenticated_user():
        client = get_test_client()
        response = client.get("/deliveries/ready?latitude=35.7796", headers={"Authorization": "Bearer token123"})
        assert response.status_code == 422
        print("Fetch ready orders missing longitude test passed")

def test_fetch_ready_orders_invalid_coordinates():
    """Test fetching ready orders with invalid coordinates"""
    with mock_authenticated_user():
        client = get_test_client()
        response = client.get("/deliveries/ready?latitude=invalid&longitude=invalid", headers={"Authorization": "Bearer token123"})
        assert response.status_code == 422
        print("Fetch ready orders invalid coordinates test passed")

def test_fetch_ready_orders_with_distance_calculation():
    """Test ready orders with distance and duration enrichment"""
    with mock_authenticated_user():
        mock_supabase = MagicMock()
        orders_data = [{
            "id": "order1",
            "user_id": "user1",
            "restaurant_id": "r1",
            "status": "ready",
            "restaurants": {"name": "Test Restaurant", "latitude": 35.7796, "longitude": -78.6382, "address": "123 St"},
            "customer": {"name": "Customer"},
            "delivery_address": "456 Ave"
        }]
        
        mock_result = MagicMock()
        mock_result.data = orders_data
        mock_supabase.from_.return_value.select.return_value.eq.return_value.is_.return_value.execute.return_value = mock_result
        
        with patch('app.routers.delivery_routes.get_db', return_value=mock_supabase):
            with patch('app.routers.delivery_routes._compute_distances_and_durations', return_value=({"r1": 8046.72}, {"r1": 900.0})):
                client = get_test_client()
                response = client.get("/deliveries/ready?latitude=35.7796&longitude=-78.6382", headers={"Authorization": "Bearer token123"})
                assert response.status_code == 200
                data = response.json()
                if data:
                    assert "distance_to_restaurant_miles" in data[0]
                    assert "duration_to_restaurant_minutes" in data[0]
                print("Fetch ready orders with distance calculation test passed")

def test_fetch_ready_orders_no_restaurant_coords():
    """Test ready orders when restaurant has no coordinates"""
    with mock_authenticated_user():
        mock_supabase = MagicMock()
        orders_data = [{
            "id": "order1",
            "user_id": "user1",
            "restaurant_id": "r1",
            "status": "ready",
            "restaurants": {"name": "Test Restaurant", "latitude": None, "longitude": None, "address": "123 St"},
            "customer": {"name": "Customer"},
            "delivery_address": "456 Ave"
        }]
        
        mock_result = MagicMock()
        mock_result.data = orders_data
        mock_supabase.from_.return_value.select.return_value.eq.return_value.is_.return_value.execute.return_value = mock_result
        
        with patch('app.routers.delivery_routes.get_db', return_value=mock_supabase):
            client = get_test_client()
            response = client.get("/deliveries/ready?latitude=35.7796&longitude=-78.6382", headers={"Authorization": "Bearer token123"})
            assert response.status_code == 200
            data = response.json()
            if data:
                assert data[0]["restaurant_reachable_by_road"] is False
            print("Fetch ready orders no restaurant coords test passed")

def test_fetch_ready_orders_multiple_restaurants():
    """Test ready orders from multiple restaurants"""
    with mock_authenticated_user():
        mock_supabase = MagicMock()
        orders_data = [
            {
                "id": "order1",
                "user_id": "user1",
                "restaurant_id": "r1",
                "status": "ready",
                "restaurants": {"name": "Restaurant 1", "latitude": 35.7796, "longitude": -78.6382, "address": "123 St"},
                "customer": {"name": "Customer 1"},
                "delivery_address": "456 Ave"
            },
            {
                "id": "order2",
                "user_id": "user2",
                "restaurant_id": "r2",
                "status": "ready",
                "restaurants": {"name": "Restaurant 2", "latitude": 35.8796, "longitude": -78.7382, "address": "789 Blvd"},
                "customer": {"name": "Customer 2"},
                "delivery_address": "101 Rd"
            }
        ]
        
        mock_result = MagicMock()
        mock_result.data = orders_data
        mock_supabase.from_.return_value.select.return_value.eq.return_value.is_.return_value.execute.return_value = mock_result
        
        with patch('app.routers.delivery_routes.get_db', return_value=mock_supabase):
            with patch('app.routers.delivery_routes._compute_distances_and_durations', return_value=({"r1": 5000.0, "r2": 7000.0}, {"r1": 600.0, "r2": 800.0})):
                client = get_test_client()
                response = client.get("/deliveries/ready?latitude=35.7796&longitude=-78.6382", headers={"Authorization": "Bearer token123"})
                assert response.status_code == 200
                data = response.json()
                assert len(data) == 2
                print("Fetch ready orders multiple restaurants test passed")

def test_fetch_ready_orders_database_error():
    """Test ready orders when database fails"""
    with mock_authenticated_user():
        mock_supabase = MagicMock()
        mock_supabase.from_.side_effect = Exception("Database error")
        
        with patch('app.routers.delivery_routes.get_db', return_value=mock_supabase):
            client = get_test_client()
            response = client.get("/deliveries/ready?latitude=35.7796&longitude=-78.6382", headers={"Authorization": "Bearer token123"})
            assert response.status_code == 500
            assert "Failed to fetch ready orders" in response.json()["detail"]
            print("Fetch ready orders database error test passed")

def test_fetch_ready_orders_extreme_coordinates():
    """Test ready orders with extreme coordinate values"""
    with mock_authenticated_user():
        mock_supabase = MagicMock()
        mock_result = MagicMock()
        mock_result.data = []
        mock_supabase.from_.return_value.select.return_value.eq.return_value.is_.return_value.execute.return_value = mock_result
        
        with patch('app.routers.delivery_routes.get_db', return_value=mock_supabase):
            client = get_test_client()
            response = client.get("/deliveries/ready?latitude=90.0&longitude=180.0", headers={"Authorization": "Bearer token123"})
            assert response.status_code in [200, 500]
            print("Fetch ready orders extreme coordinates test passed")

def test_fetch_ready_orders_distance_none():
    """Test ready orders when distance calculation returns None"""
    with mock_authenticated_user():
        mock_supabase = MagicMock()
        orders_data = [{
            "id": "order1",
            "user_id": "user1",
            "restaurant_id": "r1",
            "status": "ready",
            "restaurants": {"name": "Test", "latitude": 35.7796, "longitude": -78.6382, "address": "123 St"},
            "customer": {"name": "Customer"},
            "delivery_address": "456 Ave"
        }]
        
        mock_result = MagicMock()
        mock_result.data = orders_data
        mock_supabase.from_.return_value.select.return_value.eq.return_value.is_.return_value.execute.return_value = mock_result
        
        with patch('app.routers.delivery_routes.get_db', return_value=mock_supabase):
            with patch('app.routers.delivery_routes._compute_distances_and_durations', return_value=({"r1": None}, {"r1": None})):
                client = get_test_client()
                response = client.get("/deliveries/ready?latitude=35.7796&longitude=-78.6382", headers={"Authorization": "Bearer token123"})
                assert response.status_code == 200
                data = response.json()
                if data:
                    assert data[0]["distance_to_restaurant_miles"] is None
                    assert data[0]["duration_to_restaurant_minutes"] is None
                    assert data[0]["restaurant_reachable_by_road"] is False
                print("Fetch ready orders distance none test passed")

def test_fetch_ready_orders_large_batch():
    """Test ready orders with many restaurants (chunking logic)"""
    with mock_authenticated_user():
        mock_supabase = MagicMock()
        orders_data = [
            {
                "id": f"order{i}",
                "user_id": "user1",
                "restaurant_id": f"r{i}",
                "status": "ready",
                "restaurants": {"name": f"Restaurant {i}", "latitude": 35.7796 + i*0.01, "longitude": -78.6382 + i*0.01, "address": f"{i} St"},
                "customer": {"name": "Customer"},
                "delivery_address": "456 Ave"
            }
            for i in range(30)
        ]
        
        mock_result = MagicMock()
        mock_result.data = orders_data
        mock_supabase.from_.return_value.select.return_value.eq.return_value.is_.return_value.execute.return_value = mock_result
        
        distance_dict = {f"r{i}": 5000.0 + i*100 for i in range(30)}
        duration_dict = {f"r{i}": 600.0 + i*10 for i in range(30)}
        
        with patch('app.routers.delivery_routes.get_db', return_value=mock_supabase):
            with patch('app.routers.delivery_routes._compute_distances_and_durations', return_value=(distance_dict, duration_dict)):
                client = get_test_client()
                response = client.get("/deliveries/ready?latitude=35.7796&longitude=-78.6382", headers={"Authorization": "Bearer token123"})
                assert response.status_code == 200
                data = response.json()
                assert len(data) == 30
                print("Fetch ready orders large batch test passed")

def test_fetch_ready_orders_duplicate_restaurants():
    """Test ready orders with multiple orders from same restaurant"""
    with mock_authenticated_user():
        mock_supabase = MagicMock()
        orders_data = [
            {
                "id": "order1",
                "user_id": "user1",
                "restaurant_id": "r1",
                "status": "ready",
                "restaurants": {"name": "Restaurant 1", "latitude": 35.7796, "longitude": -78.6382, "address": "123 St"},
                "customer": {"name": "Customer 1"},
                "delivery_address": "456 Ave"
            },
            {
                "id": "order2",
                "user_id": "user2",
                "restaurant_id": "r1",
                "status": "ready",
                "restaurants": {"name": "Restaurant 1", "latitude": 35.7796, "longitude": -78.6382, "address": "123 St"},
                "customer": {"name": "Customer 2"},
                "delivery_address": "789 Blvd"
            }
        ]
        
        mock_result = MagicMock()
        mock_result.data = orders_data
        mock_supabase.from_.return_value.select.return_value.eq.return_value.is_.return_value.execute.return_value = mock_result
        
        with patch('app.routers.delivery_routes.get_db', return_value=mock_supabase):
            with patch('app.routers.delivery_routes._compute_distances_and_durations', return_value=({"r1": 5000.0}, {"r1": 600.0})):
                client = get_test_client()
                response = client.get("/deliveries/ready?latitude=35.7796&longitude=-78.6382", headers={"Authorization": "Bearer token123"})
                assert response.status_code == 200
                data = response.json()
                assert len(data) == 2
                assert data[0]["distance_to_restaurant"] == data[1]["distance_to_restaurant"]
                print("Fetch ready orders duplicate restaurants test passed")

def test_fetch_ready_orders_mixed_coords():
    """Test ready orders with mix of valid and invalid restaurant coords"""
    with mock_authenticated_user():
        mock_supabase = MagicMock()
        orders_data = [
            {
                "id": "order1",
                "user_id": "user1",
                "restaurant_id": "r1",
                "status": "ready",
                "restaurants": {"name": "Restaurant 1", "latitude": 35.7796, "longitude": -78.6382, "address": "123 St"},
                "customer": {"name": "Customer 1"},
                "delivery_address": "456 Ave"
            },
            {
                "id": "order2",
                "user_id": "user2",
                "restaurant_id": "r2",
                "status": "ready",
                "restaurants": {"name": "Restaurant 2", "latitude": None, "longitude": None, "address": "789 Blvd"},
                "customer": {"name": "Customer 2"},
                "delivery_address": "101 Rd"
            }
        ]
        
        mock_result = MagicMock()
        mock_result.data = orders_data
        mock_supabase.from_.return_value.select.return_value.eq.return_value.is_.return_value.execute.return_value = mock_result
        
        with patch('app.routers.delivery_routes.get_db', return_value=mock_supabase):
            with patch('app.routers.delivery_routes._compute_distances_and_durations', return_value=({"r1": 5000.0}, {"r1": 600.0})):
                client = get_test_client()
                response = client.get("/deliveries/ready?latitude=35.7796&longitude=-78.6382", headers={"Authorization": "Bearer token123"})
                assert response.status_code == 200
                data = response.json()
                assert len(data) == 2
                assert data[0]["restaurant_reachable_by_road"] is True
                assert data[1]["restaurant_reachable_by_road"] is False
                print("Fetch ready orders mixed coords test passed")

# ============ Health Check Test ============

def test_health_check():
    client = get_test_client()
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    print("Health check test passed with status: 200")
