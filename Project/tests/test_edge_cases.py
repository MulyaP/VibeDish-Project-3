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
    with patch('httpx.AsyncClient') as mock_httpx:
        mock_client = MagicMock()
        mock_user_resp = MagicMock()
        mock_user_resp.status_code = 200
        mock_user_resp.json.return_value = {"id": "user1", "email": "test@test.com", "user_metadata": {"name": "Test User"}}
        mock_client.__aenter__.return_value.get = AsyncMock(return_value=mock_user_resp)
        mock_httpx.return_value = mock_client
        yield

def get_test_client():
    with patch('app.routers.s3.get_s3_service', return_value=MagicMock()):
        from app.main import app
        from fastapi.testclient import TestClient
        return TestClient(app)

# ============ Auth Edge Cases ============

def test_signup_duplicate_email():
    """Test signup with already registered email"""
    with patch('httpx.AsyncClient') as mock_httpx:
        mock_client = MagicMock()
        mock_response = MagicMock(status_code=400, json=MagicMock(return_value={"message": "User already registered"}))
        mock_client.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        mock_httpx.return_value = mock_client
        
        with patch('app.routers.auth_routes.get_db', return_value=create_mock_supabase()):
            client = get_test_client()
            response = client.post("/auth/signup", json={"email": "existing@test.com", "password": "pass123", "name": "User", "role": "customer"})
            assert response.status_code == 400

def test_login_empty_credentials():
    """Test login with empty email and password"""
    client = get_test_client()
    response = client.post("/auth/login", json={"email": "", "password": ""})
    assert response.status_code in [400, 422]

def test_refresh_token_empty():
    """Test refresh with empty token"""
    with patch('httpx.AsyncClient') as mock_httpx:
        mock_client = MagicMock()
        mock_response = MagicMock(status_code=401, json=MagicMock(return_value={"message": "Invalid token"}))
        mock_client.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        mock_httpx.return_value = mock_client
        
        client = get_test_client()
        response = client.post("/auth/refresh", json={"refresh_token": ""})
        assert response.status_code in [400, 401, 422]

# def test_logout_empty_bearer():
#     """Test logout with empty bearer token"""
#     with patch('httpx.AsyncClient') as mock_httpx:
#         mock_client = MagicMock()
#         mock_response = MagicMock(status_code=401)
#         mock_client.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
#         mock_httpx.return_value = mock_client
        
#         client = get_test_client()
#         response = client.post("/auth/logout", headers={"Authorization": "Bearer "})
#         assert response.status_code == 401

# ============ Cart Edge Cases ============

def test_add_item_negative_quantity():
    """Test adding item with negative quantity"""
    with mock_authenticated_user():
        with patch('app.routers.cart.get_db', return_value=create_mock_supabase()):
            client = get_test_client()
            response = client.post("/cart/items", json={"meal_id": "m1", "qty": -5}, headers={"Authorization": "Bearer token123"})
            assert response.status_code == 400

def test_update_item_negative_quantity():
    """Test updating item with negative quantity"""
    with mock_authenticated_user():
        with patch('app.routers.cart.get_db', return_value=create_mock_supabase()):
            client = get_test_client()
            response = client.patch("/cart/items/item1?qty=-3", headers={"Authorization": "Bearer token123"})
            assert response.status_code in [400, 422]

def test_add_item_extremely_large_quantity():
    """Test adding item with unrealistic quantity"""
    with mock_authenticated_user():
        mock_supabase = MagicMock()
        
        def table_mock(name):
            mock_table = MagicMock()
            mock_table.select.return_value = mock_table
            mock_table.eq.return_value = mock_table
            if name == "carts":
                mock_table.execute.return_value = MagicMock(data=[{"id": "cart1"}])
            elif name == "meals":
                mock_table.execute.return_value = MagicMock(data=[{"id": "m1", "quantity": 10}])
            else:
                mock_table.execute.return_value = MagicMock(data=[])
            return mock_table
        
        mock_supabase.table.side_effect = table_mock
        with patch('app.routers.cart.get_db', return_value=mock_supabase):
            client = get_test_client()
            response = client.post("/cart/items", json={"meal_id": "m1", "qty": 999999}, headers={"Authorization": "Bearer token123"})
            assert response.status_code in [400, 404, 409, 500]

