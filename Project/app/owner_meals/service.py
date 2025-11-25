from fastapi import HTTPException
from ..db import get_db
from .schemas import MealCreate, MealUpdate

def get_restaurant_by_owner(user_id: str) -> str:
    db = get_db()
    result = db.table("restaurants").select("id").eq("owner_id", user_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="No restaurant found for this owner")
    return str(result.data[0]["id"])

def create_meal(restaurant_id: str, meal: MealCreate):
    db = get_db()
    result = db.table("meals").insert({
        "restaurant_id": str(restaurant_id),
        "name": meal.name,
        "tags": meal.tags,
        "base_price": meal.base_price,
        "quantity": meal.quantity,
        "surplus_price": meal.surplus_price,
        "allergens": meal.allergens,
        "calories": meal.calories,
        "image_link": meal.image_link
    }).execute()
    data = result.data[0]
    data["id"] = str(data["id"])
    data["restaurant_id"] = str(data["restaurant_id"])
    return data

def update_meal(meal_id: str, restaurant_id: str, meal: MealUpdate):
    db = get_db()
    check = db.table("meals").select("id").eq("id", meal_id).eq("restaurant_id", restaurant_id).execute()
    if not check.data:
        raise HTTPException(status_code=404, detail="Meal not found or not owned by your restaurant")
    
    updates = {}
    if meal.name is not None:
        updates["name"] = meal.name
    if meal.tags is not None:
        updates["tags"] = meal.tags
    if meal.base_price is not None:
        updates["base_price"] = meal.base_price
    if meal.quantity is not None:
        updates["quantity"] = meal.quantity
    if meal.surplus_price is not None:
        updates["surplus_price"] = meal.surplus_price
    if meal.allergens is not None:
        updates["allergens"] = meal.allergens
    if meal.calories is not None:
        updates["calories"] = meal.calories
    if meal.image_link is not None:
        updates["image_link"] = meal.image_link
    
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    result = db.table("meals").update(updates).eq("id", meal_id).execute()
    data = result.data[0]
    data["id"] = str(data["id"])
    data["restaurant_id"] = str(data["restaurant_id"])
    return data

def delete_meal(meal_id: str, restaurant_id: str):
    db = get_db()
    check = db.table("meals").select("id").eq("id", meal_id).eq("restaurant_id", restaurant_id).execute()
    if not check.data:
        raise HTTPException(status_code=404, detail="Meal not found or not owned by your restaurant")
    
    db.table("meals").delete().eq("id", meal_id).execute()

def get_restaurant_meals(restaurant_id: str):
    db = get_db()
    result = db.table("meals").select("*").eq("restaurant_id", restaurant_id).order("created_at", desc=True).execute()
    return [{**row, "id": str(row["id"]), "restaurant_id": str(row["restaurant_id"])} for row in result.data]
