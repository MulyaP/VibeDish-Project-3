import pytest
from unittest.mock import Mock, patch
from fastapi import HTTPException
from app.routers.feedback import submit_restaurant_feedback, submit_driver_feedback, get_order_feedback, FeedbackRequest


@pytest.fixture
def mock_user():
    return {"id": "user123"}


@pytest.fixture
def feedback_request():
    return FeedbackRequest(rating=5, comment="Great service!")


@patch("app.routers.feedback.get_db")
def test_submit_restaurant_feedback_success(mock_get_db, mock_user, feedback_request):
    mock_supabase = Mock()
    mock_get_db.return_value = mock_supabase
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
        {"user_id": "user123", "status": "delivered", "restaurant_rating": None}
    ]
    mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = Mock()

    result = submit_restaurant_feedback("order123", feedback_request, mock_user)

    assert result["message"] == "Restaurant feedback submitted"
    assert result["rating"] == 5


@patch("app.routers.feedback.get_db")
def test_submit_restaurant_feedback_order_not_found(mock_get_db, mock_user, feedback_request):
    mock_supabase = Mock()
    mock_get_db.return_value = mock_supabase
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []

    with pytest.raises(HTTPException) as exc:
        submit_restaurant_feedback("order123", feedback_request, mock_user)
    assert exc.value.status_code == 404


@patch("app.routers.feedback.get_db")
def test_submit_restaurant_feedback_not_your_order(mock_get_db, mock_user, feedback_request):
    mock_supabase = Mock()
    mock_get_db.return_value = mock_supabase
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
        {"user_id": "other_user", "status": "delivered", "restaurant_rating": None}
    ]

    with pytest.raises(HTTPException) as exc:
        submit_restaurant_feedback("order123", feedback_request, mock_user)
    assert exc.value.status_code == 403


@patch("app.routers.feedback.get_db")
def test_submit_restaurant_feedback_order_not_completed(mock_get_db, mock_user, feedback_request):
    mock_supabase = Mock()
    mock_get_db.return_value = mock_supabase
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
        {"user_id": "user123", "status": "pending", "restaurant_rating": None}
    ]

    with pytest.raises(HTTPException) as exc:
        submit_restaurant_feedback("order123", feedback_request, mock_user)
    assert exc.value.status_code == 400


@patch("app.routers.feedback.get_db")
def test_submit_restaurant_feedback_already_submitted(mock_get_db, mock_user, feedback_request):
    mock_supabase = Mock()
    mock_get_db.return_value = mock_supabase
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
        {"user_id": "user123", "status": "delivered", "restaurant_rating": 4}
    ]

    with pytest.raises(HTTPException) as exc:
        submit_restaurant_feedback("order123", feedback_request, mock_user)
    assert exc.value.status_code == 400


@patch("app.routers.feedback.get_db")
def test_submit_driver_feedback_success(mock_get_db, mock_user, feedback_request):
    mock_supabase = Mock()
    mock_get_db.return_value = mock_supabase
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
        {"user_id": "user123", "status": "delivered", "driver_rating": None}
    ]
    mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = Mock()

    result = submit_driver_feedback("order123", feedback_request, mock_user)

    assert result["message"] == "Driver feedback submitted"
    assert result["rating"] == 5


@patch("app.routers.feedback.get_db")
def test_submit_driver_feedback_already_submitted(mock_get_db, mock_user, feedback_request):
    mock_supabase = Mock()
    mock_get_db.return_value = mock_supabase
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
        {"user_id": "user123", "status": "delivered", "driver_rating": 3}
    ]

    with pytest.raises(HTTPException) as exc:
        submit_driver_feedback("order123", feedback_request, mock_user)
    assert exc.value.status_code == 400


@patch("app.routers.feedback.get_db")
def test_get_order_feedback_both_ratings(mock_get_db, mock_user):
    mock_supabase = Mock()
    mock_get_db.return_value = mock_supabase
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
        {
            "user_id": "user123",
            "restaurant_rating": 5,
            "restaurant_comment": "Great food",
            "driver_rating": 4,
            "driver_comment": "Fast delivery"
        }
    ]

    result = get_order_feedback("order123", mock_user)

    assert result["restaurant_feedback"]["rating"] == 5
    assert result["restaurant_feedback"]["comment"] == "Great food"
    assert result["driver_feedback"]["rating"] == 4
    assert result["driver_feedback"]["comment"] == "Fast delivery"


@patch("app.routers.feedback.get_db")
def test_get_order_feedback_no_ratings(mock_get_db, mock_user):
    mock_supabase = Mock()
    mock_get_db.return_value = mock_supabase
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
        {"user_id": "user123", "restaurant_rating": None, "driver_rating": None}
    ]

    result = get_order_feedback("order123", mock_user)

    assert result == {}


@patch("app.routers.feedback.get_db")
def test_get_order_feedback_order_not_found(mock_get_db, mock_user):
    mock_supabase = Mock()
    mock_get_db.return_value = mock_supabase
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []

    with pytest.raises(HTTPException) as exc:
        get_order_feedback("order123", mock_user)
    assert exc.value.status_code == 404
