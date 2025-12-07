# app/routers/orders.py
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Any
from ..db import get_db
from ..auth import current_user

router = APIRouter()

ALLOWED_TRANSITIONS = {
    "pending": {"accepted", "cancelled"},
    "accepted": {"preparing", "cancelled"},
    "preparing": {"ready", "cancelled"},
    "ready": {"completed"},
    "completed": set(),
    "cancelled": set(),
}

def _is_user_staff_for_order(user_id: str, order_id: str) -> bool:
    supabase = get_db()
    response = supabase.table("orders").select("restaurant_id").eq("id", order_id).execute()
    if not response.data:
        return False
    restaurant_id = response.data[0]["restaurant_id"]
    
    staff_response = supabase.table("restaurant_staff").select("user_id").eq("restaurant_id", restaurant_id).eq("user_id", user_id).execute()
    return len(staff_response.data) > 0

def _transition_order(order_id: str, target: str):
    supabase = get_db()
    order_response = supabase.table("orders").select("*").eq("id", order_id).execute()
    if not order_response.data:
        raise HTTPException(status_code=404, detail="order not found")
    
    order = order_response.data[0]
    cur = order["status"]
    if target not in ALLOWED_TRANSITIONS.get(cur, set()):
        raise HTTPException(status_code=400, detail=f"invalid transition {cur} -> {target}")
    
    supabase.table("orders").update({"status": target}).eq("id", order_id).execute()
    supabase.table("order_status_events").insert({"order_id": order_id, "status": target}).execute()
    
    updated = supabase.table("orders").select("*").eq("id", order_id).execute()
    return updated.data[0]

@router.post("")
def create_order(payload: Dict[str, Any], user=Depends(current_user)):
    restaurant_id = payload.get("restaurant_id")
    items: List[dict] = payload.get("items") or []
    if not restaurant_id or not items:
        raise HTTPException(status_code=400, detail="restaurant_id and items required")
    
    supabase = get_db()
    order_response = supabase.table("orders").insert({
        "user_id": user["id"],
        "restaurant_id": restaurant_id,
        "status": "pending",
        "total": 0,
        "delivery_user_id": None
    }).execute()
    order_id = order_response.data[0]["id"]
    
    supabase.table("order_status_events").insert({"order_id": order_id, "status": "pending"}).execute()
    
    total = 0.0
    for it in items:
        meal_id = it.get("meal_id")
        qty = int(it.get("qty", 0))
        if not meal_id or qty <= 0:
            raise HTTPException(status_code=400, detail="each item needs meal_id and positive qty")
        
        meal_response = supabase.table("meals").select("*").eq("id", meal_id).execute()
        if not meal_response.data:
            raise HTTPException(status_code=404, detail=f"meal {meal_id} not found")
        meal = meal_response.data[0]
        
        if (meal.get("quantity") or 0) < qty:
            raise HTTPException(status_code=400, detail=f"not enough surplus for meal {meal_id}")
        
        line_price = float(meal["surplus_price"]) * qty
        total += line_price
        
        supabase.table("order_items").insert({
            "order_id": order_id,
            "meal_id": meal_id,
            "qty": qty,
            "price": line_price
        }).execute()
        
        new_qty = int(meal["quantity"]) - qty
        supabase.table("meals").update({"quantity": new_qty}).eq("id", meal_id).execute()
    
    supabase.table("orders").update({"total": total}).eq("id", order_id).execute()
    final = supabase.table("orders").select("*").eq("id", order_id).execute()
    return final.data[0]

@router.get("/mine")
def list_my_orders(user=Depends(current_user), limit: int = Query(default=50, le=100)):
    supabase = get_db()
    response = supabase.table("orders").select("id,restaurant_id,restaurants(name),status,total,created_at,delivery_code").eq("user_id", user["id"]).order("created_at", desc=True).limit(limit).execute()
    return response.data

@router.get("/{order_id}")
def get_order(order_id: str, user=Depends(current_user)):
    supabase = get_db()
    order_response = supabase.table("orders").select("*, restaurants(name)").eq("id", order_id).execute()
    if not order_response.data:
        raise HTTPException(status_code=404, detail="order not found")
    
    order = order_response.data[0]
    if str(order["user_id"]) != str(user["id"]):
        raise HTTPException(status_code=403, detail="not your order")
    
    items_response = supabase.table("order_items").select("*, meals(name)").eq("order_id", order_id).execute()
    items = [{"id": item["id"], "meal_id": item["meal_id"], "meal_name": item["meals"]["name"], "qty": item["qty"], "price": item["price"]} for item in items_response.data]
    
    return {"order": order, "items": items}