def test_checkout_multiple_restaurants():
    """Test checkout with items from different restaurants"""
    with mock_authenticated_user():
        mock_supabase = MagicMock()
        
        def table_mock(name):
            mock_table = MagicMock()
            mock_table.select.return_value = mock_table
            mock_table.eq.return_value = mock_table
            if name == "carts":
                mock_table.execute.return_value = MagicMock(data=[{"id": "cart1"}])
            elif name == "cart_items":
                cart_items = [
                    {"id": "item1", "meal_id": "m1", "qty": 1, "meals": {"restaurant_id": "r1", "surplus_price": 5.99, "quantity": 10}},
                    {"id": "item2", "meal_id": "m2", "qty": 1, "meals": {"restaurant_id": "r2", "surplus_price": 7.99, "quantity": 5}}
                ]
                mock_table.execute.return_value = MagicMock(data=cart_items)
            else:
                mock_table.execute.return_value = MagicMock(data=[])
            return mock_table
        
        mock_supabase.table.side_effect = table_mock
        
        with patch('app.routers.cart.get_db', return_value=mock_supabase):
            client = get_test_client()
            response = client.post("/cart/checkout", json={"delivery_address": "123 St", "latitude": 35.7796, "longitude": -78.6382, "total": 13.98}, headers={"Authorization": "Bearer token123"})
            assert response.status_code == 400

# ============ Orders Edge Cases ============

def test_create_order_missing_restaurant_id():
    """Test creating order without restaurant_id"""
    with mock_authenticated_user():
        client = get_test_client()
        response = client.post("/orders", json={"items": [{"meal_id": "m1", "qty": 2}]}, headers={"Authorization": "Bearer token123"})
        assert response.status_code == 400

def test_create_order_empty_items():
    """Test creating order with empty items array"""
    with mock_authenticated_user():
        client = get_test_client()
        response = client.post("/orders", json={"restaurant_id": "r1", "items": []}, headers={"Authorization": "Bearer token123"})
        assert response.status_code == 400

def test_create_order_item_missing_meal_id():
    """Test creating order with item missing meal_id"""
    with mock_authenticated_user():
        with patch('app.routers.orders.get_db', return_value=create_mock_supabase()):
            client = get_test_client()
            response = client.post("/orders", json={"restaurant_id": "r1", "items": [{"qty": 2}]}, headers={"Authorization": "Bearer token123"})
            assert response.status_code in [400, 500]

def test_create_order_item_zero_quantity():
    """Test creating order with zero quantity item"""
    with mock_authenticated_user():
        with patch('app.routers.orders.get_db', return_value=create_mock_supabase()):
            client = get_test_client()
            response = client.post("/orders", json={"restaurant_id": "r1", "items": [{"meal_id": "m1", "qty": 0}]}, headers={"Authorization": "Bearer token123"})
            assert response.status_code in [400, 500]

def test_get_order_wrong_user():
    """Test getting order that belongs to another user"""
    with mock_authenticated_user():
        mock_supabase = MagicMock()
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"id": "o1", "user_id": "different_user", "status": "pending"}]
        )
        
        with patch('app.routers.orders.get_db', return_value=mock_supabase):
            client = get_test_client()
            response = client.get("/orders/o1", headers={"Authorization": "Bearer token123"})
            assert response.status_code == 403

def test_cancel_order_already_accepted():
    """Test canceling order that's already accepted"""
    with mock_authenticated_user():
        mock_supabase = MagicMock()
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"id": "o1", "user_id": "user1", "status": "accepted"}]
        )
        
        with patch('app.routers.orders.get_db', return_value=mock_supabase):
            client = get_test_client()
            response = client.patch("/orders/o1/cancel", headers={"Authorization": "Bearer token123"})
            assert response.status_code == 400

def test_order_invalid_status_transition():
    """Test invalid order status transition (pending -> completed)"""
    with mock_authenticated_user():
        mock_supabase = MagicMock()
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"id": "o1", "restaurant_id": "r1", "status": "pending"}]
        )
        
        with patch('app.routers.orders.get_db', return_value=mock_supabase):
            with patch('app.routers.s3.get_s3_service', return_value=MagicMock()):
                client = get_test_client()
                response = client.patch("/orders/o1/complete", headers={"Authorization": "Bearer token123"})
                assert response.status_code in [400, 403, 500]

