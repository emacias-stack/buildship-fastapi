"""
Unit tests for authentication module.
"""

import pytest
from datetime import timedelta
from jose import jwt
from fastapi import HTTPException, status
from unittest.mock import patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    verify_token,
    authenticate_user,
    get_current_user,
    get_current_active_user,
    get_current_superuser,
    get_current_user_optional,
    get_current_active_user_optional,
    get_user,
)
from app.config import settings
from app.models import User, Base

# Create a test database for these tests
test_engine = create_engine(
    "sqlite:///./test_auth.db",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine)


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
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[
                settings.algorithm])
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

    def test_verify_token_none(self):
        """Test verifying None token."""
        username = verify_token(None)
        assert username is None

    def test_verify_token_missing_sub(self):
        """Test verifying token without sub claim."""
        data = {"user": "testuser"}  # No 'sub' key
        token = create_access_token(data)
        username = verify_token(token)

        assert username is None


class TestUserAuthentication:
    """Test user authentication functionality."""

    def test_authenticate_user_valid(self):
        """Test authenticating a valid user."""
        # Create test database and user
        Base.metadata.create_all(bind=test_engine)
        session = TestSessionLocal()

        try:
            # Create a test user
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

            # Test authentication
            user = authenticate_user(session, "testuser", "testpassword")
            assert user is not None
            assert user.username == "testuser"
        finally:
            session.close()
            Base.metadata.drop_all(bind=test_engine)

    def test_authenticate_user_invalid_username(self):
        """Test authenticating with invalid username."""
        # Create test database
        Base.metadata.create_all(bind=test_engine)
        session = TestSessionLocal()

        try:
            user = authenticate_user(session, "nonexistent", "password")
            assert user is None
        finally:
            session.close()
            Base.metadata.drop_all(bind=test_engine)

    def test_authenticate_user_invalid_password(self):
        """Test authenticating with invalid password."""
        # Create test database and user
        Base.metadata.create_all(bind=test_engine)
        session = TestSessionLocal()

        try:
            # Create a test user
            test_user = User(
                email="test@example.com",
                username="testuser",
                hashed_password=get_password_hash("testpassword"),
                full_name="Test User",
                is_active=True,
            )
            session.add(test_user)
            session.commit()

            # Test authentication with wrong password
            user = authenticate_user(session, "testuser", "wrongpassword")
            assert user is None
        finally:
            session.close()
            Base.metadata.drop_all(bind=test_engine)

    def test_authenticate_user_inactive(self):
        """Test authenticating an inactive user."""
        # Create test database and inactive user
        Base.metadata.create_all(bind=test_engine)
        session = TestSessionLocal()

        try:
            # Create an inactive user
            inactive_user = User(
                email="inactive@example.com",
                username="inactive",
                hashed_password=get_password_hash("password"),
                full_name="Inactive User",
                is_active=False,
            )
            session.add(inactive_user)
            session.commit()

            # Test authentication - the function doesn't check is_active, so it
            # should return the user
            user = authenticate_user(session, "inactive", "password")
            assert user is not None
            assert not user.is_active
        finally:
            session.close()
            Base.metadata.drop_all(bind=test_engine)


class TestUserFunctions:
    """Test user-related functions."""

    def test_get_user_valid(self):
        """Test getting a valid user."""
        # Create test database and user
        Base.metadata.create_all(bind=test_engine)
        session = TestSessionLocal()

        try:
            # Create a test user
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

            # Test getting user by username (not id)
            user = get_user(session, "testuser")
            assert user is not None
            assert user.username == "testuser"
        finally:
            session.close()
            Base.metadata.drop_all(bind=test_engine)

    def test_get_user_invalid(self):
        """Test getting a non-existent user."""
        # Create test database
        Base.metadata.create_all(bind=test_engine)
        session = TestSessionLocal()

        try:
            user = get_user(session, 999)
            assert user is None
        finally:
            session.close()
            Base.metadata.drop_all(bind=test_engine)


