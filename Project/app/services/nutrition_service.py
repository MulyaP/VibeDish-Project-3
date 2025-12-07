import httpx
import base64
from typing import Dict
from ..config import settings

class NutritionService:
    def __init__(self):
        self.token_url = "https://oauth.fatsecret.com/connect/token"
        self.api_url = "https://platform.fatsecret.com/rest/server.api"
        self.client_id = settings.FATSECRET_CLIENT_ID
        self.client_secret = settings.FATSECRET_CLIENT_SECRET
        self._access_token = None
    
    async def _get_access_token(self) -> str:
        """Get OAuth2 access token for FatSecret API"""
        if not self.client_id or not self.client_secret:
            return None
        
        auth = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.token_url,
                headers={"Authorization": f"Basic {auth}"},
                data={"grant_type": "client_credentials", "scope": "basic"},
                timeout=10.0
            )
            if response.status_code == 200:
                return response.json().get("access_token")
        return None
    
    async def get_nutrition_data(self, food_name: str) -> Dict:
        """Get nutrition data from FatSecret API"""
        token = await self._get_access_token()
        if not token:
            result = self._get_estimated_nutrition(food_name)
            result["source"] = "estimate"
            result["source_message"] = "Failed to get API token"
            return result
        
        # Try multiple search variations
        search_terms = [
            food_name,
            food_name.replace(" wrap", ""),  # "Buffalo Chicken Wrap" -> "Buffalo Chicken"
            food_name.replace(" sandwich", ""),
            food_name.replace(" burger", ""),
        ]
        
        for search_term in search_terms:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        self.api_url,
                        headers={"Authorization": f"Bearer {token}"},
                        data={
                            "method": "foods.search",
                            "search_expression": search_term,
                            "format": "json",
                            "max_results": "1"
                        },
                        timeout=10.0
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        foods = data.get("foods", {}).get("food", [])
                        if foods:
                            food = foods[0] if isinstance(foods, list) else foods
                            result = self._format_nutrition_data(food, food_name)
                            result["source"] = "fatsecret_api"
                            result["source_message"] = f"Matched: {food.get('food_name', food_name)}"
                            result["food_url"] = food.get("food_url")
                            result["food_type"] = food.get("food_type")
                            return result
            except Exception:
                continue
        
        result = self._get_estimated_nutrition(food_name)
        result["source"] = "estimate"
        result["source_message"] = "No API match found"
        return result
    
    def _format_nutrition_data(self, food: Dict, meal_name: str) -> Dict:
        """Format FatSecret API response"""
        import re
        
        description = food.get("food_description", "")
        nutrients = {}
        serving_size = None
        
        if description:
            # Extract serving size (e.g., "Per 142g")
            serving_match = re.search(r'Per ([0-9.]+[a-z]+)', description, re.IGNORECASE)
            if serving_match:
                serving_size = serving_match.group(1)
            
            # Parse format: "Per 142g - Calories: 489kcal | Fat: 28.72g | Carbs: 37.13g | Protein: 19.98g"
            # Split by | and extract nutrient name from each part
            parts = description.split(" | ")
            for part in parts:
                if ":" in part:
                    # Extract just the nutrient name (last word before colon)
                    key_match = re.search(r'([A-Za-z]+)\s*:', part)
                    if key_match:
                        key = key_match.group(1).lower()
                        # Extract numeric value
                        value_match = re.search(r'([0-9.]+)', part.split(':', 1)[1])
                        if value_match:
                            nutrients[key] = float(value_match.group(1))
        
        return {
            "meal_name": meal_name,
            "serving_size": serving_size,
            "calories": round(nutrients.get("calories", 0)),
            "protein_g": round(nutrients.get("protein", 0), 1),
            "carbs_g": round(nutrients.get("carbs", 0), 1),
            "fat_g": round(nutrients.get("fat", 0), 1),
            "fiber_g": round(nutrients.get("fiber", 0), 1),
            "sugar_g": round(nutrients.get("sugar", 0), 1),
            "sodium_mg": round(nutrients.get("sodium", 0), 1)
        }
    
    def _get_estimated_nutrition(self, meal_name: str) -> Dict:
        """Fallback estimates when API unavailable"""
        name_lower = meal_name.lower()
        
        if any(word in name_lower for word in ['salad', 'greens']):
            return {"meal_name": meal_name, "calories": 150, "protein_g": 8.0, "carbs_g": 12.0, "fat_g": 9.0, "fiber_g": 4.0, "sugar_g": 6.0, "sodium_mg": 320.0}
        elif any(word in name_lower for word in ['chicken', 'turkey']):
            return {"meal_name": meal_name, "calories": 280, "protein_g": 35.0, "carbs_g": 8.0, "fat_g": 12.0, "fiber_g": 2.0, "sugar_g": 3.0, "sodium_mg": 450.0}
        elif any(word in name_lower for word in ['beef', 'steak']):
            return {"meal_name": meal_name, "calories": 350, "protein_g": 28.0, "carbs_g": 5.0, "fat_g": 24.0, "fiber_g": 1.0, "sugar_g": 2.0, "sodium_mg": 380.0}
        elif any(word in name_lower for word in ['fish', 'salmon']):
            return {"meal_name": meal_name, "calories": 220, "protein_g": 25.0, "carbs_g": 3.0, "fat_g": 12.0, "fiber_g": 0.5, "sugar_g": 1.0, "sodium_mg": 290.0}
        elif any(word in name_lower for word in ['pasta', 'noodles']):
            return {"meal_name": meal_name, "calories": 320, "protein_g": 12.0, "carbs_g": 58.0, "fat_g": 6.0, "fiber_g": 3.0, "sugar_g": 8.0, "sodium_mg": 420.0}
        elif 'pizza' in name_lower:
            return {"meal_name": meal_name, "calories": 285, "protein_g": 12.0, "carbs_g": 36.0, "fat_g": 10.0, "fiber_g": 2.5, "sugar_g": 4.0, "sodium_mg": 640.0}
        elif 'soup' in name_lower:
            return {"meal_name": meal_name, "calories": 180, "protein_g": 8.0, "carbs_g": 20.0, "fat_g": 7.0, "fiber_g": 3.0, "sugar_g": 5.0, "sodium_mg": 890.0}
        else:
            return {"meal_name": meal_name, "calories": 250, "protein_g": 15.0, "carbs_g": 25.0, "fat_g": 10.0, "fiber_g": 3.0, "sugar_g": 5.0, "sodium_mg": 400.0}