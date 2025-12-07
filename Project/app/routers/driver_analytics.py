from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timedelta, timezone
from ..db import get_db
from ..auth import current_user

router = APIRouter()


@router.get("/analytics")
def get_driver_analytics(user=Depends(current_user)):
    supabase = get_db()

    # Get all delivered orders for this driver
    orders_response = supabase.table("orders").select(
        "id, restaurant_id, delivery_fee, tip_amount, created_at, "
        "restaurants(name), customer:user_id(name)"
    ).eq("delivery_user_id", user["id"]).eq("status", "delivered").execute()

    orders = orders_response.data
    total_deliveries = len(orders)

    if total_deliveries == 0:
        return {
            "stats": {
                "totalEarnings": 0,
                "totalDeliveries": 0,
                "avgEarningsPerDelivery": 0,
                "totalTips": 0,
                "totalDeliveryFees": 0
            },
            "topRestaurants": [],
            "recentDeliveries": [],
            "earningsByDay": []
        }

    # Calculate earnings
    total_delivery_fees = sum(order.get("delivery_fee", 0) or 0 for order in orders)
    total_tips = sum(order.get("tip_amount", 0) or 0 for order in orders)
    total_earnings = total_delivery_fees + total_tips
    avg_earnings = round(total_earnings / total_deliveries, 2) if total_deliveries > 0 else 0

    # Top restaurants by delivery count
    restaurant_stats = {}
    for order in orders:
        rid = order["restaurant_id"]
        if rid not in restaurant_stats:
            restaurant_stats[rid] = {
                "name": order["restaurants"]["name"],
                "deliveries": 0,
                "earnings": 0
            }
        restaurant_stats[rid]["deliveries"] += 1
        restaurant_stats[rid]["earnings"] += (order.get("delivery_fee", 0) or 0) + (order.get("tip_amount", 0) or 0)

    top_restaurants = sorted(
        [{"id": k, **v, "earnings": round(v["earnings"], 2)} for k, v in restaurant_stats.items()],
        key=lambda x: x["deliveries"],
        reverse=True
    )[:5]

    # Recent deliveries
    recent_deliveries = sorted(orders, key=lambda x: x["created_at"], reverse=True)[:10]
    recent_deliveries_formatted = [
        {
            "id": d["id"],
            "restaurant": d["restaurants"]["name"],
            "customer": d["customer"]["name"],
            "earnings": round((d.get("delivery_fee", 0) or 0) + (d.get("tip_amount", 0) or 0), 2),
            "date": d["created_at"]
        }
        for d in recent_deliveries
    ]

    # Earnings by day (last 7 days)
    today = datetime.now(timezone.utc)
    earnings_by_day = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        day_orders = [
            o for o in orders
            if day_start <= datetime.fromisoformat(o["created_at"].replace('Z', '+00:00')) <= day_end
        ]
        
        day_earnings = sum(
            (o.get("delivery_fee", 0) or 0) + (o.get("tip_amount", 0) or 0)
            for o in day_orders
        )
        
        earnings_by_day.append({
            "date": day.strftime("%Y-%m-%d"),
            "day": day.strftime("%a"),
            "earnings": round(day_earnings, 2),
            "deliveries": len(day_orders)
        })

    return {
        "stats": {
            "totalEarnings": round(total_earnings, 2),
            "totalDeliveries": total_deliveries,
            "avgEarningsPerDelivery": avg_earnings,
            "totalTips": round(total_tips, 2),
            "totalDeliveryFees": round(total_delivery_fees, 2)
        },
        "topRestaurants": top_restaurants,
        "recentDeliveries": recent_deliveries_formatted,
        "earningsByDay": earnings_by_day
    }
