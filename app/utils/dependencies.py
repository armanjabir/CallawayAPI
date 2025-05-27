from fastapi import Depends, HTTPException
from app.utils.auth import get_current_user

ALLOWED_COLLECTIONS = ["travismathews", "ogios", "softgoods", "hardgoods"]

def verify_collection_access(collection_name: str, current_user=Depends(get_current_user)):
    if collection_name not in ALLOWED_COLLECTIONS:
        raise HTTPException(status_code=404, detail="Collection not found")
    return (collection_name, current_user)