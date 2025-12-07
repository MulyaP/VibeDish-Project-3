import asyncio
import sys
sys.path.insert(0, '.')

from app.services.nutrition_service import NutritionService

async def test():
    service = NutritionService()
    
    print("Testing FatSecret API...")
    print(f"Client ID configured: {service.client_id is not None}")
    print(f"Client Secret configured: {service.client_secret is not None}")
    print()
    
    # Test getting token
    print("Getting access token...")
    token = await service._get_access_token()
    if token:
        print(f"✓ Token obtained: {token[:20]}...")
    else:
        print("✗ Failed to get token")
        return
    
    print()
    
    # Test nutrition lookup
    print("Testing nutrition lookup for 'chicken breast'...")
    result = await service.get_nutrition_data("chicken breast")
    
    print("\nResult:")
    for key, value in result.items():
        print(f"  {key}: {value}")

asyncio.run(test())
