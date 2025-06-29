"""
Unit tests for CRUD operations.
"""

import pytest
from sqlalchemy.orm import Session

from app.crud import (
    get_user_by_id,
    get_user_by_email,
    get_user_by_username,
    create_user,
    update_user,
    delete_user,
    get_item_by_id,
    create_item,
    update_item,
    delete_item,
    get_items,
    get_items_count,
)
from app.schemas import UserCreate, UserUpdate, ItemCreate, ItemUpdate


class TestUserCRUD:
    """Test user CRUD operations."""
    
    def test_create_user(self, db_session):
        """Test creating a new user."""
        user_data = UserCreate(
            email="newuser@example.com",
            username="newuser",
            password="newpassword",
            full_name="New User",
        )
        
        user = create_user(db_session, user_data)
        
        assert user.email == user_data.email
        assert user.username == user_data.username
        assert user.full_name == user_data.full_name
        assert user.id is not None
    
    def test_get_user_by_id(self, db_session, test_user):
        """Test getting user by ID."""
        user = get_user_by_id(db_session, test_user.id)
        assert user is not None
        assert user.id == test_user.id
        assert user.email == test_user.email
    
    def test_get_user_by_id_not_found(self, db_session):
        """Test getting user by non-existent ID."""
        user = get_user_by_id(db_session, 999)
        assert user is None
    
    def test_get_user_by_email(self, db_session, test_user):
        """Test getting user by email."""
        user = get_user_by_email(db_session, test_user.email)
        assert user is not None
        assert user.email == test_user.email
    
    def test_get_user_by_email_not_found(self, db_session):
        """Test getting user by non-existent email."""
        user = get_user_by_email(db_session, "nonexistent@example.com")
        assert user is None
    
    def test_get_user_by_username(self, db_session, test_user):
        """Test getting user by username."""
        user = get_user_by_username(db_session, test_user.username)
        assert user is not None
        assert user.username == test_user.username
    
    def test_get_user_by_username_not_found(self, db_session):
        """Test getting user by non-existent username."""
        user = get_user_by_username(db_session, "nonexistent")
        assert user is None
    
    def test_update_user(self, db_session, test_user):
        """Test updating user information."""
        update_data = UserUpdate(
            full_name="Updated Name",
            email="updated@example.com",
        )
        
        updated_user = update_user(db_session, test_user.id, update_data)
        
        assert updated_user is not None
        assert updated_user.full_name == "Updated Name"
        assert updated_user.email == "updated@example.com"
    
    def test_update_user_not_found(self, db_session):
        """Test updating non-existent user."""
        update_data = UserUpdate(full_name="Updated Name")
        updated_user = update_user(db_session, 999, update_data)
        assert updated_user is None
    
    def test_delete_user(self, db_session, test_user):
        """Test deleting user."""
        success = delete_user(db_session, test_user.id)
        assert success is True
        
        # Verify user is deleted
        user = get_user_by_id(db_session, test_user.id)
        assert user is None
    
    def test_delete_user_not_found(self, db_session):
        """Test deleting non-existent user."""
        success = delete_user(db_session, 999)
        assert success is False


class TestItemCRUD:
    """Test item CRUD operations."""
    
    def test_create_item(self, db_session, test_user):
        """Test creating a new item."""
        item_data = ItemCreate(
            title="New Item",
            description="New Description",
            price=200,
        )
        
        item = create_item(db_session, item_data, test_user.id)
        
        assert item.title == item_data.title
        assert item.description == item_data.description
        assert item.price == item_data.price
        assert item.owner_id == test_user.id
        assert item.id is not None
    
    def test_get_item_by_id(self, db_session, test_item):
        """Test getting item by ID."""
        item = get_item_by_id(db_session, test_item.id)
        assert item is not None
        assert item.id == test_item.id
        assert item.title == test_item.title
    
    def test_get_item_by_id_not_found(self, db_session):
        """Test getting item by non-existent ID."""
        item = get_item_by_id(db_session, 999)
        assert item is None
    
    def test_update_item(self, db_session, test_item):
        """Test updating item information."""
        update_data = ItemUpdate(
            title="Updated Item",
            price=300,
        )
        
        updated_item = update_item(db_session, test_item.id, update_data)
        
        assert updated_item is not None
        assert updated_item.title == "Updated Item"
        assert updated_item.price == 300
        assert updated_item.description == test_item.description  # Unchanged
    
    def test_update_item_not_found(self, db_session):
        """Test updating non-existent item."""
        update_data = ItemUpdate(title="Updated Item")
        updated_item = update_item(db_session, 999, update_data)
        assert updated_item is None
    
    def test_delete_item(self, db_session, test_item):
        """Test deleting item."""
        success = delete_item(db_session, test_item.id)
        assert success is True
        
        # Verify item is deleted
        item = get_item_by_id(db_session, test_item.id)
        assert item is None
    
    def test_delete_item_not_found(self, db_session):
        """Test deleting non-existent item."""
        success = delete_item(db_session, 999)
        assert success is False
    
    def test_get_items(self, db_session, test_user):
        """Test getting items with pagination."""
        # Create multiple items
        for i in range(5):
            item_data = ItemCreate(
                title=f"Item {i}",
                description=f"Description {i}",
                price=100 + i,
            )
            create_item(db_session, item_data, test_user.id)
        
        items = get_items(db_session, skip=0, limit=3)
        assert len(items) == 3
        
        items = get_items(db_session, skip=3, limit=3)
        assert len(items) == 2
    
    def test_get_items_by_owner(self, db_session, test_user):
        """Test getting items by owner."""
        # Create items for test_user
        for i in range(3):
            item_data = ItemCreate(
                title=f"User Item {i}",
                description=f"Description {i}",
                price=100 + i,
            )
            create_item(db_session, item_data, test_user.id)
        
        items = get_items(db_session, owner_id=test_user.id)
        assert len(items) == 3
        assert all(item.owner_id == test_user.id for item in items)
    
    def test_get_items_count(self, db_session, test_user):
        """Test getting items count."""
        # Create multiple items
        for i in range(5):
            item_data = ItemCreate(
                title=f"Item {i}",
                description=f"Description {i}",
                price=100 + i,
            )
            create_item(db_session, item_data, test_user.id)
        
        total_count = get_items_count(db_session)
        assert total_count == 5
        
        user_count = get_items_count(db_session, owner_id=test_user.id)
        assert user_count == 5 