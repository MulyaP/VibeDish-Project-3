from fastapi import APIRouter, Depends, HTTPException
from .auth import require_owner
from ..db import get_db

router = APIRouter()

@router.get("")
async def get_my_restaurant(user: dict = Depends(require_owner)):
    try:
        db = get_db()
        result = db.table("restaurants").select("name, address").eq("owner_id", user["id"]).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="No restaurant found for this owner")
         
        return result.data[0]
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch restaurant details: {str(e)}")
