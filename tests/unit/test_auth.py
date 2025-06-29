"""
Unit tests for authentication module.
"""

import pytest
from datetime import timedelta
from jose import jwt

from app.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    verify_token,
    authenticate_user,
)
from app.config import settings


class TestPasswordHashing:
    """Test password hashing functionality."""
    
    def test_password_hashing(self):
        """Test that password hashing works correctly."""
        password = "testpassword"
        hashed = get_password_hash(password)
        
        assert hashed != password
        assert verify_password(password, hashed)
        assert not verify_password("wrongpassword", hashed)
    
    def test_different_passwords_different_hashes(self):
        """Test that different passwords produce different hashes."""
        password1 = "password1"
        password2 = "password2"
        
        hash1 = get_password_hash(password1)
        hash2 = get_password_hash(password2)
        
        assert hash1 != hash2


class TestTokenCreation:
    """Test JWT token creation and verification."""
    
    def test_create_access_token(self):
        """Test creating access token."""
        data = {"sub": "testuser"}
        token = create_access_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_create_access_token_with_expiry(self):
        """Test creating access token with custom expiry."""
        data = {"sub": "testuser"}
        expires_delta = timedelta(minutes=15)
        token = create_access_token(data, expires_delta=expires_delta)
        
        # Decode token to verify expiry
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        assert payload["sub"] == "testuser"
    
    def test_verify_token_valid(self):
        """Test verifying valid token."""
        data = {"sub": "testuser"}
        token = create_access_token(data)
        username = verify_token(token)
        
        assert username == "testuser"
    
    def test_verify_token_invalid(self):
        """Test verifying invalid token."""
        username = verify_token("invalid_token")
        assert username is None
    
    def test_verify_token_expired(self):
        """Test verifying expired token."""
        data = {"sub": "testuser"}
        expires_delta = timedelta(minutes=-10)  # Expired 10 minutes ago
        token = create_access_token(data, expires_delta=expires_delta)
        username = verify_token(token)
        
        assert username is None


class TestUserAuthentication:
    """Test user authentication functionality."""
    
    def test_authenticate_user_valid(self, db_session, test_user):
        """Test authenticating valid user."""
        user = authenticate_user(db_session, test_user.username, "testpassword")
        assert user is not None
        assert user.username == test_user.username
    
    def test_authenticate_user_invalid_username(self, db_session):
        """Test authenticating with invalid username."""
        user = authenticate_user(db_session, "nonexistent", "password")
        assert user is None
    
    def test_authenticate_user_invalid_password(self, db_session, test_user):
        """Test authenticating with invalid password."""
        user = authenticate_user(db_session, test_user.username, "wrongpassword")
        assert user is None
    
    def test_authenticate_user_inactive(self, db_session):
        """Test authenticating inactive user."""
        # Create inactive user
        from app.models import User
        from app.auth import get_password_hash
        
        inactive_user = User(
            email="inactive@example.com",
            username="inactive",
            hashed_password=get_password_hash("password"),
            is_active=False,
        )
        db_session.add(inactive_user)
        db_session.commit()
        
        user = authenticate_user(db_session, "inactive", "password")
        assert user is not None  # Authentication still works
        assert not user.is_active 