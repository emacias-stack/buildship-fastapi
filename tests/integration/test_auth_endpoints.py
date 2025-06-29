"""
Integration tests for authentication endpoints.
"""

import pytest
from fastapi import status


class TestAuthEndpoints:
    """Test authentication endpoints integration."""
    
    def test_register_user_success(self, client):
        """Test successful user registration."""
        user_data = {
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "newpassword123",
            "full_name": "New User",
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["email"] == user_data["email"]
        assert data["username"] == user_data["username"]
        assert data["full_name"] == user_data["full_name"]
        assert "password" not in data
        assert data["id"] is not None
    
    def test_register_user_duplicate_email(self, client, test_user):
        """Test registration with duplicate email."""
        user_data = {
            "email": test_user.email,
            "username": "differentuser",
            "password": "password123",
            "full_name": "Different User",
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Email already registered" in response.json()["detail"]
    
    def test_register_user_duplicate_username(self, client, test_user):
        """Test registration with duplicate username."""
        user_data = {
            "email": "different@example.com",
            "username": test_user.username,
            "password": "password123",
            "full_name": "Different User",
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Username already taken" in response.json()["detail"]
    
    def test_register_user_invalid_data(self, client):
        """Test registration with invalid data."""
        user_data = {
            "email": "invalid-email",
            "username": "ab",  # Too short
            "password": "123",  # Too short
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_login_success(self, client, test_user):
        """Test successful login."""
        login_data = {
            "username": test_user.username,
            "password": "testpassword",
        }
        
        response = client.post("/api/v1/auth/token", data=login_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 0
    
    def test_login_invalid_username(self, client):
        """Test login with invalid username."""
        login_data = {
            "username": "nonexistent",
            "password": "password123",
        }
        
        response = client.post("/api/v1/auth/token", data=login_data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Incorrect username or password" in response.json()["detail"]
    
    def test_login_invalid_password(self, client, test_user):
        """Test login with invalid password."""
        login_data = {
            "username": test_user.username,
            "password": "wrongpassword",
        }
        
        response = client.post("/api/v1/auth/token", data=login_data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Incorrect username or password" in response.json()["detail"]
    
    def test_get_current_user_success(self, client, auth_headers):
        """Test getting current user with valid token."""
        response = client.get("/api/v1/auth/me", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
        assert "password" not in data
    
    def test_get_current_user_invalid_token(self, client):
        """Test getting current user with invalid token."""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/api/v1/auth/me", headers=headers)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_current_user_no_token(self, client):
        """Test getting current user without token."""
        response = client.get("/api/v1/auth/me")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_token_lifecycle(self, client, test_user):
        """Test complete token lifecycle."""
        # 1. Register user
        user_data = {
            "email": "lifecycle@example.com",
            "username": "lifecycle",
            "password": "password123",
            "full_name": "Lifecycle User",
        }
        register_response = client.post("/api/v1/auth/register", json=user_data)
        assert register_response.status_code == status.HTTP_201_CREATED
        
        # 2. Login to get token
        login_data = {
            "username": "lifecycle",
            "password": "password123",
        }
        login_response = client.post("/api/v1/auth/token", data=login_data)
        assert login_response.status_code == status.HTTP_200_OK
        token = login_response.json()["access_token"]
        
        # 3. Use token to access protected endpoint
        headers = {"Authorization": f"Bearer {token}"}
        me_response = client.get("/api/v1/auth/me", headers=headers)
        assert me_response.status_code == status.HTTP_200_OK
        assert me_response.json()["username"] == "lifecycle" 