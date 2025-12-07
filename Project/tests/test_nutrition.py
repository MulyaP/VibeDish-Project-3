import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.nutrition_service import NutritionService


class TestNutritionService:
    """Test cases for NutritionService"""

    @pytest.fixture
    def nutrition_service(self):
        """Create a NutritionService instance"""
        service = NutritionService()
        service.client_id = "test_client_id"
        service.client_secret = "test_client_secret"
        return service

    @pytest.mark.asyncio
    async def test_get_access_token_success(self, nutrition_service):
        """Test successful OAuth token retrieval"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"access_token": "test_token_123"}
        
        with patch('app.services.nutrition_service.httpx.AsyncClient') as mock_client:
            mock_instance = MagicMock()
            mock_instance.post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value = mock_instance
            token = await nutrition_service._get_access_token()
            
            assert token == "test_token_123"

    @pytest.mark.asyncio
    async def test_get_access_token_failure(self, nutrition_service):
        """Test failed OAuth token retrieval"""
        mock_response = MagicMock()
        mock_response.status_code = 401
        
        with patch('app.services.nutrition_service.httpx.AsyncClient') as mock_client:
            mock_instance = MagicMock()
            mock_instance.post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value = mock_instance
            token = await nutrition_service._get_access_token()
            
            assert token is None

    @pytest.mark.asyncio
    async def test_get_nutrition_data_with_api_success(self, nutrition_service):
        """Test successful nutrition data retrieval from FatSecret API"""
        mock_token_response = MagicMock()
        mock_token_response.status_code = 200
        mock_token_response.json.return_value = {"access_token": "test_token"}
        
        mock_nutrition_response = MagicMock()
        mock_nutrition_response.status_code = 200
        mock_nutrition_response.json.return_value = {
            "foods": {
                "food": {
                    "food_id": "123",
                    "food_name": "Chicken Breast",
                    "food_description": "Per 100g - Calories: 165kcal | Fat: 3.6g | Carbs: 0g | Protein: 31g",
                    "food_url": "https://fatsecret.com/chicken",
                    "food_type": "Generic"
                }
            }
        }
        
        with patch('app.services.nutrition_service.httpx.AsyncClient') as mock_client:
            mock_instance = MagicMock()
            mock_instance.post = AsyncMock(
                side_effect=[mock_token_response, mock_nutrition_response]
            )
            mock_client.return_value.__aenter__.return_value = mock_instance
            
            result = await nutrition_service.get_nutrition_data("Chicken Breast")
            
            assert result["meal_name"] == "Chicken Breast"
            assert result["calories"] == 165
            assert result["protein_g"] == 31.0
            assert result["carbs_g"] == 0.0
            assert result["fat_g"] == 3.6
            assert result["source"] == "fatsecret_api"

    @pytest.mark.asyncio
    async def test_get_nutrition_data_fallback_to_estimates(self, nutrition_service):
        """Test fallback to estimates when API fails"""
        with patch.object(nutrition_service, '_get_access_token', return_value=None):
            result = await nutrition_service.get_nutrition_data("Chicken Salad")
            
            assert result["source"] == "estimate"
            assert result["calories"] > 0
            assert "chicken" in result["meal_name"].lower()

    @pytest.mark.asyncio
    async def test_get_nutrition_data_with_wrap_variation(self, nutrition_service):
        """Test search variations for wraps"""
        mock_token_response = MagicMock()
        mock_token_response.status_code = 200
        mock_token_response.json.return_value = {"access_token": "test_token"}
        
        mock_empty_response = MagicMock()
        mock_empty_response.status_code = 200
        mock_empty_response.json.return_value = {"foods": {}}
        
        mock_nutrition_response = MagicMock()
        mock_nutrition_response.status_code = 200
        mock_nutrition_response.json.return_value = {
            "foods": {
                "food": {
                    "food_name": "Buffalo Chicken",
                    "food_description": "Per 100g - Calories: 200kcal | Fat: 10g | Carbs: 5g | Protein: 25g",
                    "food_url": "https://fatsecret.com/buffalo-chicken",
                    "food_type": "Generic"
                }
            }
        }
        
        with patch('app.services.nutrition_service.httpx.AsyncClient') as mock_client:
            mock_instance = MagicMock()
            mock_instance.post = AsyncMock(
                side_effect=[mock_token_response, mock_empty_response, mock_nutrition_response]
            )
            mock_client.return_value.__aenter__.return_value = mock_instance
            
            result = await nutrition_service.get_nutrition_data("Buffalo Chicken Wrap")
            
            assert result["calories"] == 200

    def test_format_nutrition_data(self, nutrition_service):
        """Test nutrition data formatting"""
        food_data = {
            "food_name": "Test Food",
            "food_description": "Per 142g - Calories: 489kcal | Fat: 28.72g | Carbs: 37.13g | Protein: 19.98g",
            "food_url": "https://test.com",
            "food_type": "Generic"
        }
        
        result = nutrition_service._format_nutrition_data(food_data, "Test Meal")
        
        assert result["meal_name"] == "Test Meal"
        assert result["serving_size"] == "142g"
        assert result["calories"] == 489
        assert result["fat_g"] == 28.7
        assert result["carbs_g"] == 37.1
        assert result["protein_g"] == 20.0



    def test_get_estimated_nutrition_chicken(self, nutrition_service):
        """Test estimated nutrition for chicken dishes"""
        result = nutrition_service._get_estimated_nutrition("Grilled Chicken")
        
        assert result["meal_name"] == "Grilled Chicken"
        assert result["calories"] == 280
        assert result["protein_g"] == 35.0

    def test_get_estimated_nutrition_salad(self, nutrition_service):
        """Test estimated nutrition for salad dishes"""
        result = nutrition_service._get_estimated_nutrition("Caesar Salad")
        
        assert result["meal_name"] == "Caesar Salad"
        assert result["calories"] == 150

    def test_get_estimated_nutrition_pasta(self, nutrition_service):
        """Test estimated nutrition for pasta dishes"""
        result = nutrition_service._get_estimated_nutrition("Pasta Primavera")
        
        assert result["meal_name"] == "Pasta Primavera"
        assert result["calories"] == 320
        assert result["carbs_g"] == 58.0

    def test_get_estimated_nutrition_generic(self, nutrition_service):
        """Test estimated nutrition for generic dishes"""
        result = nutrition_service._get_estimated_nutrition("Mystery Meal")
        
        assert result["meal_name"] == "Mystery Meal"
        assert result["calories"] == 250
        assert result["protein_g"] == 15.0


class TestNutritionEndpoint:
    """Test cases for nutrition API endpoint"""

    @pytest.mark.asyncio
    async def test_nutrition_endpoint_success(self):
        """Test successful nutrition endpoint call"""
        from fastapi.testclient import TestClient
        from app.main import app
        
        client = TestClient(app)
        
        # Mock the database and nutrition service
        with patch('app.routers.catalog.get_db') as mock_db, \
             patch('app.services.nutrition_service.NutritionService.get_nutrition_data') as mock_nutrition:
            
            mock_supabase = MagicMock()
            mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
                {"name": "Test Meal"}
            ]
            mock_db.return_value = mock_supabase
            
            mock_nutrition.return_value = {
                "meal_name": "Test Meal",
                "calories": 300,
                "protein_g": 20.0,
                "carbs_g": 30.0,
                "fat_g": 10.0,
                "source": "fatsecret_api"
            }
            
            response = client.get("/catalog/meals/test-meal-id/nutrition")
            
            assert response.status_code == 200
            data = response.json()
            assert data["meal_name"] == "Test Meal"
            assert data["calories"] == 300
            assert data["source"] == "fatsecret_api"

    @pytest.mark.asyncio
    async def test_nutrition_endpoint_meal_not_found(self):
        """Test nutrition endpoint with non-existent meal"""
        from fastapi.testclient import TestClient
        from app.main import app
        
        client = TestClient(app)
        
        with patch('app.routers.catalog.get_db') as mock_db:
            mock_supabase = MagicMock()
            mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
            mock_db.return_value = mock_supabase
            
            response = client.get("/catalog/meals/non-existent-id/nutrition")
            
            assert response.status_code == 200
            data = response.json()
            assert "error" in data
