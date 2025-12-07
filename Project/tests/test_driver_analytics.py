import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timezone, timedelta
from app.routers.driver_analytics import get_driver_analytics


@pytest.fixture
def mock_user():
    return {"id": "driver123", "email": "driver@test.com"}


@pytest.fixture
def mock_orders():
    return [
        {
            "id": "order1",
            "restaurant_id": "rest1",
            "delivery_fee": 5.0,
            "tip_amount": 3.0,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "restaurants": {"name": "Restaurant A"},
            "customer": {"name": "Customer 1"}
        },
        {
            "id": "order2",
            "restaurant_id": "rest1",
            "delivery_fee": 6.0,
            "tip_amount": 4.0,
            "created_at": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(),
            "restaurants": {"name": "Restaurant A"},
            "customer": {"name": "Customer 2"}
        },
        {
            "id": "order3",
            "restaurant_id": "rest2",
            "delivery_fee": 7.0,
            "tip_amount": 2.0,
            "created_at": (datetime.now(timezone.utc) - timedelta(days=2)).isoformat(),
            "restaurants": {"name": "Restaurant B"},
            "customer": {"name": "Customer 3"}
        }
    ]


@patch("app.routers.driver_analytics.get_db")
def test_get_driver_analytics_with_orders(mock_get_db, mock_user, mock_orders):
    mock_supabase = Mock()
    mock_get_db.return_value = mock_supabase
    mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = mock_orders

    result = get_driver_analytics(user=mock_user)

    assert result["stats"]["totalDeliveries"] == 3
    assert result["stats"]["totalEarnings"] == 27.0
    assert result["stats"]["totalTips"] == 9.0
    assert result["stats"]["totalDeliveryFees"] == 18.0
    assert result["stats"]["avgEarningsPerDelivery"] == 9.0
    assert len(result["topRestaurants"]) == 2
    assert result["topRestaurants"][0]["deliveries"] == 2
    assert len(result["recentDeliveries"]) == 3
    assert len(result["earningsByDay"]) == 7


@patch("app.routers.driver_analytics.get_db")
def test_get_driver_analytics_no_orders(mock_get_db, mock_user):
    mock_supabase = Mock()
    mock_get_db.return_value = mock_supabase
    mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = []

    result = get_driver_analytics(user=mock_user)

    assert result["stats"]["totalDeliveries"] == 0
    assert result["stats"]["totalEarnings"] == 0
    assert result["stats"]["avgEarningsPerDelivery"] == 0
    assert result["topRestaurants"] == []
    assert result["recentDeliveries"] == []
    assert result["earningsByDay"] == []


@patch("app.routers.driver_analytics.get_db")
def test_top_restaurants_sorted_by_deliveries(mock_get_db, mock_user, mock_orders):
    mock_supabase = Mock()
    mock_get_db.return_value = mock_supabase
    mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = mock_orders

    result = get_driver_analytics(user=mock_user)

    assert result["topRestaurants"][0]["name"] == "Restaurant A"
    assert result["topRestaurants"][0]["deliveries"] == 2
    assert result["topRestaurants"][1]["name"] == "Restaurant B"
    assert result["topRestaurants"][1]["deliveries"] == 1


@patch("app.routers.driver_analytics.get_db")
def test_recent_deliveries_sorted_by_date(mock_get_db, mock_user, mock_orders):
    mock_supabase = Mock()
    mock_get_db.return_value = mock_supabase
    mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = mock_orders

    result = get_driver_analytics(user=mock_user)

    assert result["recentDeliveries"][0]["id"] == "order1"
    assert result["recentDeliveries"][1]["id"] == "order2"
    assert result["recentDeliveries"][2]["id"] == "order3"


@patch("app.routers.driver_analytics.get_db")
def test_earnings_by_day_structure(mock_get_db, mock_user, mock_orders):
    mock_supabase = Mock()
    mock_get_db.return_value = mock_supabase
    mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = mock_orders

    result = get_driver_analytics(user=mock_user)

    assert len(result["earningsByDay"]) == 7
    for day in result["earningsByDay"]:
        assert "date" in day
        assert "day" in day
        assert "earnings" in day
        assert "deliveries" in day


@patch("app.routers.driver_analytics.get_db")
def test_handles_null_fees_and_tips(mock_get_db, mock_user):
    orders_with_nulls = [
        {
            "id": "order1",
            "restaurant_id": "rest1",
            "delivery_fee": None,
            "tip_amount": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "restaurants": {"name": "Restaurant A"},
            "customer": {"name": "Customer 1"}
        }
    ]
    mock_supabase = Mock()
    mock_get_db.return_value = mock_supabase
    mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = orders_with_nulls

    result = get_driver_analytics(user=mock_user)

    assert result["stats"]["totalEarnings"] == 0
    assert result["stats"]["totalTips"] == 0
    assert result["stats"]["totalDeliveryFees"] == 0