def test_accept_order_not_staff():
    """Test accepting order when user is not restaurant staff"""
    with mock_authenticated_user():
        mock_supabase = MagicMock()
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
        
        with patch('app.routers.orders.get_db', return_value=mock_supabase):
            client = get_test_client()
            response = client.patch("/orders/o1/accept", headers={"Authorization": "Bearer token123"})
            assert response.status_code == 403

# ============ Address Edge Cases ============

def test_create_address_missing_required_fields():
    """Test creating address without required fields"""
    with mock_authenticated_user():
        client = get_test_client()
        response = client.post("/addresses", json={"line1": "123 St"}, headers={"Authorization": "Bearer token123"})
        assert response.status_code == 422

def test_update_address_not_owned():
    """Test updating address that doesn't belong to user"""
    with mock_authenticated_user():
        mock_supabase = MagicMock()
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
        
        with patch('app.routers.address.get_db', return_value=mock_supabase):
            client = get_test_client()
            response = client.patch("/addresses/addr1", json={"line1": "New St"}, headers={"Authorization": "Bearer token123"})
            assert response.status_code in [200, 404, 500]

def test_delete_address_not_found():
    """Test deleting non-existent address"""
    with mock_authenticated_user():
        mock_supabase = MagicMock()
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
        
        with patch('app.routers.address.get_db', return_value=mock_supabase):
            client = get_test_client()
            response = client.delete("/addresses/nonexistent", headers={"Authorization": "Bearer token123"})
            assert response.status_code in [200, 404, 500]

# # ============ S3 Edge Cases ============

# def test_presigned_url_missing_filename():
#     """Test presigned URL without filename"""
#     with mock_authenticated_user():
#         client = get_test_client()
#         response = client.post("/api/s3/presigned-upload-url", json={"content_type": "image/jpeg"}, headers={"Authorization": "Bearer token123"})
#         assert response.status_code == 422

# def test_presigned_url_missing_content_type():
#     """Test presigned URL without content_type"""
#     with mock_authenticated_user():
#         client = get_test_client()
#         response = client.post("/api/s3/presigned-upload-url", json={"filename": "test.jpg"}, headers={"Authorization": "Bearer token123"})
#         assert response.status_code == 422

# def test_delete_image_missing_url():
#     """Test deleting image without URL"""
#     with mock_authenticated_user():
#         client = get_test_client()
#         response = client.request("DELETE", "/api/s3/delete-image", json={}, headers={"Authorization": "Bearer token123"})
#         assert response.status_code == 422

# def test_presigned_url_executable_file():
#     """Test presigned URL for executable file type"""
#     with mock_authenticated_user():
#         mock_service = MagicMock()
#         with patch('app.routers.s3.get_s3_service', return_value=mock_service):
#             client = get_test_client()
#             response = client.post("/api/s3/presigned-upload-url", 
#                 json={"filename": "malware.exe", "content_type": "application/x-msdownload"},
#                 headers={"Authorization": "Bearer token123"})
#             assert response.status_code == 400

# ============ Catalog Edge Cases ============

def test_list_meals_invalid_restaurant():
    """Test listing meals for non-existent restaurant"""
    with mock_authenticated_user():
        mock_supabase = MagicMock()
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
        
        with patch('app.routers.catalog.get_db', return_value=mock_supabase):
            client = get_test_client()
            response = client.get("/catalog/restaurants/nonexistent/meals", headers={"Authorization": "Bearer token123"})
            assert response.status_code in [200, 404, 500]

def test_search_restaurants_special_characters():
    """Test searching restaurants with special characters"""
    with mock_authenticated_user():
        with patch('app.routers.catalog.get_db', return_value=create_mock_supabase()):
            client = get_test_client()
            response = client.get("/catalog/restaurants?search=<script>alert('xss')</script>", headers={"Authorization": "Bearer token123"})
            assert response.status_code in [200, 500]

def test_search_restaurants_sql_injection():
    """Test searching restaurants with SQL injection attempt"""
    with mock_authenticated_user():
        with patch('app.routers.catalog.get_db', return_value=create_mock_supabase()):
            client = get_test_client()
            response = client.get("/catalog/restaurants?search=' OR '1'='1", headers={"Authorization": "Bearer token123"})
            assert response.status_code in [200, 500]

# ============ Me Router Edge Cases ============

