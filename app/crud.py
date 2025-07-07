"""
CRUD operations for database interactions.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models import User, Item
from app.schemas import UserCreate, UserUpdate, ItemCreate, ItemUpdate
from app.auth import get_password_hash

# User CRUD operations
def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """Get user by ID."""
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get user by email."""
    return db.query(User).filter(User.email == email).first()

def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """Get user by username."""
    return db.query(User).filter(User.username == username).first()

def get_users(
    db: Session, skip: int = 0, limit: int = 100
) -> List[User]:
    """Get users with pagination."""
    return db.query(User).offset(skip).limit(limit).all()

def create_user(db: Session, user: UserCreate) -> User:
    """Create a new user."""
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        username=user.username,
        hashed_password=hashed_password,
        full_name=user.full_name,
        is_active=user.is_active,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user(db: Session, user_id: int, user_update: UserUpdate) -> Optional[User]:
    """Update user information."""
    db_user = get_user_by_id(db, user_id)
    if not db_user:
        return None

    update_data = user_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_user, field, value)

    db.commit()
    db.refresh(db_user)
    return db_user

def delete_user(db: Session, user_id: int) -> bool:
    """Delete a user."""
    db_user = get_user_by_id(db, user_id)
    if not db_user:
        return False

    db.delete(db_user)
    db.commit()
    return True

# Item CRUD operations
def get_item_by_id(db: Session, item_id: int) -> Optional[Item]:
    """Get item by ID."""
    return db.query(Item).filter(Item.id == item_id).first()

def get_items(
    db: Session, skip: int = 0, limit: int = 100, owner_id: Optional[int] = None
) -> List[Item]:
    """Get items with pagination and optional owner filter."""
    query = db.query(Item)
    if owner_id is not None:
        query = query.filter(Item.owner_id == owner_id)
    return query.offset(skip).limit(limit).all()

def get_items_count(db: Session, owner_id: Optional[int] = None) -> int:
    """Get total count of items."""
    query = db.query(func.count(Item.id))
    if owner_id is not None:
        query = query.filter(Item.owner_id == owner_id)
    return query.scalar()

def create_item(db: Session, item: ItemCreate, owner_id: int) -> Item:
    """Create a new item."""
    db_item = Item(**item.dict(), owner_id=owner_id)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

def update_item(db: Session, item_id: int, item_update: ItemUpdate) -> Optional[Item]:
    """Update item information."""
    db_item = get_item_by_id(db, item_id)
    if not db_item:
        return None

    update_data = item_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_item, field, value)

    db.commit()
    db.refresh(db_item)
    return db_item

def delete_item(db: Session, item_id: int) -> bool:
    """Delete an item."""
    db_item = get_item_by_id(db, item_id)
    if not db_item:
        return False

    db.delete(db_item)
    db.commit()
    return True

def get_user_items(
    db: Session, user_id: int, skip: int = 0, limit: int = 100
) -> List[Item]:
    """Get items owned by a specific user."""
    return get_items(db, skip=skip, limit=limit, owner_id=user_id)
