# backend/app/schemas/auth.py

from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: Optional[EmailStr] = None # Email is optional for now
    password: str = Field(..., min_length=6)

class UserLogin(BaseModel):
    username: str
    password: str

class UserInDB(BaseModel):
    # Model for user data as stored in the database, without the raw password
    id: int
    username: str
    email: Optional[EmailStr] = None
    hashed_password: str
    is_active: bool
    is_admin: bool

    class Config:
        from_attributes = True # Changed from orm_mode = True in Pydantic v2

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    username: Optional[str] = None
    scopes: list[str] = []