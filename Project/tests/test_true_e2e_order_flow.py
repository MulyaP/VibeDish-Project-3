"""
TRUE End-to-End Integration Tests

Tests complete order flow with real data flowing through all components:
Cart → Checkout → Restaurant Accept → Driver Pickup → Delivery → Feedback
"""

import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from app.main import app
from app.auth import current_user

# Real user IDs that will flow through the system
CUSTOMER_ID = "e2e-customer-123"
RESTAURANT_ID = "e2e-restaurant-456"
STAFF_ID = "e2e-staff-789"
DRIVER_ID = "e2e-driver-101"
MEAL_ID = "e2e-meal-001"
ORDER_ID = None  # Will be set during flow


@pytest.fixture
def shared_supabase_mock():
    """Single shared mock that maintains state across the entire flow"""
    mock = Mock()
    
    # Shared state that persists across calls
    state = {
        "cart_id": "e2e-cart-001",
        "cart_items": [],
        "orders": {},
        "order_status_events": {},
        "meals": {
            MEAL_ID: {"id": MEAL_ID, "restaurant_id": RESTAURANT_ID, "quantity": 10, "surplus_price": 9.99, "base_price": 15.99}
        },
        "restaurants": {
            RESTAURANT_ID: {"id": RESTAURANT_ID, "name": "E2E Restaurant", "latitude": 40.7128, "longitude": -74.0060}
        },
        "staff": {STAFF_ID: {"user_id": STAFF_ID, "restaurant_id": RESTAURANT_ID}},
        "feedbacks": {}
    }
    
    def table_mock(table_name):
        table = Mock()
        
        def select_mock(*args):
            chain = Mock()
            
            def eq_mock(field, value):
                eq_chain = Mock()
                
                def execute_mock():
                    result = Mock()
                    
                    # Cart operations
                    if table_name == "carts" and field == "user_id":
                        result.data = [{"id": state["cart_id"], "user_id": value}]
                    
                    # Cart items
                    elif table_name == "cart_items" and field == "cart_id":
                        items_with_meals = []
                        for item in state["cart_items"]:
                            if item["cart_id"] == value:
                                item_copy = item.copy()
                                item_copy["meals"] = state["meals"].get(item["meal_id"], {})
                                items_with_meals.append(item_copy)
                        result.data = items_with_meals
                    
                    # Meals
                    elif table_name == "meals" and field == "id":
                        result.data = [state["meals"].get(value)] if value in state["meals"] else []
                    
                    # Orders
                    elif table_name == "orders" and field == "id":
                        order = state["orders"].get(value)
                        if order:
                            order_copy = order.copy()
                            order_copy["restaurants"] = state["restaurants"].get(order["restaurant_id"], {})
                            result.data = [order_copy]
                        else:
                            result.data = []
                    
                    elif table_name == "orders" and field == "user_id":
                        user_orders = [o for o in state["orders"].values() if o["user_id"] == value]
                        for order in user_orders:
                            order["restaurants"] = state["restaurants"].get(order["restaurant_id"], {})
                        result.data = user_orders
                    
                    elif table_name == "orders" and field == "delivery_user_id":
                        driver_orders = [o for o in state["orders"].values() if o.get("delivery_user_id") == value]
                        result.data = driver_orders
                    
                    # Restaurant staff
                    elif table_name == "restaurant_staff":
                        result.data = [state["staff"].get(value)] if value in state["staff"] else []
                    
                    # Order status events
                    elif table_name == "order_status_events" and field == "order_id":
                        events = state["order_status_events"].get(value, [])
                        
                        # Handle order() chaining
                        order_chain = Mock()
                        order_chain.execute.return_value.data = events
                        eq_chain.order = Mock(return_value=order_chain)
                        
                        result.data = events
                    
                    else:
                        result.data = []
                    
                    return result
                
                eq_chain.execute = execute_mock
                
                # Support double eq() for cart_items lookup
                def eq2_mock(field2, value2):
                    eq2_chain = Mock()
                    
                    def execute2_mock():
                        result = Mock()
                        if table_name == "cart_items":
                            result.data = [item for item in state["cart_items"] 
                                         if item.get(field) == value and item.get(field2) == value2]
                        else:
                            result.data = []
                        return result
                    
                    eq2_chain.execute = execute2_mock
                    return eq2_chain
                
                eq_chain.eq = eq2_mock
                return eq_chain
            
            chain.eq = eq_mock
            return chain
        
        def insert_mock(data):
            insert_chain = Mock()
            
            def execute_mock():
                result = Mock()
                
                if table_name == "cart_items":
                    state["cart_items"].append(data)
                    result.data = [data]
                
                elif table_name == "orders":
                    global ORDER_ID
                    ORDER_ID = data.get("id", f"order-{len(state['orders']) + 1}")
                    data["id"] = ORDER_ID
                    state["orders"][ORDER_ID] = data
                    result.data = [data]
                
                elif table_name == "order_status_events":
                    order_id = data["order_id"]
                    if order_id not in state["order_status_events"]:
                        state["order_status_events"][order_id] = []
                    state["order_status_events"][order_id].append(data)
                    result.data = [data]
                
                else:
                    result.data = [data]
                
                return result
            
            insert_chain.execute = execute_mock
            return insert_chain
        
        def update_mock(data):
            update_chain = Mock()
            
            def eq_mock(field, value):
                eq_chain = Mock()
                
                def execute_mock():
                    result = Mock()
                    
                    if table_name == "meals" and field == "id":
                        if value in state["meals"]:
                            state["meals"][value].update(data)
                    
                    elif table_name == "orders" and field == "id":
                        if value in state["orders"]:
                            state["orders"][value].update(data)
                    
                    result.data = [data]
                    return result
                
                eq_chain.execute = execute_mock
                return eq_chain
            
            update_chain.eq = eq_mock
            return update_chain
        
        def delete_mock():
            delete_chain = Mock()
            
            def eq_mock(field, value):
                eq_chain = Mock()
                
                def execute_mock():
                    result = Mock()
                    if table_name == "cart_items" and field == "cart_id":
                        state["cart_items"] = [item for item in state["cart_items"] if item["cart_id"] != value]
                    result.data = []
                    return result
                
                eq_chain.execute = execute_mock
                return eq_chain
            
            delete_chain.eq = eq_mock
            return delete_chain
        
        table.select = select_mock
        table.insert = insert_mock
        table.update = update_mock
        table.delete = delete_mock
        
        return table
    
    mock.table = table_mock
    return mock


