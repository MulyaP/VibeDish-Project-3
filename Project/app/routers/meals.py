# app/routers/meals.py
from fastapi import APIRouter, HTTPException, Query
from ..db import get_db

router = APIRouter()

@router.get("")
def list_meals(
    surplus_only: bool = Query(default=True),
    limit: int = Query(default=50, le=100),
):
    try:
        supabase = get_db()
        query = supabase.table("meals").select("*")
        
        if surplus_only:
            query = query.gt("quantity", 0)
        
        query = query.order("created_at", desc=True).limit(limit)
        response = query.execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB error: {e}")
