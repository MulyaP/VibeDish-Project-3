import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException
from fastapi.testclient import TestClient
from app.owner_meals.auth import require_owner
from app.owner_meals import service
from app.owner_meals.schemas import MealCreate, MealUpdate
from app.main import app

client = TestClient(app)


@pytest.mark.asyncio
async def test_require_owner_success():
    mock_user = {'id': 'owner-123', 'email': 'owner@test.com'}
    mock_db = MagicMock()
    mock_table = MagicMock()
    mock_table.select.return_value = mock_table
    mock_table.eq.return_value = mock_table
    mock_table.execute.return_value = MagicMock(data=[{'role': 'owner'}])
    mock_db.table.return_value = mock_table
    
    result = await require_owner(mock_user, mock_db)
    assert result == mock_user


@pytest.mark.asyncio
async def test_require_owner_not_owner_role():
    mock_user = {'id': 'user-123', 'email': 'user@test.com'}
    mock_db = MagicMock()
    mock_table = MagicMock()
    mock_table.select.return_value = mock_table
    mock_table.eq.return_value = mock_table
    mock_table.execute.return_value = MagicMock(data=[{'role': 'customer'}])
    mock_db.table.return_value = mock_table
    
    with pytest.raises(HTTPException) as exc:
        await require_owner(mock_user, mock_db)
    assert exc.value.status_code == 403
    assert exc.value.detail == 'Owner role required'


@pytest.mark.asyncio
async def test_require_owner_user_not_found():
    mock_user = {'id': 'nonexistent-123', 'email': 'none@test.com'}
    mock_db = MagicMock()
    mock_table = MagicMock()
    mock_table.select.return_value = mock_table
    mock_table.eq.return_value = mock_table
    mock_table.execute.return_value = MagicMock(data=[])
    mock_db.table.return_value = mock_table
    
    with pytest.raises(HTTPException) as exc:
        await require_owner(mock_user, mock_db)
    assert exc.value.status_code == 403


def test_get_restaurant_by_owner_success():
    with patch('app.owner_meals.service.get_db') as mock_get_db:
        mock_db = MagicMock()
        mock_table = MagicMock()
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.execute.return_value = MagicMock(data=[{'id': 'rest-123'}])
        mock_db.table.return_value = mock_table
        mock_get_db.return_value = mock_db
        
        result = service.get_restaurant_by_owner('owner-123')
        assert result == 'rest-123'


def test_get_restaurant_by_owner_not_found():
    with patch('app.owner_meals.service.get_db') as mock_get_db:
        mock_db = MagicMock()
        mock_table = MagicMock()
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.execute.return_value = MagicMock(data=[])
        mock_db.table.return_value = mock_table
        mock_get_db.return_value = mock_db
        
        with pytest.raises(HTTPException) as exc:
            service.get_restaurant_by_owner('owner-123')
        assert exc.value.status_code == 404


def test_create_meal_success():
    with patch('app.owner_meals.service.get_db') as mock_get_db:
        mock_db = MagicMock()
        mock_table = MagicMock()
        mock_table.insert.return_value = mock_table
        mock_table.execute.return_value = MagicMock(data=[{
            'id': 'meal-123', 'restaurant_id': 'rest-123', 'name': 'Pizza',
            'tags': ['italian'], 'base_price': 10.0, 'quantity': 5,
            'surplus_price': 8.0, 'allergens': [], 'calories': 500, 'image_link': None
        }])
        mock_db.table.return_value = mock_table
        mock_get_db.return_value = mock_db
        
        meal = MealCreate(name='Pizza', base_price=10.0, tags=['italian'])
        result = service.create_meal('rest-123', meal)
        assert result['name'] == 'Pizza'


def test_update_meal_success():
    with patch('app.owner_meals.service.get_db') as mock_get_db:
        mock_db = MagicMock()
        mock_table = MagicMock()
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.update.return_value = mock_table
        mock_table.execute.side_effect = [
            MagicMock(data=[{'id': 'meal-123'}]),
            MagicMock(data=[{'id': 'meal-123', 'restaurant_id': 'rest-123', 'name': 'Updated Pizza', 'quantity': 10, 'tags': [], 'base_price': 10.0, 'surplus_price': None, 'allergens': [], 'calories': None, 'image_link': None}])
        ]
        mock_db.table.return_value = mock_table
        mock_get_db.return_value = mock_db
        
        meal = MealUpdate(name='Updated Pizza', quantity=10)
        result = service.update_meal('meal-123', 'rest-123', meal)
        assert result['name'] == 'Updated Pizza'


def test_update_meal_not_found():
    with patch('app.owner_meals.service.get_db') as mock_get_db:
        mock_db = MagicMock()
        mock_table = MagicMock()
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.execute.return_value = MagicMock(data=[])
        mock_db.table.return_value = mock_table
        mock_get_db.return_value = mock_db
        
        with pytest.raises(HTTPException) as exc:
            service.update_meal('meal-123', 'rest-123', MealUpdate(name='Test'))
        assert exc.value.status_code == 404