@router.get("/{order_id}/status")
def get_order_status_timeline(order_id: str, user=Depends(current_user)):
    supabase = get_db()
    order_response = supabase.table("orders").select("user_id").eq("id", order_id).execute()
    if not order_response.data:
        raise HTTPException(status_code=404, detail="order not found")
    
    if str(order_response.data[0]["user_id"]) != str(user["id"]):
        raise HTTPException(status_code=403, detail="not your order")
    
    events_response = supabase.table("order_status_events").select("status,created_at").eq("order_id", order_id).order("created_at").execute()
    return {"order_id": order_id, "timeline": events_response.data}

@router.patch("/{order_id}/cancel")
def cancel_order(order_id: str, user=Depends(current_user)):
    supabase = get_db()
    order_response = supabase.table("orders").select("*").eq("id", order_id).execute()
    if not order_response.data:
        raise HTTPException(status_code=404, detail="order not found")
    
    order = order_response.data[0]
    if str(order["user_id"]) != str(user["id"]):
        raise HTTPException(status_code=403, detail="not your order")
    
    if order["status"] != "pending":
        raise HTTPException(status_code=400, detail="cannot cancel after it is accepted")
    
    items_response = supabase.table("order_items").select("meal_id,qty").eq("order_id", order_id).execute()
    for item in items_response.data:
        meal = supabase.table("meals").select("quantity").eq("id", item["meal_id"]).execute().data[0]
        new_qty = int(meal["quantity"]) + int(item["qty"])
        supabase.table("meals").update({"quantity": new_qty}).eq("id", item["meal_id"]).execute()
    
    supabase.table("orders").update({"status": "cancelled"}).eq("id", order_id).execute()
    supabase.table("order_status_events").insert({"order_id": order_id, "status": "cancelled"}).execute()
    
    return {"status": "cancelled", "order_id": order_id}

@router.patch("/{order_id}/accept")
def accept_order(order_id: str, user=Depends(current_user)):
    if not _is_user_staff_for_order(user["id"], order_id):
        raise HTTPException(status_code=403, detail="not allowed")
    return _transition_order(order_id, "accepted")

@router.patch("/{order_id}/preparing")
def preparing_order(order_id: str, user=Depends(current_user)):
    if not _is_user_staff_for_order(user["id"], order_id):
        raise HTTPException(status_code=403, detail="not allowed")
    return _transition_order(order_id, "preparing")

@router.patch("/{order_id}/ready")
def ready_order(order_id: str, user=Depends(current_user)):
    if not _is_user_staff_for_order(user["id"], order_id):
        raise HTTPException(status_code=403, detail="not allowed")
    return _transition_order(order_id, "ready")

@router.patch("/{order_id}/complete")
def complete_order(order_id: str, user=Depends(current_user)):
    if not _is_user_staff_for_order(user["id"], order_id):
        raise HTTPException(status_code=403, detail="not allowed")
    return _transition_order(order_id, "completed")

@router.patch("/{order_id}/status")
def update_order_status(order_id: str, payload: Dict[str, Any], user=Depends(current_user)):
    status = payload.get("status")
    delivery_code = payload.get("delivery_code")
    
    supabase = get_db()
    order_response = supabase.table("orders").select("*").eq("id", order_id).execute()
    if not order_response.data:
        raise HTTPException(status_code=404, detail="order not found")
    
    order = order_response.data[0]
    
    if str(order["delivery_user_id"]) != str(user["id"]):
        raise HTTPException(status_code=403, detail="not authorized")
    
    if status == "delivered":
        if not delivery_code:
            raise HTTPException(status_code=400, detail="delivery code required")
        if delivery_code != order.get("delivery_code"):
            raise HTTPException(status_code=400, detail="invalid delivery code")
    
    supabase.table("orders").update({"status": status}).eq("id", order_id).execute()
    supabase.table("order_status_events").insert({"order_id": order_id, "status": status}).execute()
    
    updated = supabase.table("orders").select("*").eq("id", order_id).execute()
    return updated.data[0]
