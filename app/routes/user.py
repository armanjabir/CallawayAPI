from fastapi import APIRouter, HTTPException
from app.database.connection import db  
from fastapi import APIRouter, HTTPException, Body
from datetime import datetime

from app.database.connection import db
from datetime import datetime
from app.schemas.user import UserCreate,UserInDB

router = APIRouter()
@router.get("/")
def get_all_users():
    try:
        users_collection = db["users"]
        users = list(users_collection.find({}, {"_id": 0}))
        if not users:
            return {"message": "No users found."}
        return {"users": users}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.post("/create_user")
def create_user(user: UserCreate):
    users_collection = db["users"]

    # Check if the email already exists
    if users_collection.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="Email already registered.")

    # Get the next available ID (auto-increment logic)
    last_user = users_collection.find_one(sort=[("id", -1)])
    next_id = (last_user["id"] + 1) if last_user and "id" in last_user else 1

    user_data = user.dict()
    user_data["id"] = next_id  #  assign custom ID
    user_data["createdAt"] = datetime.utcnow()
    user_data["updatedAt"] = datetime.utcnow()

    try:
        users_collection.insert_one(user_data)
        # Remove MongoDB's _id from response if you want
        user_data.pop("_id", None)
        return {
            "message": "User created successfully.",
            "user": user_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
    


#  get user by it's id:

@router.get("/users/{user_id}")
def get_user_by_id(user_id: int):
    users_collection = db["users"]

    user = users_collection.find_one({"id": user_id}, {"_id": 0})  # Exclude MongoDB _id
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    return {"user": user}

# Deleting user by it's id
@router.delete("/users/{user_id}")
def delete_user_by_id(user_id: int):
    users_collection = db["users"]

    # Try to find the user by the `id` field (not MongoDB's _id field)
    result = users_collection.delete_one({"id": user_id})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")

    return {"message": "User deleted successfully"}


# Updating the user by id
@router.put("/users/{user_id}")
def update_user_by_id(user_id: int, user_data: UserCreate):
    users_collection = db["users"]

    existing_user = users_collection.find_one({"id": user_id})
    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found.")

    updated_data = user_data.dict()
    updated_data["updatedAt"] = datetime.utcnow()

    # Optional: ensure `id` stays unchanged
    updated_data["id"] = user_id

    users_collection.update_one({"id": user_id}, {"$set": updated_data})

    return {"message": "User updated successfully", "user": updated_data}