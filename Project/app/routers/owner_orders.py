from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from ..db import get_db
from ..auth import current_user

router = APIRouter()


class UpdateOrderStatusRequest(BaseModel):
    status: str


@router.get("")
def get_restaurant_orders(user=Depends(current_user)):
    supabase = get_db()

    staff_response = supabase.table("restaurant_staff").select(
        "restaurant_id"
    ).eq("user_id", user["id"]).execute()

    if not staff_response.data:
        raise HTTPException(
            status_code=404,
            detail="No restaurant found for this user"
        )

    restaurant_id = staff_response.data[0]["restaurant_id"]

    orders_response = supabase.table("orders").select(
        "id, user_id, status, total, created_at, users:user_id(name), "
        "delivery_address"
    ).eq("restaurant_id", restaurant_id).in_(
        "status", ["pending", "accepted", "ready"]
    ).order("created_at", desc=True).execute()

    orders = []
    for order in orders_response.data:
        items_response = supabase.table("order_items").select(
            "qty, meals(name)"
        ).eq("order_id", order["id"]).execute()

        items = [
            {"name": item["meals"]["name"], "qty": item["qty"]}
            for item in items_response.data
        ]

        # address = order.get("addresses", {})
        # address_str = (
        #     f"{address.get('street', '')}, {address.get('city', '')}, "
        #     f"{address.get('state', '')} {address.get('zip_code', '')}"
        # ) if address else "N/A"

        orders.append({
            "id": order["id"],
            "customer_name": order["users"]["name"],
            "customer_address": order.get("delivery_address", "N/A"),
            "order_placement_time": order["created_at"],
            "items": items,
            "total": order["total"],
            "status": order["status"]
        })

    return orders


@router.patch("/{order_id}/status")
def update_order_status(
    order_id: str,
    request: UpdateOrderStatusRequest,
    user=Depends(current_user)
):
    supabase = get_db()

    order_response = supabase.table("orders").select(
        "id, restaurant_id"
    ).eq("id", order_id).execute()

    if not order_response.data:
        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )

    supabase.table("orders").update(
        {"status": request.status}
    ).eq("id", order_id).execute()

    supabase.table("order_status_events").insert(
        {"order_id": order_id, "status": request.status}
    ).execute()

    return {"id": order_id, "status": request.status}
