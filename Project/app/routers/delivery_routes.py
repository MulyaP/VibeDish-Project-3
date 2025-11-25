import httpx
from fastapi import APIRouter, HTTPException, status, Depends, Header, Query
import os
import asyncio
from dotenv import load_dotenv
from app.models.delivery_models import Location
from app.db import get_db
from app.auth import current_user

load_dotenv()

router = APIRouter()

MAPBOX_TOKEN = os.getenv("NEXT_PUBLIC_MAPBOX_TOKEN") or os.getenv("MAPBOX_TOKEN")
MAX_DEST_PER_MATRIX = 24

if not MAPBOX_TOKEN:
    print("WARNING: MAPBOX_TOKEN not found in environment variables")

def location_from_query(
    latitude: float = Query(...), longitude: float = Query(...)
) -> Location:
    return Location(latitude=latitude, longitude=longitude)

def _extract_restaurant_coords(orders):
    """Extract restaurant IDs and coordinates from orders."""
    restaurant_ids = []
    restaurant_coords_by_id = {}

    for o in orders:
        rid = o.get("restaurant_id")
        if rid is not None and rid not in restaurant_ids:
            restaurant_ids.append(rid)

        rest_info = o.get("restaurants") or {}
        lat_raw = rest_info.get("latitude")
        lng_raw = rest_info.get("longitude")
        try:
            if lat_raw is not None and lng_raw is not None:
                latitude = float(lat_raw)
                longitude = float(lng_raw)
                restaurant_coords_by_id[rid] = (latitude, longitude)
        except (TypeError, ValueError):
            pass

    return restaurant_ids, restaurant_coords_by_id

def _prepare_destinations(restaurant_ids, restaurant_coords_by_id):
    """Prepare destination list and filter out those without coordinates."""
    dests = []
    for rid in restaurant_ids:
        coords = restaurant_coords_by_id.get(rid)
        if coords:
            dests.append({"restaurant_id": rid, "lat": coords[0], "lng": coords[1]})
        else:
            dests.append({"restaurant_id": rid, "lat": None, "lng": None})

    return [ri for ri in dests if ri["lat"] is not None and ri["lng"] is not None]

async def _fetch_matrix_for_chunk(src_lng, src_lat, chunk):
    """Fetch distance matrix for a chunk of destinations."""
    if not MAPBOX_TOKEN:
        print("ERROR: MAPBOX_TOKEN is not set")
        return {}
    
    if not chunk:
        return {}
    
    coordinates = [[src_lng, src_lat]] + [[c["lng"], c["lat"]] for c in chunk]
    coordinates_str = ";".join(f"{lng},{lat}" for lng, lat in coordinates)
    
    params = {
        "access_token": MAPBOX_TOKEN,
        "sources": "0",
        "annotations": "distance,duration",
    }

    url = f"https://api.mapbox.com/directions-matrix/v1/mapbox/driving/{coordinates_str}"
    
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPError as http_err:
        print(f"HTTP error occurred while fetching matrix: {http_err}")
        return {}


async def _compute_distances_and_durations(src_lng, src_lat, dests):
    """Compute distances and durations to all destinations."""
    if not dests:
        return {}, {}

    chunks = [
        dests[i : i + MAX_DEST_PER_MATRIX]
        for i in range(0, len(dests), MAX_DEST_PER_MATRIX)
    ]

    tasks = [_fetch_matrix_for_chunk(src_lng, src_lat, chunk) for chunk in chunks]
    results = await asyncio.gather(*tasks)

    distance_by_restaurant = {}
    duration_by_restaurant = {}

    for chunk_result, chunk in zip(results, chunks):
        distances_matrix = chunk_result.get("distances")
        durations_matrix = chunk_result.get("durations")

        distances_from_source = (
            distances_matrix[0][1:]
            if distances_matrix and len(distances_matrix) > 0
            else [None] * len(chunk)
        )
        durations_from_source = (
            durations_matrix[0][1:]
            if durations_matrix and len(durations_matrix) > 0
            else [None] * len(chunk)
        )

        for item, dist_val, dur_val in zip(
            chunk, distances_from_source, durations_from_source
        ):
            rid = item.get("restaurant_id")
            distance_by_restaurant[rid] = (
                float(dist_val) if dist_val is not None else None
            )
            duration_by_restaurant[rid] = (
                float(dur_val) if dur_val is not None else None
            )

    return distance_by_restaurant, duration_by_restaurant

