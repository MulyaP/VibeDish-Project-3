# app/routers/addresses.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from ..db import get_db
from ..auth import current_user

router = APIRouter(prefix="/addresses", tags=["addresses"])

class AddressCreate(BaseModel):
    label: Optional[str] = None
    line1: str
    line2: Optional[str] = None
    city: str
    state: str
    zip: str
    is_default: bool = False

class AddressUpdate(BaseModel):
    label: Optional[str] = None
    line1: Optional[str] = None
    line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip: Optional[str] = None
    is_default: Optional[bool] = None

@router.get("")
def list_addresses(user=Depends(current_user)):
    supabase = get_db()
    response = supabase.table("addresses").select("*").eq("user_id", user["id"]).order("created_at", desc=True).execute()
    return response.data

@router.post("")
def create_address(body: AddressCreate, user=Depends(current_user)):
    supabase = get_db()
    if body.is_default:
        supabase.table("addresses").update({"is_default": False}).eq("user_id", user["id"]).execute()
    
    data = {"user_id": user["id"], **body.model_dump()}
    response = supabase.table("addresses").insert(data).execute()
    return response.data[0]

@router.patch("/{addr_id}")
def update_address(addr_id: str, body: AddressUpdate, user=Depends(current_user)):
    supabase = get_db()
    check = supabase.table("addresses").select("id").eq("id", addr_id).eq("user_id", user["id"]).execute()
    if not check.data:
        raise HTTPException(status_code=404, detail="address not found")
    
    if body.is_default is True:
        supabase.table("addresses").update({"is_default": False}).eq("user_id", user["id"]).neq("id", addr_id).execute()
    
    update_data = {k: v for k, v in body.model_dump().items() if v is not None}
    response = supabase.table("addresses").update(update_data).eq("id", addr_id).eq("user_id", user["id"]).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="address not found")
    return response.data[0]

@router.delete("/{addr_id}")
def delete_address(addr_id: str, user=Depends(current_user)):
    supabase = get_db()
    response = supabase.table("addresses").delete().eq("id", addr_id).eq("user_id", user["id"]).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="address not found")
    return {"deleted": addr_id}
