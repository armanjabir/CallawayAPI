from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from bson import ObjectId

class UserCreate(BaseModel):
    # id:int
    email: EmailStr
    phone: Optional[str] = None
    phone2: Optional[str] = None
    name: Optional[str] = None
    role: Optional[str] = None
    code: Optional[str] = None
    manager_id: Optional[int] = None
    designation: Optional[str] = None
    gstin: Optional[str] = None
    address: Optional[str] = None
    secondary_email: Optional[EmailStr] = None
    status: Optional[str] = None
    password_hash: Optional[str] = None

class UserInDB(UserCreate):
    id: Optional[str] = Field(alias="_id")
    createdAt: datetime
    updatedAt: datetime

