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


@router.get("/analytics")
def get_restaurant_analytics(user=Depends(current_user)):
    supabase = get_db()

    staff_response = supabase.table("restaurant_staff").select(
        "restaurant_id, restaurants(name)"
    ).eq("user_id", user["id"]).execute()

    if not staff_response.data:
        raise HTTPException(
            status_code=404,
            detail="No restaurant found for this user"
        )

    restaurant_id = staff_response.data[0]["restaurant_id"]
    restaurant_name = staff_response.data[0]["restaurants"]["name"]

    # Get all orders for the restaurant
    orders_response = (
        supabase.table("orders")
        .select(
        "id, user_id, total, restaurant_rating, restaurant_comment, created_at, delivery_fee, tip_amount, tax"
        )
        .eq("restaurant_id", restaurant_id)
        .in_("status", ["delivered", "completed"])
        .execute()
    )

    orders = orders_response.data
    total_orders = len(orders)
    total_revenue = sum(
        order["total"] - (order.get("delivery_fee", 0) or 0) - (order.get("tip_amount", 0) or 0) - (order.get("tax", 0) or 0)
        for order in orders
    )
    avg_order_value = round(total_revenue / total_orders, 2) if total_orders > 0 else 0

    # Calculate average rating
    ratings = [order["restaurant_rating"] for order in orders if order.get("restaurant_rating")]
    avg_rating = round(sum(ratings) / len(ratings), 1) if ratings else 0
    total_reviews = len(ratings)

    # Calculate repeat customers
    user_order_counts = {}
    for order in orders:
        user_id = order["user_id"]
        user_order_counts[user_id] = user_order_counts.get(user_id, 0) + 1
    
    unique_customers = len(user_order_counts)
    repeat_customers = sum(1 for count in user_order_counts.values() if count > 1)
    repeat_customer_ratio = round((repeat_customers / unique_customers * 100), 0) if unique_customers > 0 else 0

    # Get popular dishes
    order_items_response = (
        supabase.table("order_items")
        .select(
            "meal_id, qty, price, meals(name, image_link), order_id"
        )
        .in_("order_id", [order["id"] for order in orders])
        .execute()
    )

    print(order_items_response)

    meal_stats = {}
    for item in order_items_response.data:
        meal_id = item["meal_id"]
        if meal_id not in meal_stats:
            meal_stats[meal_id] = {
                "name": item["meals"]["name"],
                "image": item["meals"].get("image_link", ""),
                "orders": 0,
                "revenue": 0
            }
        meal_stats[meal_id]["orders"] += 1
        meal_stats[meal_id]["revenue"] += item["price"]

    popular_dishes = sorted(
        [{"id": k, **v, "revenue": round(v.get("revenue", 0), 2)} for k, v in meal_stats.items()],
        key=lambda x: x["orders"],
        reverse=True
    )[:5]

    # Get recent reviews
    recent_reviews_response = supabase.table("orders").select(
        "id, restaurant_rating, restaurant_comment, created_at, users:user_id(name)"
    ).eq("restaurant_id", restaurant_id).not_.is_("restaurant_rating", "null").order(
        "created_at", desc=True
    ).limit(10).execute()

    recent_reviews = []
    for review in recent_reviews_response.data:
        if review.get("restaurant_rating"):
            recent_reviews.append({
                "id": review["id"],
                "customer": review["users"]["name"],
                "rating": review["restaurant_rating"],
                "comment": review.get("restaurant_comment", ""),
                "date": review["created_at"]
            })

    return {
        "restaurant": {
            "name": restaurant_name,
            "averageRating": avg_rating,
            "totalReviews": total_reviews,
            "totalOrders": total_orders
        },
        "stats": {
            "totalRevenue": round(total_revenue, 2),
            "avgOrderValue": avg_order_value,
            "repeatCustomers": int(repeat_customer_ratio)
        },
        "popularDishes": popular_dishes,
        "recentReviews": recent_reviews
    }
