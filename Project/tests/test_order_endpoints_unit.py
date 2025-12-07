"""
End-to-End Order Flow Integration Tests - Fixed Version

Following the working pattern from test_auth_routes.py
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.auth import current_user

# Mock users
CUSTOMER_USER = {"id": "customer-123", "email": "customer@test.com"}
RESTAURANT_STAFF = {"id": "staff-456", "email": "staff@test.com"}
DRIVER_USER = {"id": "driver-789", "email": "driver@test.com"}


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_customer():
    def override():
        return CUSTOMER_USER
    app.dependency_overrides[current_user] = override
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def mock_restaurant_staff():
    def override():
        return RESTAURANT_STAFF
    app.dependency_overrides[current_user] = override
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def mock_driver():
    def override():
        return DRIVER_USER
    app.dependency_overrides[current_user] = override
    yield
    app.dependency_overrides.clear()


class TestOrderFlowEdgeCases:
    """Test edge cases"""
    
    @patch("app.routers.cart.get_db")
    @patch("app.routers.cart._get_or_create_cart_id")
    def test_checkout_empty_cart(self, mock_cart_id, mock_db, client, mock_customer):
        """Test checkout fails with empty cart"""
        mock_supabase = Mock()
        mock_db.return_value = mock_supabase
        mock_cart_id.return_value = "cart-1"
        
        # Empty cart items
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
        
        response = client.post("/cart/checkout", json={
            "delivery_address": "123 St",
            "latitude": 40.7,
            "longitude": -74.0,
            "tax": 0,
            "tip_amount": 0,
            "total": 0,
            "delivery_fee": 0
        })
        assert response.status_code == 400
        assert "empty" in response.json()["detail"].lower()
    
    @patch("app.routers.cart.get_db")
    def test_insufficient_meal_quantity(self, mock_db, client, mock_customer):
        """Test adding more items than available"""
        mock_supabase = Mock()
        mock_db.return_value = mock_supabase
        
        # Cart exists
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [{"id": "cart-1"}]
        # Meal has only 1 item
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [{"id": "meal-1", "quantity": 1}]
        # No existing cart item
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = []
        
        response = client.post("/cart/items", json={"meal_id": "meal-1", "qty": 5})
        assert response.status_code == 409
    
    @patch("app.routers.orders.get_db")
    def test_cancel_order_after_accepted(self, mock_db, client, mock_customer):
        """Test cannot cancel accepted order"""
        mock_supabase = Mock()
        mock_db.return_value = mock_supabase
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [{
            "id": "order-1",
            "user_id": "customer-123",
            "status": "accepted"
        }]
        
        response = client.patch("/orders/order-1/cancel")
        assert response.status_code == 400
        assert "cannot cancel" in response.json()["detail"].lower()
    
    @patch("app.routers.orders.get_db")
    @patch("app.routers.orders._is_user_staff_for_order")
    def test_invalid_status_transition(self, mock_staff_check, mock_db, client, mock_restaurant_staff):
        """Test invalid status transition"""
        mock_supabase = Mock()
        mock_db.return_value = mock_supabase
        mock_staff_check.return_value = True
        
        # Order is pending
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [{
            "id": "order-1",
            "status": "pending",
            "restaurant_id": "rest-1"
        }]
        
        # Try to skip to ready (invalid: pending -> ready not allowed)
        response = client.patch("/orders/order-1/ready")
        assert response.status_code == 400
        assert "invalid transition" in response.json()["detail"].lower()
    
    @patch("app.routers.delivery_routes.get_db")
    def test_driver_accepts_with_active_order(self, mock_db, client, mock_driver):
        """Test driver cannot accept multiple orders"""
        mock_supabase = Mock()
        mock_db.return_value = mock_supabase
        
        # Driver already has active order
        mock_supabase.table.return_value.select.return_value.eq.return_value.in_.return_value.execute.return_value.data = [{"id": "order-999"}]
        
        response = client.patch("/deliveries/order-1/accept")
        assert response.status_code == 400
        assert "already have an active" in response.json()["detail"].lower()
    
    @patch("app.routers.orders.get_db")
    def test_wrong_delivery_code(self, mock_db, client, mock_driver):
        """Test wrong delivery code"""
        mock_supabase = Mock()
        mock_db.return_value = mock_supabase
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [{
            "id": "order-1",
            "delivery_user_id": "driver-789",
            "delivery_code": "123456"
        }]
        
        response = client.patch("/orders/order-1/status", json={
            "status": "delivered",
            "delivery_code": "999999"
        })
        assert response.status_code == 400
        assert "invalid" in response.json()["detail"].lower()
    
    @patch("app.routers.feedback.get_db")
    def test_feedback_on_incomplete_order(self, mock_db, client, mock_customer):
        """Test feedback only on completed orders"""
        mock_supabase = Mock()
        mock_db.return_value = mock_supabase
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [{
            "user_id": "customer-123",
            "status": "preparing",
            "restaurant_rating": None
        }]
        
        response = client.post("/orders/order-1/feedback/restaurant", json={
            "rating": 5,
            "comment": "Great!"
        })
        assert response.status_code == 400
        assert "completed" in response.json()["detail"].lower()
    
    @patch("app.routers.feedback.get_db")
    def test_duplicate_feedback(self, mock_db, client, mock_customer):
        """Test cannot submit feedback twice"""
        mock_supabase = Mock()
        mock_db.return_value = mock_supabase
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [{
            "user_id": "customer-123",
            "status": "delivered",
            "restaurant_rating": 5
        }]
        
        response = client.post("/orders/order-1/feedback/restaurant", json={
            "rating": 4,
            "comment": "Changed mind"
        })
        assert response.status_code == 400
        assert "already submitted" in response.json()["detail"].lower()


class TestOrderFlowAuthorization:
    """Test authorization"""
    
    @patch("app.routers.orders.get_db")
    def test_customer_cannot_accept_order(self, mock_db, client, mock_customer):
        """Test customer cannot accept order"""
        mock_supabase = Mock()
        mock_db.return_value = mock_supabase
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [{"restaurant_id": "rest-1"}]
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = []
        
        response = client.patch("/orders/order-1/accept")
        assert response.status_code == 403
    
    @patch("app.routers.orders.get_db")
    def test_wrong_customer_access_order(self, mock_db, client, mock_customer):
        """Test customer cannot access other's order"""
        mock_supabase = Mock()
        mock_db.return_value = mock_supabase
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [{
            "id": "order-1",
            "user_id": "different-customer"
        }]
        
        response = client.get("/orders/order-1")
        assert response.status_code == 403
    
    @patch("app.routers.orders.get_db")
    def test_wrong_driver_deliver_order(self, mock_db, client, mock_driver):
        """Test driver cannot deliver other's order"""
        mock_supabase = Mock()
        mock_db.return_value = mock_supabase
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [{
            "id": "order-1",
            "delivery_user_id": "different-driver"
        }]
        
        response = client.patch("/orders/order-1/status", json={
            "status": "delivered",
            "delivery_code": "123456"
        })
        assert response.status_code == 403


class TestOrderFlowDataIntegrity:
    """Test data integrity"""
    
    @patch("app.routers.orders.get_db")
    def test_order_status_timeline(self, mock_db, client, mock_customer):
        """Test status timeline is recorded"""
        mock_supabase = Mock()
        mock_db.return_value = mock_supabase
        
        # Order belongs to customer
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [{"user_id": "customer-123"}]
        
        # Timeline events
        mock_supabase.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value.data = [
            {"status": "pending", "created_at": "2024-01-01T10:00:00"},
            {"status": "accepted", "created_at": "2024-01-01T10:05:00"},
            {"status": "delivered", "created_at": "2024-01-01T10:50:00"}
        ]
        
        response = client.get("/orders/order-1/status")
        assert response.status_code == 200
        timeline = response.json()["timeline"]
        assert len(timeline) == 3
        assert timeline[0]["status"] == "pending"
        assert timeline[-1]["status"] == "delivered"
