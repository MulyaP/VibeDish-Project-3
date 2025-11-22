# app/routers/auth_routes.py
import httpx
from fastapi import APIRouter, HTTPException, status, Depends, Header
from pydantic import BaseModel, EmailStr
from typing import Optional

from ..config import settings
from ..db import get_db
from ..auth import current_user

router = APIRouter(prefix="/auth", tags=["auth"])

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    name: str
    role: str

class OwnerSignupRequest(BaseModel):
    email: EmailStr
    password: str
    name: str
    restaurant_name: str
    restaurant_address: str
    latitude: float
    longitude: float

class RefreshRequest(BaseModel):
    refresh_token: str

def ensure_app_user(*, user_id: str, email: str, name: Optional[str] = None) -> None:
    supabase = get_db()
    response = supabase.table("users").select("id").eq("id", user_id).execute()
    if response.data:
        update_data = {"email": email}
        if name:
            update_data["name"] = name
        supabase.table("users").update(update_data).eq("id", user_id).execute()
        return
    
    response = supabase.table("users").select("id").eq("email", email).execute()
    if response.data:
        update_data = {"email": email}
        if name:
            update_data["name"] = name
        supabase.table("users").update(update_data).eq("email", email).execute()
        return
    
    supabase.table("users").insert({"id": user_id, "email": email, "name": name, "role": "customer"}).execute()

def _extract_bearer_token(authorization: Optional[str]) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing bearer token")
    return authorization.split(" ", 1)[1].strip()

@router.post("/signup")
async def signup(payload: SignupRequest):
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.post(
            f"{settings.SUPABASE_URL}/auth/v1/signup",
            headers={"apikey": settings.SUPABASE_ANON_KEY or "", "Content-Type": "application/json"},
            json={"email": payload.email, "password": payload.password, "data": {"name": payload.name}},
        )
    if r.status_code >= 400:
        try:
            err = r.json()
        except Exception:
            err = {"message": r.text}
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err)

    data = r.json()
    user_id = data.get("id") or (data.get("user") or {}).get("id")
    user_email = data.get("email") or (data.get("user") or {}).get("email")

    if not user_id or not user_email:
        raise HTTPException(status_code=500, detail="unexpected signup response from auth provider")

    try:
        supabase = get_db()
        existing = supabase.table("users").select("id").eq("id", user_id).execute()
        if existing.data:
            supabase.table("users").update({"name": payload.name, "email": user_email}).eq("id", user_id).execute()
        else:
            supabase.table("users").insert({"id": user_id, "email": user_email, "name": payload.name, "role": payload.role}).execute()
    except Exception as e:
        print(f"Error syncing user: {e}")

    return {"id": user_id, "email": user_email, "name": payload.name}