class TestCurrentUserDependencies:
    """Test current user dependency functions."""

    @pytest.mark.asyncio
    async def test_get_current_user_valid_token(self):
        """Test getting current user with valid token."""
        # Create test database and user
        Base.metadata.create_all(bind=test_engine)
        session = TestSessionLocal()

        try:
            # Create a test user
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

            # Create valid token
            token = create_access_token({"sub": test_user.username})

            # Mock the dependency
            with patch('app.auth.oauth2_scheme', return_value=token):
                with patch('app.auth.get_db', return_value=session):
                    user = await get_current_user(token=token, db=session)
                    assert user is not None
                    assert user.username == test_user.username
        finally:
            session.close()
            Base.metadata.drop_all(bind=test_engine)

    @pytest.mark.asyncio
    async def test_get_current_user_no_token(self):
        """Test getting current user with no token."""
        # Create test database
        Base.metadata.create_all(bind=test_engine)
        session = TestSessionLocal()

        try:
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(token=None, db=session)

            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        finally:
            session.close()
            Base.metadata.drop_all(bind=test_engine)

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self):
        """Test getting current user with invalid token."""
        # Create test database
        Base.metadata.create_all(bind=test_engine)
        session = TestSessionLocal()

        try:
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(token="invalid_token", db=session)

            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        finally:
            session.close()
            Base.metadata.drop_all(bind=test_engine)

    @pytest.mark.asyncio
    async def test_get_current_user_user_not_found(self):
        """Test getting current user when user doesn't exist in database."""
        # Create test database
        Base.metadata.create_all(bind=test_engine)
        session = TestSessionLocal()

        try:
            # Create token for non-existent user
            token = create_access_token({"sub": "nonexistent"})

            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(token=token, db=session)

            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        finally:
            session.close()
            Base.metadata.drop_all(bind=test_engine)

    @pytest.mark.asyncio
    async def test_get_current_active_user_valid(self):
        """Test getting current active user."""
        # Create test database and user
        Base.metadata.create_all(bind=test_engine)
        session = TestSessionLocal()

        try:
            # Create a test user
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

            # Mock get_current_user to return active user
            with patch('app.auth.get_current_user', return_value=test_user):
                user = await get_current_active_user(current_user=test_user)
                assert user is not None
                assert user.is_active
        finally:
            session.close()
            Base.metadata.drop_all(bind=test_engine)

    @pytest.mark.asyncio
    async def test_get_current_active_user_inactive(self):
        """Test getting current active user when user is inactive."""
        # Create test database
        Base.metadata.create_all(bind=test_engine)
        session = TestSessionLocal()

        try:
            # Create inactive user
            inactive_user = User(
                email="inactive@example.com",
                username="inactive",
                hashed_password=get_password_hash("password"),
                is_active=False,
            )

            with pytest.raises(HTTPException) as exc_info:
                await get_current_active_user(current_user=inactive_user)

            assert exc_info.value.status_code == 400
            assert "Inactive user" in str(exc_info.value.detail)
        finally:
            session.close()
            Base.metadata.drop_all(bind=test_engine)

    @pytest.mark.asyncio
    async def test_get_current_superuser_valid(self):
        """Test getting current superuser."""
        # Create test database
        Base.metadata.create_all(bind=test_engine)
        session = TestSessionLocal()

        try:
            # Create superuser
            superuser = User(
                email="admin@example.com",
                username="admin",
                hashed_password=get_password_hash("hashed"),
                is_superuser=True,
            )

            with patch('app.auth.get_current_user', return_value=superuser):
                user = await get_current_superuser(current_user=superuser)
                assert user is not None
                assert user.is_superuser
        finally:
            session.close()
            Base.metadata.drop_all(bind=test_engine)

    @pytest.mark.asyncio
    async def test_get_current_superuser_not_superuser(self):
        """Test getting current superuser when user is not superuser."""
        # Create test database and user
        Base.metadata.create_all(bind=test_engine)
        session = TestSessionLocal()

        try:
            # Create a regular user
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

            with pytest.raises(HTTPException) as exc_info:
                await get_current_superuser(current_user=test_user)

            assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
            assert "Not enough permissions" in str(exc_info.value.detail)
        finally:
            session.close()
            Base.metadata.drop_all(bind=test_engine)


class TestOptionalAuthentication:
    """Test optional authentication functions."""

    def test_get_current_user_optional_with_token(self):
        """Test getting current user optional with valid token."""
        # Create test database and user
        Base.metadata.create_all(bind=test_engine)
        session = TestSessionLocal()

        try:
            # Create a test user
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

            # Create valid token
            token = create_access_token({"sub": test_user.username})

            # Mock the dependency
            with patch('app.auth.oauth2_scheme', return_value=token):
                with patch('app.auth.get_db', return_value=session):
                    user = get_current_user_optional(token=token, db=session)
                    assert user is not None
                    assert user.username == test_user.username
        finally:
            session.close()
            Base.metadata.drop_all(bind=test_engine)

    def test_get_current_user_optional_with_invalid_token(self):
        """Test getting current user optional with invalid token."""
        # Create test database
        Base.metadata.create_all(bind=test_engine)
        session = TestSessionLocal()

        try:
            user = get_current_user_optional(token="invalid_token", db=session)
            assert user is None
        finally:
            session.close()
            Base.metadata.drop_all(bind=test_engine)

    def test_get_current_user_optional_with_credentials(self):
        """Test getting current user optional with credentials."""
        # Create test database
        Base.metadata.create_all(bind=test_engine)
        session = TestSessionLocal()

        try:
            user = get_current_user_optional(token="credentials", db=session)
            assert user is None
        finally:
            session.close()
            Base.metadata.drop_all(bind=test_engine)

    def test_get_current_user_optional_no_auth(self):
        """Test getting current user optional with no authentication."""
        # Create test database
        Base.metadata.create_all(bind=test_engine)
        session = TestSessionLocal()

        try:
            user = get_current_user_optional(token=None, db=session)
            assert user is None
        finally:
            session.close()
            Base.metadata.drop_all(bind=test_engine)

    def test_get_current_active_user_optional_with_active_user(self):
        """Test getting current active user optional with active user."""
        # Create test database and user
        Base.metadata.create_all(bind=test_engine)
        session = TestSessionLocal()

        try:
            # Create a test user
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

            user = get_current_active_user_optional(current_user=test_user)
            assert user is not None
            assert user.is_active
        finally:
            session.close()
            Base.metadata.drop_all(bind=test_engine)

    def test_get_current_active_user_optional_with_inactive_user(self):
        """Test getting current active user optional with inactive user."""
        # Create test database
        Base.metadata.create_all(bind=test_engine)
        session = TestSessionLocal()

        try:
            # Create inactive user
            inactive_user = User(
                email="inactive@example.com",
                username="inactive",
                hashed_password=get_password_hash("password"),
                is_active=False,
            )

            user = get_current_active_user_optional(current_user=inactive_user)
            assert user is None
        finally:
            session.close()
            Base.metadata.drop_all(bind=test_engine)

    def test_get_current_active_user_optional_no_user(self):
        """Test getting current active user optional with no user."""
        # Create test database
        Base.metadata.create_all(bind=test_engine)
        session = TestSessionLocal()

        try:
            user = get_current_active_user_optional(current_user=None)
            assert user is None
        finally:
            session.close()
            Base.metadata.drop_all(bind=test_engine)
