# app/routers/catalog.py
from fastapi import APIRouter, Query
from typing import Optional
from ..db import get_db

router = APIRouter()

@router.get("/restaurants")
def list_restaurants(
    search: Optional[str] = Query(default=None, description="Search substring for restaurant name"),
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0),
    sort: str = Query(default="name_asc", description="one of: name_asc,name_desc"),
):
    supabase = get_db()
    query = supabase.table("restaurants").select("id,name,address,latitude,longitude")
    
    if search:
        query = query.ilike("name", f"%{search}%")
    
    ascending = sort == "name_asc"
    query = query.order("name", desc=not ascending).range(offset, offset + limit - 1)
    
    response = query.execute()
    return response.data


@router.get("/restaurants/{restaurant_id}/meals")
def list_meals_for_restaurant(
    restaurant_id: str,
    surplus_only: bool = Query(default=False, description="Only show meals with surplus available"),
    search: Optional[str] = Query(default=None, description="Search substring for meal name"),
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0),
    sort: str = Query(
        default="name_asc",
        description="one of: name_asc,name_desc,price_asc,price_desc"
    ),
    vegetarian: bool = Query(default=False),
    vegan: bool = Query(default=False),
    gluten_free: bool = Query(default=False),
    exclude_allergens: str = Query(default=""),
):
    supabase = get_db()
    query = supabase.table("meals").select("*").eq("restaurant_id", restaurant_id)
    
    if surplus_only:
        query = query.gt("quantity", 0)
    
    if search:
        query = query.ilike("name", f"%{search}%")
    
    sort_col = "name" if "name" in sort else "surplus_price"
    ascending = "asc" in sort
    query = query.order(sort_col, desc=not ascending).range(offset, offset + limit - 1)
    
    response = query.execute()
    meals = response.data
    
    # Apply dietary filters
    if not (vegetarian or vegan or gluten_free or exclude_allergens):
        return meals
        
    filtered_meals = []
    for meal in meals:
        # Handle tags as string or array
        tags = meal.get("tags") or []
        if isinstance(tags, str):
            tags = [tags] if tags else []
        tags_lower = [tag.lower() for tag in tags]
        
        # Handle allergens as string or array  
        allergens = meal.get("allergens") or []
        if isinstance(allergens, str):
            allergens = [allergens] if allergens else []
        allergens_lower = [allergen.lower() for allergen in allergens]
        
        # Check dietary preferences
        if vegetarian and "vegetarian" not in tags_lower:
            continue
        if vegan and "vegan" not in tags_lower:
            continue
        if gluten_free and any("gluten" in allergen for allergen in allergens_lower):
            continue
            
        # Check allergen exclusions
        if exclude_allergens:
            excluded = [a.strip().lower() for a in exclude_allergens.split(",") if a.strip()]
            if any(any(exc in allergen for exc in excluded) for allergen in allergens_lower):
                continue
        
        filtered_meals.append(meal)
    
    return filtered_meals
