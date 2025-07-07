"""
Items endpoints for CRUD operations.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth import get_current_active_user
from app.crud import (
    create_item,
    delete_item,
    get_item_by_id,
    get_items,
    get_items_count,
    update_item,
)
from app.database import get_db
from app.models import User
from app.schemas import Item, ItemCreate, ItemUpdate, PaginatedResponse

router = APIRouter()


@router.get("/", response_model=PaginatedResponse)
async def read_items(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of items to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get paginated list of items."""
    items = get_items(db, skip=skip, limit=limit)
    total = get_items_count(db)

    pages = (total + limit - 1) // limit
    page = (skip // limit) + 1

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        size=limit,
        pages=pages,
    )


@router.get("/my-items", response_model=List[Item])
async def read_my_items(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of items to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get current user's items."""
    items = get_items(db, skip=skip, limit=limit, owner_id=current_user.id)
    return items


@router.get("/{item_id}", response_model=Item)
async def read_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get a specific item by ID."""
    item = get_item_by_id(db, item_id=item_id)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
        )
    return item


@router.post("/", response_model=Item, status_code=status.HTTP_201_CREATED)
async def create_new_item(
    item: ItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new item."""
    return create_item(db=db, item=item, owner_id=current_user.id)


@router.put("/{item_id}", response_model=Item)
async def update_existing_item(
    item_id: int,
    item_update: ItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update an existing item."""
    # Check if item exists and belongs to current user
    existing_item = get_item_by_id(db, item_id=item_id)
    if existing_item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
        )

    if existing_item.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    updated_item = update_item(db=db, item_id=item_id, item_update=item_update)
    return updated_item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete an existing item."""
    # Check if item exists and belongs to current user
    existing_item = get_item_by_id(db, item_id=item_id)
    if existing_item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
        )

    if existing_item.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    success = delete_item(db=db, item_id=item_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete item",
        )