class TestTrueE2EOrderFlow:
    """TRUE end-to-end test with data flowing through entire system"""
    
    @patch("app.routers.cart.get_db")
    @patch("app.routers.orders.get_db")
    @patch("app.routers.delivery_routes.get_db")
    @patch("app.routers.feedback.get_db")
    @patch("requests.get")
    def test_complete_order_lifecycle(self, mock_requests, mock_feedback_db, mock_delivery_db, 
                                      mock_orders_db, mock_cart_db, shared_supabase_mock):
        """
        Complete order flow:
        1. Customer adds item to cart
        2. Customer checks out → creates order
        3. Restaurant staff accepts order
        4. Restaurant staff marks preparing
        5. Restaurant staff marks ready
        6. Driver accepts delivery
        7. Driver delivers with code
        8. Customer submits feedback
        
        Data flows through all steps - order ID from step 2 is used in steps 3-8
        """
        # Setup all routers to use same mock
        mock_cart_db.return_value = shared_supabase_mock
        mock_orders_db.return_value = shared_supabase_mock
        mock_delivery_db.return_value = shared_supabase_mock
        mock_feedback_db.return_value = shared_supabase_mock
        
        # Mock Mapbox
        mock_requests.return_value.json.return_value = {"routes": [{"distance": 3218, "duration": 600}]}
        mock_requests.return_value.raise_for_status = Mock()
        
        client = TestClient(app)
        
        # STEP 1: Customer adds item to cart
        app.dependency_overrides[current_user] = lambda: {"id": CUSTOMER_ID, "email": "customer@test.com"}
        
        response = client.post("/cart/items", json={"meal_id": MEAL_ID, "qty": 2})
        assert response.status_code == 200, f"Add to cart failed: {response.json()}"
        
        # Verify cart has item
        response = client.get("/cart")
        assert response.status_code == 200
        cart_data = response.json()
        assert len(cart_data["items"]) == 1
        assert cart_data["items"][0]["meal_id"] == MEAL_ID
        assert cart_data["items"][0]["qty"] == 2
        
        # STEP 2: Customer checks out → creates order
        response = client.post("/cart/checkout", json={
            "delivery_address": "123 Customer St",
            "latitude": 40.7580,
            "longitude": -73.9855,
            "tax": 2.50,
            "tip_amount": 3.00,
            "total": 25.48,
            "delivery_fee": 3.99
        })
        assert response.status_code == 200, f"Checkout failed: {response.json()}"
        
        order_id = response.json()["order_id"]
        assert order_id is not None, "Order ID not returned from checkout"
        
        # Verify cart is cleared
        response = client.get("/cart")
        cart_data = response.json()
        assert len(cart_data["items"]) == 0, "Cart should be empty after checkout"
        
        # Verify order exists
        response = client.get(f"/orders/{order_id}")
        assert response.status_code == 200
        order_data = response.json()
        assert order_data["order"]["status"] == "pending"
        assert len(order_data["items"]) == 1
        
        # STEP 3: Restaurant staff accepts order (using SAME order_id)
        app.dependency_overrides[current_user] = lambda: {"id": STAFF_ID, "email": "staff@test.com"}
        
        response = client.patch(f"/orders/{order_id}/accept")
        assert response.status_code == 200, f"Accept failed: {response.json()}"
        assert response.json()["status"] == "accepted"
        
        # STEP 4: Restaurant marks preparing (using SAME order_id)
        response = client.patch(f"/orders/{order_id}/preparing")
        assert response.status_code == 200
        assert response.json()["status"] == "preparing"
        
        # STEP 5: Restaurant marks ready (using SAME order_id)
        response = client.patch(f"/orders/{order_id}/ready")
        assert response.status_code == 200
        assert response.json()["status"] == "ready"
        
        # STEP 6: Driver accepts delivery (using SAME order_id)
        app.dependency_overrides[current_user] = lambda: {"id": DRIVER_ID, "email": "driver@test.com"}
        
        response = client.patch(f"/deliveries/{order_id}/accept")
        assert response.status_code == 200
        accepted_order = response.json()
        assert accepted_order["status"] == "assigned"
        assert accepted_order["delivery_user_id"] == DRIVER_ID
        delivery_code = accepted_order["delivery_code"]
        assert delivery_code is not None
        
        # STEP 7: Driver delivers with code (using SAME order_id and delivery_code from step 6)
        response = client.patch(f"/orders/{order_id}/status", json={
            "status": "delivered",
            "delivery_code": delivery_code
        })
        assert response.status_code == 200
        assert response.json()["status"] == "delivered"
        
        # STEP 8: Customer submits feedback (using SAME order_id)
        app.dependency_overrides[current_user] = lambda: {"id": CUSTOMER_ID, "email": "customer@test.com"}
        
        response = client.post(f"/orders/{order_id}/feedback/restaurant", json={
            "rating": 5,
            "comment": "Great food!"
        })
        assert response.status_code == 200
        
        response = client.post(f"/orders/{order_id}/feedback/driver", json={
            "rating": 5,
            "comment": "Fast delivery!"
        })
        assert response.status_code == 200
        
        # VERIFY: Check complete order timeline (using SAME order_id)
        response = client.get(f"/orders/{order_id}/status")
        assert response.status_code == 200
        timeline = response.json()["timeline"]
        
        # Verify all status transitions were recorded
        statuses = [event["status"] for event in timeline]
        assert "pending" in statuses
        assert "accepted" in statuses
        assert "preparing" in statuses
        assert "ready" in statuses
        assert "assigned" in statuses
        assert "delivered" in statuses
        
        app.dependency_overrides.clear()
        
        print(f"\n✅ TRUE E2E TEST PASSED!")
        print(f"   Order {order_id} completed full lifecycle:")
        print(f"   Cart → Checkout → Accept → Prepare → Ready → Assigned → Delivered → Feedback")
        print(f"   Timeline: {' → '.join(statuses)}")
