"""
Pydantic schemas for request/response validation.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field


# User schemas
class UserBase(BaseModel):
    """Base user schema."""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100)
    full_name: Optional[str] = None
    is_active: bool = True


class UserCreate(UserBase):
    """Schema for creating a user."""
    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    """Schema for updating a user."""
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=100)
    full_name: Optional[str] = None
    is_active: Optional[bool] = None


class UserInDB(UserBase):
    """Schema for user in database."""
    id: int
    is_superuser: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class User(UserInDB):
    """Schema for user response."""
    pass


# Item schemas
class ItemBase(BaseModel):
    """Base item schema."""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    price: int = Field(..., gt=0)


class ItemCreate(ItemBase):
    """Schema for creating an item."""
    pass


class ItemUpdate(BaseModel):
    """Schema for updating an item."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    price: Optional[int] = Field(None, gt=0)


class ItemInDB(ItemBase):
    """Schema for item in database."""
    id: int
    owner_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Item(ItemInDB):
    """Schema for item response."""
    owner: User

    class Config:
        from_attributes = True


# Token schemas
class Token(BaseModel):
    """Schema for authentication token."""
    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Schema for token data."""
    username: Optional[str] = None


# Response schemas
class HealthCheck(BaseModel):
    """Schema for health check response."""
    status: str
    timestamp: datetime
    version: str
    database: str


class PaginatedResponse(BaseModel):
    """Schema for paginated responses."""
    items: List[Item]
    total: int
    page: int
    size: int
    pages: int 