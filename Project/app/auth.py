# app/auth.py
from typing import Any, Dict, Optional

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt, JWTError
from .config import settings
from .db import get_db

security = HTTPBearer()

SUPABASE_USERINFO_URL = settings.SUPABASE_URL.rstrip("/") + "/auth/v1/user"


async def _get_user_from_supabase(token: str) -> Dict[str, Any]:
    """
    Remote-verify the token by calling Supabase.
    This bypasses the whole "HS256 vs EC vs JWKS" mess.
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "apikey": settings.SUPABASE_ANON_KEY,
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(SUPABASE_USERINFO_URL, headers=headers)

    if r.status_code != 200:
        # bubble up error
        try:
            data = r.json()
        except Exception:
            data = {"message": r.text}
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Supabase auth failed: {data}",
        )

    return r.json()


def _try_decode_local_hs256(token: str) -> Optional[Dict[str, Any]]:
    """
    Try to decode using legacy HS256 secret (for your earlier hand-made tokens).
    If it fails, just return None so we can fall back to remote check.
    """
    if not settings.SUPABASE_JWT_SECRET:
        return None
    try:
        claims = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated",
        )
        return claims
    except JWTError:
        return None


async def current_user(
    creds: HTTPAuthorizationCredentials = Depends(security),
):
    token = creds.credentials

    # 1) try local HS256 (for your old dev tokens)
    claims = _try_decode_local_hs256(token)
    if claims is not None:
        sub = claims.get("sub")
        if not sub:
            raise HTTPException(status_code=401, detail="JWT missing sub")
        return {
            "id": str(sub),
            "email": claims.get("email"),
            "role": claims.get("role"),
            "raw": claims,
            "source": "local-hs256",
        }

    # 2) fallback: ask Supabase directly
    userinfo = await _get_user_from_supabase(token)

    # Supabase returns {id, email, ...}
    uid = userinfo.get("id") or userinfo.get("sub")
    if not uid:
        raise HTTPException(status_code=401, detail="Supabase user has no id")

    return {
        "id": str(uid),
        "email": userinfo.get("email"),
        "role": userinfo.get("role", "authenticated"),
        "raw": userinfo,
        "source": "supabase-remote",
    }

def ensure_app_user(
    *,
    user_id: str,
    email: str,
    name: str | None = None,
):
    supabase = get_db()
    
    # 1) try by id
    response = supabase.table("users").select("id").eq("id", user_id).execute()
    if response.data:
        # update basic fields
        update_data = {"email": email}
        if name:
            update_data["name"] = name
        supabase.table("users").update(update_data).eq("id", user_id).execute()
        return
    
    # 2) try by email (old row before we synced with supabase)
    response = supabase.table("users").select("id").eq("email", email).execute()
    if response.data:
        # relink this app user to the real supabase id
        update_data = {"id": user_id}
        if name:
            update_data["name"] = name
        supabase.table("users").update(update_data).eq("email", email).execute()
        return
    
    # 3) neither exists → clean insert
    supabase.table("users").insert({
        "id": user_id,
        "email": email,
        "name": name,
        "role": "customer"
    }).execute()