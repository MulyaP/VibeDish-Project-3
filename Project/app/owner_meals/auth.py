from fastapi import Depends, HTTPException
from ..auth import current_user
from ..db import get_db

async def require_owner(user: dict = Depends(current_user), db = Depends(get_db)):
    result = db.table("users").select("role").eq("id", user["id"]).execute()
    
    if not result.data or result.data[0]["role"] != "owner":
        raise HTTPException(status_code=403, detail="Owner role required")
    return user
