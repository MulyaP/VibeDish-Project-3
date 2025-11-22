# app/routers/me.py
from fastapi import APIRouter, Depends, HTTPException
from ..db import get_db
from ..auth import current_user

router = APIRouter(prefix="/me", tags=["me"])

@router.get("")
def get_me(user=Depends(current_user)):
    supabase = get_db()
    response = supabase.table("users").select("id,email,name,role").eq("id", user["id"]).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="user not found")
    return response.data[0]

@router.patch("")
def patch_me(payload: dict, user=Depends(current_user)):
    supabase = get_db()
    update_data = {}
    if payload.get("name"):
        update_data["name"] = payload["name"]
    
    response = supabase.table("users").update(update_data).eq("id", user["id"]).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="user not found")
    return response.data[0]
