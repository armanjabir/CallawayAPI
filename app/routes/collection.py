from fastapi import APIRouter, Depends
from app.database.connection import db
from app.utils.dependencies import verify_collection_access

router = APIRouter()

@router.get("/collections/{collection_name}")
def get_collection_data(data=Depends(verify_collection_access)):
    collection_name, current_user = data
    data = list(db[collection_name].find({}, {"_id": 0}))
    return {
        "message": f"Data fetched for {current_user['email']}",
        "collection": collection_name,
        "data": data
    }