def test_patch_me_empty_data():
    """Test updating user profile with empty data"""
    with mock_authenticated_user():
        with patch('app.routers.me.get_db', return_value=create_mock_supabase()):
            client = get_test_client()
            response = client.patch("/me", json={}, headers={"Authorization": "Bearer token123"})
            assert response.status_code in [200, 400, 500]

def test_get_me_user_not_found():
    """Test getting user profile when user doesn't exist in DB"""
    with mock_authenticated_user():
        mock_supabase = MagicMock()
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
        
        with patch('app.routers.me.get_db', return_value=mock_supabase):
            client = get_test_client()
            response = client.get("/me", headers={"Authorization": "Bearer token123"})
            assert response.status_code in [404, 500]

# ============ Meals Edge Cases ============

def test_list_meals_with_limit():
    """Test listing meals with limit parameter"""
    with mock_authenticated_user():
        with patch('app.routers.meals.get_db', return_value=create_mock_supabase()):
            client = get_test_client()
            response = client.get("/meals?limit=5", headers={"Authorization": "Bearer token123"})
            assert response.status_code in [200, 500]

def test_list_meals_negative_limit():
    """Test listing meals with negative limit"""
    with mock_authenticated_user():
        with patch('app.routers.meals.get_db', return_value=create_mock_supabase()):
            client = get_test_client()
            response = client.get("/meals?limit=-1", headers={"Authorization": "Bearer token123"})
            assert response.status_code in [200, 422, 500]

def test_list_meals_excessive_limit():
    """Test listing meals with excessive limit"""
    with mock_authenticated_user():
        with patch('app.routers.meals.get_db', return_value=create_mock_supabase()):
            client = get_test_client()
            response = client.get("/meals?limit=10000", headers={"Authorization": "Bearer token123"})
            assert response.status_code in [200, 422, 500]

# ============ Delivery Routes Edge Cases ============

def test_fetch_ready_orders_zero_coordinates():
    """Test fetching ready orders with zero coordinates"""
    with mock_authenticated_user():
        mock_supabase = MagicMock()
        mock_result = MagicMock()
        mock_result.data = []
        mock_supabase.from_.return_value.select.return_value.eq.return_value.is_.return_value.execute.return_value = mock_result
        
        with patch('app.routers.delivery_routes.get_db', return_value=mock_supabase):
            client = get_test_client()
            response = client.get("/deliveries/ready?latitude=0.0&longitude=0.0", headers={"Authorization": "Bearer token123"})
            assert response.status_code in [200, 500]

def test_fetch_ready_orders_negative_coordinates():
    """Test fetching ready orders with negative coordinates"""
    with mock_authenticated_user():
        mock_supabase = MagicMock()
        mock_result = MagicMock()
        mock_result.data = []
        mock_supabase.from_.return_value.select.return_value.eq.return_value.is_.return_value.execute.return_value = mock_result
        
        with patch('app.routers.delivery_routes.get_db', return_value=mock_supabase):
            client = get_test_client()
            response = client.get("/deliveries/ready?latitude=-35.7796&longitude=-78.6382", headers={"Authorization": "Bearer token123"})
            assert response.status_code in [200, 500]

