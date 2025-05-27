from fastapi import APIRouter, HTTPException
from app.database.connection import db  
from fastapi import APIRouter, HTTPException, Body
from datetime import datetime

from app.database.connection import db
from datetime import datetime
from app.schemas.user import UserCreate,UserInDB
from app.utils.auth import hash_password
from fastapi import Depends, HTTPException, status
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


# @router.post("/create_user")
# def create_user(user: UserCreate):
#     users_collection = db["users"]

#     # Check if the email already exists
#     if users_collection.find_one({"email": user.email}):
#         raise HTTPException(status_code=400, detail="Email already registered.")

#     # Get the next available ID (auto-increment logic)
#     last_user = users_collection.find_one(sort=[("id", -1)])
#     next_id = (last_user["id"] + 1) if last_user and "id" in last_user else 1

#     user_data = user.dict()
#     user_data["id"] = next_id  #  assign custom ID
#     user_data["createdAt"] = datetime.utcnow()
#     user_data["updatedAt"] = datetime.utcnow()

#     try:
#         users_collection.insert_one(user_data)
#         # Remove MongoDB's _id from response if you want
#         user_data.pop("_id", None)
#         return {
#             "message": "User created successfully.",
#             "user": user_data
#         }
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

    

@router.post("/create_user")
def create_user(user: UserCreate):
    users_collection = db["users"]

    if users_collection.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="Email already registered.")

    last_user = users_collection.find_one(sort=[("id", -1)])
    next_id = (last_user["id"] + 1) if last_user and "id" in last_user else 1

    user_data = user.dict()
    plain_password = user_data.pop("password")  # Remove plain password from dict
    user_data["password_hash"] = hash_password(plain_password)  # Hash password here

    user_data["id"] = next_id
    user_data["createdAt"] = datetime.utcnow()
    user_data["updatedAt"] = datetime.utcnow()

    try:
        users_collection.insert_one(user_data)
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





from fastapi import APIRouter, HTTPException, Depends
from ..schemas.user import LoginRequest, LoginResponse
from ..utils.auth import verify_password
from ..database.connection import users_collection
import time




# @router.post("/login", response_model=LoginResponse)
# def login(payload: LoginRequest):
#     user = users_collection.find_one({"email": payload.email})

#     if not user:
#         raise HTTPException(status_code=404, detail="User not found")

#     if not user.get("password_hash"):
#         raise HTTPException(status_code=400, detail="User has no password set")

#     if not verify_password(payload.password, user["password_hash"]):
#         raise HTTPException(status_code=401, detail="Invalid password")

#     return LoginResponse(
#         message="Login successful",
#         user_id=str(user["_id"]),
#         name=user.get("name", ""),
#         email=user["email"]
#     )

# role based 
from fastapi import APIRouter, HTTPException, Depends, Header
from app.database.connection import db
from app.utils.auth import verify_password
from pydantic import BaseModel
import time
from fastapi import APIRouter, Depends, HTTPException
from app.database.connection import db
from app.utils.auth import get_current_user
from fastapi import APIRouter, HTTPException
from app.database.connection import db
from app.utils.auth import verify_password, create_access_token
from pydantic import BaseModel
from fastapi import Security
from fastapi.security import OAuth2PasswordBearer
from fastapi import Query

# @router.post("/login", response_model=LoginResponse)
# def login(payload: LoginRequest):
#     user = db["users"].find_one({"email": payload.email})
#     if not user:
#         raise HTTPException(status_code=404, detail="User not found")
#     if not user.get("password_hash"):
#         raise HTTPException(status_code=400, detail="User has no password set")
#     if not verify_password(payload.password, user["password_hash"]):
#         raise HTTPException(status_code=401, detail="Invalid password")

#     access_token = create_access_token(data={"sub": user["email"]})

#     return LoginResponse(
#         message="Login successful",
#         user_id=str(user["_id"]),
#         name=user.get("name", ""),
#         email=user["email"],
#         access_token=access_token,
#         token_type="bearer"  # Usually "bearer" for JWT tokens
#     )

# # ✅ Admin-only protected collections route

# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# @router.get("/collections/{collection_name}")
# def get_collection_data(collection_name: str, current_user: dict = Depends(get_current_admin_user)):
# # your existing code here
    
#     allowed_collections = ["travismathews", "ogios", "softgoods", "hardgoods"]
#     if collection_name not in allowed_collections:
#         raise HTTPException(status_code=404, detail="Collection not found")

#     data = list(db[collection_name].find({}, {"_id": 0}))
#     return {"collection": collection_name, "data": data}


# --- app/routes/user.py ---
from fastapi import APIRouter, HTTPException
from app.schemas.user import LoginRequest, LoginResponse
from app.utils.auth import verify_password, create_access_token
from app.database.connection import db
from bson import ObjectId



@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest):
    user = db["users"].find_one({"email": payload.email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.get("password_hash"):
        raise HTTPException(status_code=400, detail="User has no password set")
    if not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid password")

    access_token = create_access_token(data={"sub": user["email"]})

    return LoginResponse(
        message="Login successful",
        id=user.get("id"),
        name=user.get("name", ""),
        email=user["email"],
        phone=user.get("phone"),
        phone2=user.get("phone2"),
        role=user.get("role"),
        code=user.get("code"),
        manager_id=user.get("manager_id"),
        designation=user.get("designation"),
        gstin=user.get("gstin"),
        address=user.get("address"),
        secondary_email=user.get("secondary_email"),
        status=user.get("status"),
        access_token=access_token,
        token_type="bearer"
    )

from fastapi import Depends
from app.utils.auth import get_current_user  # adjust import path to match your structure
from app.schemas.user import ManagerPayload
from bson import ObjectId
@router.post("/get-retailer-associated")
def get_retailer_associated(
    payload: ManagerPayload,
    current_user: dict = Depends(get_current_user)
):
    manager_id = payload.manager_id
    print("Received manager_id:", manager_id)

    if not manager_id:
        raise HTTPException(status_code=400, detail="manager_id is required")

    retailers = list(db["users"].find(
        {"manager_id": manager_id, "role": "Retailer"},
        {"_id": 0}
    ))
    print("Found retailers:", retailers)

    if not retailers:
        raise HTTPException(status_code=404, detail="No retailers found")

    return {"retailers": retailers}




@router.post("/update-user-details")
def update_user_details(payload: dict, current_user: dict = Depends(get_current_user)):
    user_id = payload.get("id")

    if not user_id:
        raise HTTPException(status_code=400, detail="User ID is required")

    if current_user["id"] != user_id:
        raise HTTPException(status_code=403, detail="You can only update your own profile")

    result = db["users"].update_one({"id": user_id}, {"$set": payload})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")

    updated_user = db["users"].find_one({"id": user_id}, {"password_hash": 0})

    # Convert ObjectId to string
    if "_id" in updated_user:
        updated_user["_id"] = str(updated_user["_id"])

    return {"message": "User updated", "user": updated_user}
