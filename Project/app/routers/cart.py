# app/routers/cart.py
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from typing import Dict, Any
from ..db import get_db
from ..auth import current_user

router = APIRouter(prefix="/cart", tags=["cart"])

def _get_or_create_cart_id(user_id: str) -> str:
    supabase = get_db()
    response = supabase.table("carts").select("id").eq("user_id", user_id).execute()
    if response.data:
        return response.data[0]["id"]
    
    response = supabase.table("carts").insert({"user_id": user_id}).execute()
    return response.data[0]["id"]

def _get_cart_payload(cart_id: str) -> Dict[str, Any]:
    supabase = get_db()
    response = supabase.table("cart_items").select("*, meals(*)").eq("cart_id", cart_id).execute()
    
    items = []
    total = 0.0
    for item in response.data:
        meal = item["meals"]
        unit_price = float(meal["surplus_price"]) if meal.get("surplus_price") else float(meal["base_price"])
        qty = int(item["qty"])
        line_total = unit_price * qty
        total += line_total
        items.append({
            "item_id": item["id"],
            "meal_id": item["meal_id"],
            "meal_name": meal["name"],
            "restaurant_id": meal["restaurant_id"],
            "qty": qty,
            "unit_price": unit_price,
            "line_total": line_total,
            "surplus_left": int(meal.get("quantity") or 0),
        })
    return {"cart_id": cart_id, "items": items, "cart_total": total}

@router.get("")
def get_my_cart(user=Depends(current_user)):
    cart_id = _get_or_create_cart_id(user["id"])
    return _get_cart_payload(cart_id)

@router.post("/items")
def add_item(payload: dict, user=Depends(current_user)):
    meal_id = payload.get("meal_id")
    add_qty = int(payload.get("qty") or 0)
    if not meal_id or add_qty <= 0:
        raise HTTPException(status_code=400, detail="meal_id and positive qty required")
    
    supabase = get_db()
    cart_id = _get_or_create_cart_id(user["id"])
    
    meal_response = supabase.table("meals").select("id,quantity").eq("id", meal_id).execute()
    if not meal_response.data:
        raise HTTPException(status_code=404, detail="meal not found")
    meal = meal_response.data[0]
    
    existing = supabase.table("cart_items").select("qty").eq("cart_id", cart_id).eq("meal_id", meal_id).execute()
    current_qty = int(existing.data[0]["qty"]) if existing.data else 0
    new_qty = current_qty + add_qty
    
    if meal.get("quantity") and new_qty > int(meal["quantity"]):
        raise HTTPException(status_code=409, detail=f"only {meal['quantity']} left for this item")
    
    if existing.data:
        supabase.table("cart_items").update({"qty": new_qty}).eq("cart_id", cart_id).eq("meal_id", meal_id).execute()
    else:
        supabase.table("cart_items").insert({"cart_id": cart_id, "meal_id": meal_id, "qty": add_qty}).execute()
    
    return _get_cart_payload(cart_id)

@router.patch("/items/{item_id}")
def update_item_qty(item_id: str = Path(...), qty: int = Query(..., gt=0), user=Depends(current_user)):
    supabase = get_db()
    cart_id = _get_or_create_cart_id(user["id"])
    
    item_response = supabase.table("cart_items").select("meal_id, meals(quantity)").eq("id", item_id).eq("cart_id", cart_id).execute()
    if not item_response.data:
        raise HTTPException(status_code=404, detail="item not found")
    
    meal_qty = item_response.data[0]["meals"]["quantity"]
    if meal_qty and qty > int(meal_qty):
        raise HTTPException(status_code=409, detail=f"only {meal_qty} left for this item")
    
    supabase.table("cart_items").update({"qty": qty}).eq("id", item_id).execute()
    return _get_cart_payload(cart_id)

@router.delete("/items/{item_id}")
def remove_item(item_id: str, user=Depends(current_user)):
    supabase = get_db()
    cart_id = _get_or_create_cart_id(user["id"])
    supabase.table("cart_items").delete().eq("id", item_id).eq("cart_id", cart_id).execute()
    return _get_cart_payload(cart_id)

@router.delete("")
def clear_cart(user=Depends(current_user)):
    supabase = get_db()
    cart_id = _get_or_create_cart_id(user["id"])
    supabase.table("cart_items").delete().eq("cart_id", cart_id).execute()
    return _get_cart_payload(cart_id)

@router.post("/checkout")
def checkout_cart(user=Depends(current_user)):
    supabase = get_db()
    cart_id = _get_or_create_cart_id(user["id"])
    
    items_response = supabase.table("cart_items").select("*, meals(*)").eq("cart_id", cart_id).execute()
    if not items_response.data:
        raise HTTPException(status_code=400, detail="cart is empty")
    
    rest_ids = {item["meals"]["restaurant_id"] for item in items_response.data}
    if len(rest_ids) != 1:
        raise HTTPException(status_code=400, detail="cart contains items from multiple restaurants")
    restaurant_id = list(rest_ids)[0]
    
    total = 0.0
    for item in items_response.data:
        meal = item["meals"]
        is_surplus = meal.get("surplus_price") and meal.get("quantity")
        
        if is_surplus:
            if int(meal["quantity"]) < int(item["qty"]):
                raise HTTPException(status_code=400, detail=f"not enough surplus for meal {item['meal_id']}")
            price_per_item = float(meal["surplus_price"])
        else:
            price_per_item = float(meal["base_price"])
        
        total += price_per_item * int(item["qty"])
    
    order_response = supabase.table("orders").insert({
        "user_id": user["id"],
        "restaurant_id": restaurant_id,
        "status": "pending",
        "total": total,
        "delivery_user_id": None
    }).execute()
    order_id = order_response.data[0]["id"]
    
    for item in items_response.data:
        meal = item["meals"]
        is_surplus = meal.get("surplus_price") and meal.get("quantity")
        price_per_item = float(meal["surplus_price"]) if is_surplus else float(meal["base_price"])
        line_price = price_per_item * int(item["qty"])
        
        supabase.table("order_items").insert({
            "order_id": order_id,
            "meal_id": item["meal_id"],
            "qty": int(item["qty"]),
            "price": line_price
        }).execute()
        
        if is_surplus:
            current_meal = supabase.table("meals").select("quantity").eq("id", item["meal_id"]).execute().data[0]
            new_qty = int(current_meal["quantity"]) - int(item["qty"])
            supabase.table("meals").update({"quantity": new_qty}).eq("id", item["meal_id"]).execute()
    
    supabase.table("order_status_events").insert({"order_id": order_id, "status": "pending"}).execute()
    supabase.table("cart_items").delete().eq("cart_id", cart_id).execute()
    
    return {"order_id": order_id, "status": "pending", "total": total}
