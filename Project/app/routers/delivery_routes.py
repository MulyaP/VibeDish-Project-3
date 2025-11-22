import httpx
from fastapi import APIRouter, HTTPException, status, Depends, Header, Query
import os
import asyncio
from dotenv import load_dotenv
from app.models.delivery_models import Location
from app.db import get_db

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
    
    coordinates = [[src_lng, src_lat]] + [[c["lng"], c["lat"]] for c in chunk]
    coordinates_str = ";".join(f"{lng},{lat}" for lng, lat in coordinates)
    destinations_idx = ";".join(str(i) for i in range(1, len(coordinates)))

    params = {
        "access_token": MAPBOX_TOKEN,
        "sources": "0",
        "destinations": destinations_idx,
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
        print(f"URL: {url}")
        print(f"Params: {params}")
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
            distances_matrix[0]
            if distances_matrix and len(distances_matrix) > 0
            else [None] * len(chunk)
        )
        durations_from_source = (
            durations_matrix[0]
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