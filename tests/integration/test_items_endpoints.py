"""
Integration tests for items endpoints.
"""

import pytest
from fastapi import status


class TestItemsEndpoints:
    """Test items endpoints integration."""
    
    def test_create_item_success(self, client, auth_headers):
        """Test successful item creation."""
        item_data = {
            "title": "New Test Item",
            "description": "A test item description",
            "price": 150,
        }
        
        response = client.post("/api/v1/items/", json=item_data, headers=auth_headers)
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["title"] == item_data["title"]
        assert data["description"] == item_data["description"]
        assert data["price"] == item_data["price"]
        assert data["id"] is not None
        assert data["owner"]["username"] == "testuser"
    
    def test_create_item_unauthorized(self, client):
        """Test item creation without authentication."""
        item_data = {
            "title": "New Test Item",
            "description": "A test item description",
            "price": 150,
        }
        
        response = client.post("/api/v1/items/", json=item_data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_create_item_invalid_data(self, client, auth_headers):
        """Test item creation with invalid data."""
        item_data = {
            "title": "",  # Empty title
            "price": -10,  # Negative price
        }
        
        response = client.post("/api/v1/items/", json=item_data, headers=auth_headers)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_get_items_paginated(self, client, auth_headers, test_user, db_session):
        """Test getting paginated items."""
        # Create multiple items
        from app.crud import create_item
        from app.schemas import ItemCreate
        
        for i in range(5):
            item_data = ItemCreate(
                title=f"Item {i}",
                description=f"Description {i}",
                price=100 + i,
            )
            create_item(db_session, item_data, test_user.id)
        
        response = client.get("/api/v1/items/?skip=0&limit=3", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["items"]) == 3
        assert data["total"] == 5
        assert data["page"] == 1
        assert data["size"] == 3
        assert data["pages"] == 2
    
    def test_get_my_items(self, client, auth_headers, test_user, db_session):
        """Test getting current user's items."""
        # Create items for test_user
        from app.crud import create_item
        from app.schemas import ItemCreate
        
        for i in range(3):
            item_data = ItemCreate(
                title=f"My Item {i}",
                description=f"Description {i}",
                price=100 + i,
            )
            create_item(db_session, item_data, test_user.id)
        
        response = client.get("/api/v1/items/my-items", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 3
        assert all(item["owner"]["id"] == test_user.id for item in data)
    
    def test_get_item_by_id_success(self, client, auth_headers, test_item):
        """Test getting item by ID."""
        response = client.get(f"/api/v1/items/{test_item.id}", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == test_item.id
        assert data["title"] == test_item.title
        assert data["description"] == test_item.description
        assert data["price"] == test_item.price
    
    def test_get_item_by_id_not_found(self, client, auth_headers):
        """Test getting non-existent item."""
        response = client.get("/api/v1/items/999", headers=auth_headers)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "Item not found" in response.json()["detail"]
    
    def test_update_item_success(self, client, auth_headers, test_item):
        """Test successful item update."""
        update_data = {
            "title": "Updated Item Title",
            "price": 250,
        }
        
        response = client.put(
            f"/api/v1/items/{test_item.id}",
            json=update_data,
            headers=auth_headers,
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["title"] == "Updated Item Title"
        assert data["price"] == 250
        assert data["description"] == test_item.description  # Unchanged
    
    def test_update_item_not_found(self, client, auth_headers):
        """Test updating non-existent item."""
        update_data = {"title": "Updated Title"}
        
        response = client.put(
            "/api/v1/items/999",
            json=update_data,
            headers=auth_headers,
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "Item not found" in response.json()["detail"]
    
    def test_update_item_unauthorized(self, client, auth_headers, test_item, db_session):
        """Test updating item owned by another user."""
        # Create another user and item
        from app.models import User
        from app.auth import get_password_hash
        from app.crud import create_item
        from app.schemas import ItemCreate
        
        other_user = User(
            email="other@example.com",
            username="otheruser",
            hashed_password=get_password_hash("password"),
            full_name="Other User",
        )
        db_session.add(other_user)
        db_session.commit()
        
        other_item_data = ItemCreate(
            title="Other User's Item",
            description="Description",
            price=100,
        )
        other_item = create_item(db_session, other_item_data, other_user.id)
        
        update_data = {"title": "Unauthorized Update"}
        
        response = client.put(
            f"/api/v1/items/{other_item.id}",
            json=update_data,
            headers=auth_headers,
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Not enough permissions" in response.json()["detail"]
    
    def test_delete_item_success(self, client, auth_headers, test_item):
        """Test successful item deletion."""
        response = client.delete(f"/api/v1/items/{test_item.id}", headers=auth_headers)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify item is deleted
        get_response = client.get(f"/api/v1/items/{test_item.id}", headers=auth_headers)
        assert get_response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_delete_item_not_found(self, client, auth_headers):
        """Test deleting non-existent item."""
        response = client.delete("/api/v1/items/999", headers=auth_headers)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "Item not found" in response.json()["detail"]
    
    def test_delete_item_unauthorized(self, client, auth_headers, db_session):
        """Test deleting item owned by another user."""
        # Create another user and item
        from app.models import User
        from app.auth import get_password_hash
        from app.crud import create_item
        from app.schemas import ItemCreate
        
        other_user = User(
            email="other@example.com",
            username="otheruser",
            hashed_password=get_password_hash("password"),
            full_name="Other User",
        )
        db_session.add(other_user)
        db_session.commit()
        
        other_item_data = ItemCreate(
            title="Other User's Item",
            description="Description",
            price=100,
        )
        other_item = create_item(db_session, other_item_data, other_user.id)
        
        response = client.delete(f"/api/v1/items/{other_item.id}", headers=auth_headers)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Not enough permissions" in response.json()["detail"]
    
    def test_items_crud_lifecycle(self, client, auth_headers):
        """Test complete CRUD lifecycle for items."""
        # 1. Create item
        create_data = {
            "title": "Lifecycle Item",
            "description": "Test lifecycle",
            "price": 100,
        }
        create_response = client.post("/api/v1/items/", json=create_data, headers=auth_headers)
        assert create_response.status_code == status.HTTP_201_CREATED
        item_id = create_response.json()["id"]
        
        # 2. Read item
        read_response = client.get(f"/api/v1/items/{item_id}", headers=auth_headers)
        assert read_response.status_code == status.HTTP_200_OK
        assert read_response.json()["title"] == "Lifecycle Item"
        
        # 3. Update item
        update_data = {"title": "Updated Lifecycle Item", "price": 200}
        update_response = client.put(f"/api/v1/items/{item_id}", json=update_data, headers=auth_headers)
        assert update_response.status_code == status.HTTP_200_OK
        assert update_response.json()["title"] == "Updated Lifecycle Item"
        assert update_response.json()["price"] == 200
        
        # 4. Delete item
        delete_response = client.delete(f"/api/v1/items/{item_id}", headers=auth_headers)
        assert delete_response.status_code == status.HTTP_204_NO_CONTENT
        
        # 5. Verify deletion
        verify_response = client.get(f"/api/v1/items/{item_id}", headers=auth_headers)
        assert verify_response.status_code == status.HTTP_404_NOT_FOUND 