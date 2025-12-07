import pytest
from unittest.mock import Mock, patch
from fastapi import HTTPException
from app.routers.owner_orders import get_restaurant_orders, update_order_status, get_restaurant_analytics, UpdateOrderStatusRequest


@pytest.fixture
def mock_user():
    return {"id": "owner123"}


@pytest.fixture
def mock_orders():
    return [
        {
            "id": "order1",
            "user_id": "user1",
            "status": "pending",
            "total": 25.50,
            "created_at": "2024-01-01T10:00:00",
            "users": {"name": "John Doe"},
            "delivery_address": "123 Main St"
        }
    ]


@patch("app.routers.owner_orders.get_db")
def test_get_restaurant_orders_success(mock_get_db, mock_user, mock_orders):
    mock_supabase = Mock()
    mock_get_db.return_value = mock_supabase
    
    table1 = Mock()
    table1.select.return_value.eq.return_value.execute.return_value.data = [{"restaurant_id": "rest1"}]
    
    table2 = Mock()
    table2.select.return_value.eq.return_value.in_.return_value.order.return_value.execute.return_value.data = mock_orders
    
    table3 = Mock()
    table3.select.return_value.eq.return_value.execute.return_value.data = [{"meals": {"name": "Pizza"}, "qty": 2}]
    
    mock_supabase.table.side_effect = [table1, table2, table3]

    result = get_restaurant_orders(mock_user)

    assert len(result) == 1
    assert result[0]["id"] == "order1"
    assert result[0]["customer_name"] == "John Doe"


@patch("app.routers.owner_orders.get_db")
def test_get_restaurant_orders_no_restaurant(mock_get_db, mock_user):
    mock_supabase = Mock()
    mock_get_db.return_value = mock_supabase
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []

    with pytest.raises(HTTPException) as exc:
        get_restaurant_orders(mock_user)
    assert exc.value.status_code == 404


@patch("app.routers.owner_orders.get_db")
def test_update_order_status_success(mock_get_db, mock_user):
    mock_supabase = Mock()
    mock_get_db.return_value = mock_supabase
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [{"id": "order1", "restaurant_id": "rest1"}]
    mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = Mock()
    mock_supabase.table.return_value.insert.return_value.execute.return_value = Mock()

    request = UpdateOrderStatusRequest(status="ready")
    result = update_order_status("order1", request, mock_user)

    assert result["id"] == "order1"
    assert result["status"] == "ready"


@patch("app.routers.owner_orders.get_db")
def test_update_order_status_not_found(mock_get_db, mock_user):
    mock_supabase = Mock()
    mock_get_db.return_value = mock_supabase
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []

    request = UpdateOrderStatusRequest(status="ready")
    with pytest.raises(HTTPException) as exc:
        update_order_status("order1", request, mock_user)
    assert exc.value.status_code == 404


@patch("app.routers.owner_orders.get_db")
def test_get_restaurant_analytics_success(mock_get_db, mock_user):
    mock_supabase = Mock()
    mock_get_db.return_value = mock_supabase
    
    staff_mock = Mock()
    staff_mock.data = [{"restaurant_id": "rest1", "restaurants": {"name": "Test Restaurant"}}]
    
    orders_data = [
        {
            "id": "order1",
            "user_id": "user1",
            "total": 30.0,
            "restaurant_rating": 5,
            "restaurant_comment": "Great!",
            "created_at": "2024-01-01",
            "delivery_fee": 5.0,
            "tip_amount": 3.0,
            "tax": 2.0
        },
        {
            "id": "order2",
            "user_id": "user1",
            "total": 40.0,
            "restaurant_rating": 4,
            "restaurant_comment": "Good",
            "created_at": "2024-01-02",
            "delivery_fee": 5.0,
            "tip_amount": 4.0,
            "tax": 3.0
        }
    ]
    
    orders_mock = Mock()
    orders_mock.data = orders_data
    
    items_mock = Mock()
    items_mock.data = [{"meal_id": "meal1", "qty": 2, "price": 20.0, "meals": {"name": "Pizza", "image_link": "img.jpg"}, "order_id": "order1"}]
    
    reviews_data = [
        {"id": "order1", "restaurant_rating": 5, "restaurant_comment": "Great!", "created_at": "2024-01-01", "users": {"name": "John"}},
        {"id": "order2", "restaurant_rating": 4, "restaurant_comment": "Good", "created_at": "2024-01-02", "users": {"name": "Jane"}}
    ]
    reviews_mock = Mock()
    reviews_mock.data = reviews_data
    
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.side_effect = [staff_mock]
    mock_supabase.table.return_value.select.return_value.eq.return_value.in_.return_value.execute.return_value = orders_mock
    mock_supabase.table.return_value.select.return_value.in_.return_value.execute.return_value = items_mock
    mock_supabase.table.return_value.select.return_value.eq.return_value.not_.is_.return_value.order.return_value.limit.return_value.execute.return_value = reviews_mock

    result = get_restaurant_analytics(mock_user)

    assert result["restaurant"]["name"] == "Test Restaurant"
    assert result["restaurant"]["totalOrders"] == 2
    assert result["restaurant"]["averageRating"] == 4.5
    assert result["stats"]["totalRevenue"] == 48.0


@patch("app.routers.owner_orders.get_db")
def test_get_restaurant_analytics_no_restaurant(mock_get_db, mock_user):
    mock_supabase = Mock()
    mock_get_db.return_value = mock_supabase
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []

    with pytest.raises(HTTPException) as exc:
        get_restaurant_analytics(mock_user)
    assert exc.value.status_code == 404


@patch("app.routers.owner_orders.get_db")
def test_get_restaurant_analytics_no_orders(mock_get_db, mock_user):
    mock_supabase = Mock()
    mock_get_db.return_value = mock_supabase
    
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
        {"restaurant_id": "rest1", "restaurants": {"name": "Test Restaurant"}}
    ]
    mock_supabase.table.return_value.select.return_value.eq.return_value.in_.return_value.execute.return_value.data = []
    mock_supabase.table.return_value.select.return_value.in_.return_value.execute.return_value.data = []
    mock_supabase.table.return_value.select.return_value.eq.return_value.not_.is_.return_value.order.return_value.limit.return_value.execute.return_value.data = []

    result = get_restaurant_analytics(mock_user)

    assert result["restaurant"]["totalOrders"] == 0
    assert result["stats"]["totalRevenue"] == 0
    assert result["stats"]["avgOrderValue"] == 0