def _enrich_order_with_distance(order, distance_by_restaurant, duration_by_restaurant):
    """Enrich a single order with distance and duration information."""
    o_enriched = dict(order)
    rid = order.get("restaurant_id")
    dist_m = distance_by_restaurant.get(rid)
    dur_s = duration_by_restaurant.get(rid)

    o_enriched["distance_to_restaurant"] = dist_m
    o_enriched["duration_to_restaurant"] = dur_s

    if dist_m is not None:
        o_enriched["distance_to_restaurant_miles"] = round(dist_m / 1609.34, 3)
        o_enriched["restaurant_reachable_by_road"] = True
    else:
        o_enriched["distance_to_restaurant_miles"] = None
        o_enriched["restaurant_reachable_by_road"] = False

    if dur_s is not None:
        o_enriched["duration_to_restaurant_minutes"] = round(dur_s / 60.0, 1)
    else:
        o_enriched["duration_to_restaurant_minutes"] = None

    return o_enriched

@router.get("/deliveries/ready", response_model=list)
async def fetch_ready_orders(source: Location = Depends(location_from_query)):
    """Fetch all orders that are ready for delivery"""
    try:
        supabase = get_db()
        result = (
            supabase.from_("orders")
            .select(
                "id, user_id, restaurant_id, restaurants(name, latitude, longitude, address), customer:user_id(name), delivery_address , delivery_fee, tip_amount, latitude, longitude, status, distance_restaurant_delivery, duration_restaurant_delivery"
            )
            .eq("status", "ready")
            .is_("delivery_user_id", None)
            .execute()
        )
        orders = result.data or []

        if not orders:
            return []

        # Extract restaurant coordinates
        restaurant_ids, restaurant_coords_by_id = _extract_restaurant_coords(orders)

        # Prepare destinations
        dests = _prepare_destinations(restaurant_ids, restaurant_coords_by_id)
        src_lng, src_lat = float(source.longitude), float(source.latitude)

        # Compute distances and durations
        distance_by_restaurant, duration_by_restaurant = (
            await _compute_distances_and_durations(src_lng, src_lat, dests)
        )

        # Attach distances and durations to orders
        enriched_orders = [
            _enrich_order_with_distance(
                o, distance_by_restaurant, duration_by_restaurant
            )
            for o in orders
        ]

        return enriched_orders
        # return orders

    except Exception as e:
        print(f"Error fetching ready orders: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch ready orders")

@router.get("/deliveries/active", response_model=list)
async def fetch_active_orders(user = Depends(current_user)):
    """Fetch active delivery orders for the current driver"""
    try:
        supabase = get_db()
        result = (
            supabase.from_("orders")
            .select(
                "id, user_id, restaurant_id, restaurants(name, address, latitude, longitude), customer:user_id(name), delivery_address, delivery_fee, tip_amount, total, status, created_at, latitude, longitude"
            )
            .eq("delivery_user_id", user["id"])
            .in_("status", ["assigned", "out-for-delivery"])
            .execute()
        )
        return result.data or []
    except Exception as e:
        print(f"Error fetching active orders: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch active orders")

@router.patch("/deliveries/{order_id}/accept")
async def accept_delivery_order(order_id: str, user = Depends(current_user)):
    """Accept a delivery order and assign it to the driver"""
    try:
        supabase = get_db()
        
        # Check if driver already has an active order
        active_orders = supabase.table("orders").select("id").eq("delivery_user_id", user["id"]).in_("status", ["assigned", "out-for-delivery"]).execute()
        if active_orders.data:
            raise HTTPException(status_code=400, detail="You already have an active delivery order")
        
        order_response = supabase.table("orders").select("*").eq("id", order_id).execute()
        if not order_response.data:
            raise HTTPException(status_code=404, detail="Order not found")
        
        order = order_response.data[0]
        if order["status"] != "ready":
            raise HTTPException(status_code=400, detail="Order is not ready for delivery")
        
        if order["delivery_user_id"] is not None:
            raise HTTPException(status_code=400, detail="Order already assigned to another driver")
        
        supabase.table("orders").update({
            "delivery_user_id": user["id"],
            "status": "assigned"
        }).eq("id", order_id).execute()
        
        supabase.table("order_status_events").insert({
            "order_id": order_id,
            "status": "assigned"
        }).execute()
        
        updated = supabase.table("orders").select("*").eq("id", order_id).execute()
        return updated.data[0]
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error accepting delivery order: {e}")
        raise HTTPException(status_code=500, detail="Failed to accept delivery order")