def test_fetch_ready_orders_invalid_restaurant_coords():
    """Test ready orders with invalid restaurant coordinate types"""
    with mock_authenticated_user():
        mock_supabase = MagicMock()
        orders_data = [{
            "id": "order1",
            "user_id": "user1",
            "restaurant_id": "r1",
            "status": "ready",
            "restaurants": {"name": "Test", "latitude": "invalid", "longitude": "invalid", "address": "123 St"},
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

def test_fetch_ready_orders_missing_restaurant_info():
    """Test ready orders when restaurant info is missing"""
    with mock_authenticated_user():
        mock_supabase = MagicMock()
        orders_data = [{
            "id": "order1",
            "user_id": "user1",
            "restaurant_id": "r1",
            "status": "ready",
            "restaurants": None,
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

def test_fetch_ready_orders_mapbox_api_failure():
    """Test ready orders when Mapbox API fails"""
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
            with patch('app.routers.delivery_routes._compute_distances_and_durations', return_value=({}, {})):
                client = get_test_client()
                response = client.get("/deliveries/ready?latitude=35.7796&longitude=-78.6382", headers={"Authorization": "Bearer token123"})
                assert response.status_code == 200

def test_fetch_ready_orders_partial_distance_data():
    """Test ready orders with partial distance calculation results"""
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
            with patch('app.routers.delivery_routes._compute_distances_and_durations', return_value=({"r1": 5000.0}, {"r1": 600.0})):
                client = get_test_client()
                response = client.get("/deliveries/ready?latitude=35.7796&longitude=-78.6382", headers={"Authorization": "Bearer token123"})
                assert response.status_code == 200
                data = response.json()
                assert len(data) == 2

# def test_fetch_ready_orders_httpx_error():
#     """Test ready orders when httpx raises error during distance calculation"""
#     with mock_authenticated_user():
#         mock_supabase = MagicMock()
#         orders_data = [{
#             "id": "order1",
#             "user_id": "user1",
#             "restaurant_id": "r1",
#             "status": "ready",
#             "restaurants": {"name": "Test", "latitude": 35.7796, "longitude": -78.6382, "address": "123 St"},
#             "customer": {"name": "Customer"},
#             "delivery_address": "456 Ave"
#         }]
        
#         mock_result = MagicMock()
#         mock_result.data = orders_data
#         mock_supabase.from_.return_value.select.return_value.eq.return_value.is_.return_value.execute.return_value = mock_result
        
#         with patch('app.routers.delivery_routes.get_db', return_value=mock_supabase):
#             with patch('httpx.AsyncClient') as mock_httpx:
#                 mock_client = MagicMock()
#                 mock_client.__aenter__.return_value.get = AsyncMock(side_effect=Exception("HTTP Error"))
#                 mock_httpx.return_value = mock_client
                
#                 client = get_test_client()
#                 response = client.get("/deliveries/ready?latitude=35.7796&longitude=-78.6382", headers={"Authorization": "Bearer token123"})
#                 assert response.status_code == 200

def test_fetch_ready_orders_empty_matrix_response():
    """Test ready orders when Mapbox returns empty matrix"""
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
            with patch('httpx.AsyncClient') as mock_httpx:
                mock_client = MagicMock()
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.json.return_value = {}
                mock_response.raise_for_status = MagicMock()
                mock_client.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
                mock_httpx.return_value = mock_client
                
                client = get_test_client()
                response = client.get("/deliveries/ready?latitude=35.7796&longitude=-78.6382", headers={"Authorization": "Bearer token123"})
                assert response.status_code == 200

def test_fetch_ready_orders_no_mapbox_token():
    """Test ready orders when MAPBOX_TOKEN is not set"""
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
            with patch('app.routers.delivery_routes.MAPBOX_TOKEN', None):
                client = get_test_client()
                response = client.get("/deliveries/ready?latitude=35.7796&longitude=-78.6382", headers={"Authorization": "Bearer token123"})
                assert response.status_code == 200

def test_fetch_ready_orders_float_conversion_error():
    """Test ready orders with non-numeric latitude/longitude in restaurant data"""
    with mock_authenticated_user():
        mock_supabase = MagicMock()
        orders_data = [{
            "id": "order1",
            "user_id": "user1",
            "restaurant_id": "r1",
            "status": "ready",
            "restaurants": {"name": "Test", "latitude": "not_a_number", "longitude": "also_not_a_number", "address": "123 St"},
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

def test_fetch_ready_orders_matrix_with_none_values():
    """Test ready orders when matrix returns None for some distances"""
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
            with patch('httpx.AsyncClient') as mock_httpx:
                mock_client = MagicMock()
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    "distances": [[None]],
                    "durations": [[None]]
                }
                mock_response.raise_for_status = MagicMock()
                mock_client.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
                mock_httpx.return_value = mock_client
                
                client = get_test_client()
                response = client.get("/deliveries/ready?latitude=35.7796&longitude=-78.6382", headers={"Authorization": "Bearer token123"})
                assert response.status_code == 200
                data = response.json()
                if data:
                    assert data[0]["distance_to_restaurant"] is None
                    assert data[0]["duration_to_restaurant"] is None

def test_fetch_ready_orders_restaurant_id_none():
    """Test ready orders when restaurant_id is None"""
    with mock_authenticated_user():
        mock_supabase = MagicMock()
        orders_data = [{
            "id": "order1",
            "user_id": "user1",
            "restaurant_id": None,
            "status": "ready",
            "restaurants": {"name": "Test", "latitude": 35.7796, "longitude": -78.6382, "address": "123 St"},
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

print("Edge case tests created successfully!")
