from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from ..db import get_db
from ..auth import current_user

router = APIRouter()

class FeedbackRequest(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None

@router.post("/{order_id}/feedback/restaurant")
def submit_restaurant_feedback(order_id: str, feedback: FeedbackRequest, user=Depends(current_user)):
    supabase = get_db()
    
    order_response = supabase.table("orders").select("user_id,status,restaurant_rating").eq("id", order_id).execute()
    if not order_response.data:
        raise HTTPException(status_code=404, detail="Order not found")
    
    order = order_response.data[0]
    if str(order["user_id"]) != str(user["id"]):
        raise HTTPException(status_code=403, detail="Not your order")
    
    if order["status"] not in ["delivered", "completed"]:
        raise HTTPException(status_code=400, detail="Can only rate completed orders")
    
    if order.get("restaurant_rating"):
        raise HTTPException(status_code=400, detail="Restaurant feedback already submitted")
    
    supabase.table("orders").update({
        "restaurant_rating": feedback.rating,
        "restaurant_comment": feedback.comment
    }).eq("id", order_id).execute()
    
    return {"message": "Restaurant feedback submitted", "rating": feedback.rating}

@router.post("/{order_id}/feedback/driver")
def submit_driver_feedback(order_id: str, feedback: FeedbackRequest, user=Depends(current_user)):
    supabase = get_db()
    
    order_response = supabase.table("orders").select("user_id,status,driver_rating").eq("id", order_id).execute()
    if not order_response.data:
        raise HTTPException(status_code=404, detail="Order not found")
    
    order = order_response.data[0]
    if str(order["user_id"]) != str(user["id"]):
        raise HTTPException(status_code=403, detail="Not your order")
    
    if order["status"] not in ["delivered", "completed"]:
        raise HTTPException(status_code=400, detail="Can only rate completed orders")
    
    if order.get("driver_rating"):
        raise HTTPException(status_code=400, detail="Driver feedback already submitted")
    
    supabase.table("orders").update({
        "driver_rating": feedback.rating,
        "driver_comment": feedback.comment
    }).eq("id", order_id).execute()
    
    return {"message": "Driver feedback submitted", "rating": feedback.rating}

@router.get("/{order_id}/feedback")
def get_order_feedback(order_id: str, user=Depends(current_user)):
    supabase = get_db()
    
    order_response = supabase.table("orders").select(
        "user_id,restaurant_rating,restaurant_comment,driver_rating,driver_comment"
    ).eq("id", order_id).execute()
    
    if not order_response.data:
        raise HTTPException(status_code=404, detail="Order not found")
    
    order = order_response.data[0]
    if str(order["user_id"]) != str(user["id"]):
        raise HTTPException(status_code=403, detail="Not your order")
    
    result = {}
    
    if order.get("restaurant_rating"):
        result["restaurant_feedback"] = {
            "rating": order["restaurant_rating"],
            "comment": order.get("restaurant_comment")
        }
    
    if order.get("driver_rating"):
        result["driver_feedback"] = {
            "rating": order["driver_rating"],
            "comment": order.get("driver_comment")
        }
    
    return result
