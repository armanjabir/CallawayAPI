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
    password: str

class UserInDB(UserCreate):
    id: Optional[str] = Field(alias="_id")
    createdAt: datetime
    updatedAt: datetime


# class LoginRequest(BaseModel):
#     email: EmailStr
#     password: str

# class LoginResponse(BaseModel):
#     message: str
#     user_id: str
#     name: Optional[str]
#     email: EmailStr
#     access_token: str
#     token_type: str


from pydantic import BaseModel, EmailStr
from typing import Optional

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    message: str
    id: str
    name: Optional[str] = None
    email: EmailStr
    phone: Optional[str] = None
    phone2: Optional[str] = None
    role: Optional[str] = None
    code: Optional[str] = None
    manager_id: Optional[int] = None
    designation: Optional[str] = None
    gstin: Optional[str] = None
    address: Optional[str] = None
    secondary_email: Optional[EmailStr] = None
    status: Optional[str] = None
    access_token: str
    token_type: str


class ManagerPayload(BaseModel):
    manager_id: int  # or str, depending on your DB