@router.post("/owner/signup")
async def owner_signup(payload: OwnerSignupRequest):
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.post(
            f"{settings.SUPABASE_URL}/auth/v1/signup",
            headers={"apikey": settings.SUPABASE_ANON_KEY or "", "Content-Type": "application/json"},
            json={"email": payload.email, "password": payload.password, "data": {"name": payload.name}},
        )
    if r.status_code >= 400:
        try:
            err = r.json()
        except Exception:
            err = {"message": r.text}
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err)

    data = r.json()
    user_id = data.get("id") or (data.get("user") or {}).get("id")
    user_email = data.get("email") or (data.get("user") or {}).get("email")

    if not user_id or not user_email:
        raise HTTPException(status_code=500, detail="unexpected signup response from auth provider")

    try:
        supabase = get_db()
        existing = supabase.table("users").select("id").eq("id", user_id).execute()
        if existing.data:
            supabase.table("users").update({"name": payload.name, "email": user_email, "role": "owner"}).eq("id", user_id).execute()
        else:
            supabase.table("users").insert({"id": user_id, "email": user_email, "name": payload.name, "role": "owner"}).execute()
        
        restaurant_response = supabase.table("restaurants").insert({
            "name": payload.restaurant_name,
            "address": payload.restaurant_address,
            "owner_id": user_id,
            "latitude": payload.latitude,
            "longitude": payload.longitude
        }).execute()
        
        if not restaurant_response.data:
            raise HTTPException(status_code=500, detail="failed to create restaurant record")
        restaurant_id = restaurant_response.data[0]["id"]
        
        supabase.table("restaurant_staff").insert({"restaurant_id": restaurant_id, "user_id": user_id, "role": "owner"}).execute()
        
        return {
            "id": user_id,
            "email": user_email,
            "name": payload.name,
            "restaurant_id": str(restaurant_id),
            "restaurant_name": payload.restaurant_name
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create owner account: {str(e)}")

@router.post("/login")
async def login(payload: LoginRequest):
    if not payload.email or not payload.password:
        raise HTTPException(status_code=400, detail="email and password required")

    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.post(
            f"{settings.SUPABASE_URL}/auth/v1/token?grant_type=password",
            headers={"apikey": settings.SUPABASE_ANON_KEY or "", "Content-Type": "application/json"},
            json={"email": payload.email, "password": payload.password},
        )
    if r.status_code >= 400:
        raise HTTPException(status_code=400, detail="invalid credentials")

    token_data = r.json()
    access_token = token_data.get("access_token")
    if not access_token:
        raise HTTPException(status_code=400, detail="invalid credentials")

    async with httpx.AsyncClient(timeout=10.0) as client:
        me = await client.get(
            f"{settings.SUPABASE_URL}/auth/v1/user",
            headers={"apikey": settings.SUPABASE_ANON_KEY or "", "Authorization": f"Bearer {access_token}"},
        )
    if me.status_code >= 400:
        raise HTTPException(status_code=400, detail="could not fetch user from supabase")

    me_data = me.json()
    user_id = me_data.get("id")
    user_email = me_data.get("email")
    user_name = (me_data.get("user_metadata") or {}).get("name")

    if not user_id or not user_email:
        raise HTTPException(status_code=400, detail="invalid user data from auth provider")

    ensure_app_user(user_id=user_id, email=user_email, name=user_name)

    return {
        "access_token": access_token,
        "token_type": token_data.get("token_type", "bearer"),
        "refresh_token": token_data.get("refresh_token"),
        "user": {"id": user_id, "email": user_email, "name": user_name},
    }

@router.post("/refresh")
async def refresh_token(body: RefreshRequest):
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.post(
            f"{settings.SUPABASE_URL}/auth/v1/token?grant_type=refresh_token",
            headers={"apikey": settings.SUPABASE_ANON_KEY or "", "Content-Type": "application/json"},
            json={"refresh_token": body.refresh_token}
        )

    if r.status_code != 200:
        try:
            err = r.json()
        except Exception:
            err = {"message": r.text}
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=err.get("message", "refresh failed"))

    return r.json()

@router.post("/logout")
async def logout(authorization: Optional[str] = Header(None)):
    access_token = _extract_bearer_token(authorization)

    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.post(
            f"{settings.SUPABASE_URL}/auth/v1/logout",
            headers={"apikey": settings.SUPABASE_ANON_KEY or "", "Authorization": f"Bearer {access_token}"},
        )

    if r.status_code in (200, 204, 401):
        return {"ok": True}
    try:
        err = r.json()
    except Exception:
        err = {"message": r.text}
    raise HTTPException(status_code=r.status_code, detail=err)

@router.delete("/me")
async def delete_me(user=Depends(current_user)):
    uid = str(user["id"]).strip()

    try:
        supabase = get_db()
        supabase.table("users").delete().eq("id", uid).execute()
    except Exception:
        pass

    if not settings.SUPABASE_SERVICE_ROLE_KEY:
        return {
            "deleted_in_app_db": True,
            "deleted_in_supabase": False,
            "note": "Missing SUPABASE_SERVICE_ROLE_KEY; only local data was removed.",
        }

    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.delete(
            f"{settings.SUPABASE_URL}/auth/v1/admin/users/{uid}",
            headers={
                "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
                "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
            },
        )

    if r.status_code in (200, 204):
        return {"deleted_in_app_db": True, "deleted_in_supabase": True}

    try:
        err = r.json()
    except Exception:
        err = {"message": r.text}
    raise HTTPException(status_code=r.status_code, detail=err)
