"""
Integration tests for authentication endpoints.
"""

import pytest
from fastapi import status, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.v1.endpoints import auth as auth_endpoints
from app.database import get_db
from app.models import User, Base
from app.auth import get_password_hash

# Create a test database for these tests
test_engine = create_engine(
    "sqlite:///./test_integration_auth.db",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestSessionLocal()
        yield db
    finally:
        db.close()

# Create a new FastAPI app for testing
test_app = FastAPI()
test_app.include_router(auth_endpoints.router, prefix="/api/v1/auth", tags=["auth"])
test_app.dependency_overrides[get_db] = override_get_db
client = TestClient(test_app)

class TestAuthEndpoints:
    """Test authentication endpoints integration."""

    def setup_method(self):
        """Set up test database before each test."""
        # Create all tables using the test engine
        Base.metadata.create_all(bind=test_engine)

    def teardown_method(self):
        """Clean up test database after each test."""
        Base.metadata.drop_all(bind=test_engine)

    def test_register_user_success(self):
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

    def test_register_user_duplicate_email(self):
        """Test registration with duplicate email."""
        # Create a test user first
        session = TestSessionLocal()
        test_user = User(
            email="test@example.com",
            username="testuser",
            hashed_password=get_password_hash("testpassword"),
            full_name="Test User",
            is_active=True,
        )
        session.add(test_user)
        session.commit()
        session.refresh(test_user)
        test_email = test_user.email  # Get the email before closing session
        session.close()

        user_data = {
            "email": test_email,
            "username": "differentuser",
            "password": "password123",
            "full_name": "Different User",
        }

        response = client.post("/api/v1/auth/register", json=user_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Email already registered" in response.json()["detail"]

    def test_register_user_duplicate_username(self):
        """Test registration with duplicate username."""
        # Create a test user first
        session = TestSessionLocal()
        test_user = User(
            email="test@example.com",
            username="testuser",
            hashed_password=get_password_hash("testpassword"),
            full_name="Test User",
            is_active=True,
        )
        session.add(test_user)
        session.commit()
        session.refresh(test_user)
        test_username = test_user.username  # Get the username before closing session
        session.close()

        user_data = {
            "email": "different@example.com",
            "username": test_username,
            "password": "password123",
            "full_name": "Different User",
        }

        response = client.post("/api/v1/auth/register", json=user_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Username already taken" in response.json()["detail"]

    def test_register_user_invalid_data(self):
        """Test registration with invalid data."""
        user_data = {
            "email": "invalid-email",
            "username": "ab",  # Too short
            "password": "123",  # Too short
        }

        response = client.post("/api/v1/auth/register", json=user_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_login_success(self):
        """Test successful login."""
        # Create a test user first
        session = TestSessionLocal()
        test_user = User(
            email="test@example.com",
            username="testuser",
            hashed_password=get_password_hash("testpassword"),
            full_name="Test User",
            is_active=True,
        )
        session.add(test_user)
        session.commit()
        session.refresh(test_user)
        test_username = test_user.username  # Get the username before closing session
        session.close()

        login_data = {
            "username": test_username,
            "password": "testpassword",
        }

        response = client.post("/api/v1/auth/token", data=login_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 0

    def test_login_invalid_username(self):
        """Test login with invalid username."""
        login_data = {
            "username": "nonexistent",
            "password": "password123",
        }

        response = client.post("/api/v1/auth/token", data=login_data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Incorrect username or password" in response.json()["detail"]

    def test_login_invalid_password(self):
        """Test login with invalid password."""
        # Create a test user first
        session = TestSessionLocal()
        test_user = User(
            email="test@example.com",
            username="testuser",
            hashed_password=get_password_hash("testpassword"),
            full_name="Test User",
            is_active=True,
        )
        session.add(test_user)
        session.commit()
        session.refresh(test_user)
        test_username = test_user.username  # Get the username before closing session
        session.close()

        login_data = {
            "username": test_username,
            "password": "wrongpassword",
        }

        response = client.post("/api/v1/auth/token", data=login_data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Incorrect username or password" in response.json()["detail"]

    def test_get_current_user_success(self):
        """Test getting current user with valid token."""
        # Create a test user first
        session = TestSessionLocal()
        test_user = User(
            email="test@example.com",
            username="testuser",
            hashed_password=get_password_hash("testpassword"),
            full_name="Test User",
            is_active=True,
        )
        session.add(test_user)
        session.commit()
        session.refresh(test_user)
        test_username = test_user.username  # Get the username before closing session
        session.close()

        # Login to get token
        login_data = {
            "username": test_username,
            "password": "testpassword",
        }
        login_response = client.post("/api/v1/auth/token", data=login_data)
        token = login_response.json()["access_token"]

        # Use token to access protected endpoint
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/v1/auth/me", headers=headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
        assert "password" not in data

    def test_get_current_user_invalid_token(self):
        """Test getting current user with invalid token."""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/api/v1/auth/me", headers=headers)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_current_user_no_token(self):
        """Test getting current user without token."""
        response = client.get("/api/v1/auth/me")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_token_lifecycle(self):
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
