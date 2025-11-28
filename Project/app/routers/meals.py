# app/routers/meals.py
from fastapi import APIRouter, HTTPException, Query
from ..db import get_db

router = APIRouter()

@router.get("")
def list_meals(
    surplus_only: bool = Query(default=True),
    limit: int = Query(default=50, le=100),
    vegetarian: bool = Query(default=False),
    vegan: bool = Query(default=False),
    gluten_free: bool = Query(default=False),
    exclude_allergens: str = Query(default=""),
):
    try:
        supabase = get_db()
        query = supabase.table("meals").select("*")
        
        if surplus_only:
            query = query.gt("quantity", 0)
        
        query = query.order("created_at", desc=True).limit(limit)
        response = query.execute()
        meals = response.data
        
        # Apply dietary filters
        filtered_meals = []
        for meal in meals:
            tags = (meal.get("tags") or "").lower()
            allergens = (meal.get("allergens") or "").lower()
            
            # Check dietary preferences
            if vegetarian and "vegetarian" not in tags:
                continue
            if vegan and "vegan" not in tags:
                continue
            if gluten_free and "gluten" in allergens:
                continue
                
            # Check allergen exclusions
            if exclude_allergens:
                excluded = [a.strip().lower() for a in exclude_allergens.split(",")]
                if any(allergen in allergens for allergen in excluded):
                    continue
            
            filtered_meals.append(meal)
        
        return filtered_meals
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB error: {e}")