def test_update_meal_no_fields():
    with patch('app.owner_meals.service.get_db') as mock_get_db:
        mock_db = MagicMock()
        mock_table = MagicMock()
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.execute.return_value = MagicMock(data=[{'id': 'meal-123'}])
        mock_db.table.return_value = mock_table
        mock_get_db.return_value = mock_db
        
        with pytest.raises(HTTPException) as exc:
            service.update_meal('meal-123', 'rest-123', MealUpdate())
        assert exc.value.status_code == 400


def test_delete_meal_success():
    with patch('app.owner_meals.service.get_db') as mock_get_db:
        mock_db = MagicMock()
        mock_table = MagicMock()
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.execute.return_value = MagicMock(data=[{'id': 'meal-123'}])
        mock_table.delete.return_value = mock_table
        mock_db.table.return_value = mock_table
        mock_get_db.return_value = mock_db
        
        service.delete_meal('meal-123', 'rest-123')


def test_delete_meal_not_found():
    with patch('app.owner_meals.service.get_db') as mock_get_db:
        mock_db = MagicMock()
        mock_table = MagicMock()
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.execute.return_value = MagicMock(data=[])
        mock_db.table.return_value = mock_table
        mock_get_db.return_value = mock_db
        
        with pytest.raises(HTTPException) as exc:
            service.delete_meal('meal-123', 'rest-123')
        assert exc.value.status_code == 404


def test_get_restaurant_meals():
    with patch('app.owner_meals.service.get_db') as mock_get_db:
        mock_db = MagicMock()
        mock_table = MagicMock()
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.order.return_value = mock_table
        mock_table.execute.return_value = MagicMock(data=[
            {'id': 'meal-1', 'restaurant_id': 'rest-123', 'name': 'Pizza', 'tags': [], 'base_price': 10.0, 'quantity': 5, 'surplus_price': None, 'allergens': [], 'calories': None, 'image_link': None},
            {'id': 'meal-2', 'restaurant_id': 'rest-123', 'name': 'Burger', 'tags': [], 'base_price': 8.0, 'quantity': 3, 'surplus_price': None, 'allergens': [], 'calories': None, 'image_link': None}
        ])
        mock_db.table.return_value = mock_table
        mock_get_db.return_value = mock_db
        
        result = service.get_restaurant_meals('rest-123')
        assert len(result) == 2
        assert result[0]['name'] == 'Pizza'


@pytest.mark.asyncio
async def test_router_add_meal():
    from app.owner_meals.router import add_meal
    with patch('app.owner_meals.service.get_restaurant_by_owner') as mock_get_rest, \
         patch('app.owner_meals.service.create_meal') as mock_create:
        mock_get_rest.return_value = 'rest-123'
        mock_create.return_value = {'id': 'meal-123', 'restaurant_id': 'rest-123', 'name': 'Pizza', 'tags': [], 'base_price': 10.0, 'quantity': 5, 'surplus_price': None, 'allergens': [], 'calories': None, 'image_link': None}
        
        meal = MealCreate(name='Pizza', base_price=10.0)
        user = {'id': 'owner-123', 'email': 'owner@test.com'}
        result = await add_meal(meal, user)
        assert result['name'] == 'Pizza'


@pytest.mark.asyncio
async def test_router_modify_meal():
    from app.owner_meals.router import modify_meal
    with patch('app.owner_meals.service.get_restaurant_by_owner') as mock_get_rest, \
         patch('app.owner_meals.service.update_meal') as mock_update:
        mock_get_rest.return_value = 'rest-123'
        mock_update.return_value = {'id': 'meal-123', 'restaurant_id': 'rest-123', 'name': 'Updated', 'tags': [], 'base_price': 12.0, 'quantity': 10, 'surplus_price': None, 'allergens': [], 'calories': None, 'image_link': None}
        
        meal = MealUpdate(name='Updated')
        user = {'id': 'owner-123', 'email': 'owner@test.com'}
        result = await modify_meal('meal-123', meal, user)
        assert result['name'] == 'Updated'


@pytest.mark.asyncio
async def test_router_remove_meal():
    from app.owner_meals.router import remove_meal
    with patch('app.owner_meals.service.get_restaurant_by_owner') as mock_get_rest, \
         patch('app.owner_meals.service.delete_meal') as mock_delete:
        mock_get_rest.return_value = 'rest-123'
        mock_delete.return_value = None
        
        user = {'id': 'owner-123', 'email': 'owner@test.com'}
        await remove_meal('meal-123', user)
        mock_delete.assert_called_once_with('meal-123', 'rest-123')


@pytest.mark.asyncio
async def test_router_list_my_meals():
    from app.owner_meals.router import list_my_meals
    with patch('app.owner_meals.service.get_restaurant_by_owner') as mock_get_rest, \
         patch('app.owner_meals.service.get_restaurant_meals') as mock_get_meals:
        mock_get_rest.return_value = 'rest-123'
        mock_get_meals.return_value = [{'id': 'meal-1', 'restaurant_id': 'rest-123', 'name': 'Pizza', 'tags': [], 'base_price': 10.0, 'quantity': 5, 'surplus_price': None, 'allergens': [], 'calories': None, 'image_link': None}]
        
        user = {'id': 'owner-123', 'email': 'owner@test.com'}
        result = await list_my_meals(user)
        assert len(result) == 1
        assert result[0]['name'] == 'Pizza'
