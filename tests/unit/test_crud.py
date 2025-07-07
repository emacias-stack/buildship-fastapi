"""
Unit tests for CRUD operations.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.crud import (
    create_item,
    create_user,
    delete_item,
    delete_user,
    get_item_by_id,
    get_items,
    get_items_count,
    get_user_by_email,
    get_user_by_id,
    get_user_by_username,
    update_item,
    update_user,
)
from app.models import Base, Item, User
from app.schemas import ItemCreate, ItemUpdate, UserCreate, UserUpdate

# Create a test database for these tests
test_engine = create_engine(
    "sqlite:///./test_crud.db",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


class TestUserCRUD:
    """Test user CRUD operations."""

    def test_create_user(self):
        """Test creating a new user."""
        # Create test database
        Base.metadata.create_all(bind=test_engine)
        session = TestSessionLocal()

        try:
            user_data = UserCreate(
                email="test@example.com",
                username="testuser",
                password="testpassword",
                full_name="Test User",
            )

            user = create_user(session, user_data)
            assert user is not None
            assert user.email == "test@example.com"
            assert user.username == "testuser"
            assert user.full_name == "Test User"
            assert user.is_active is True
        finally:
            session.close()
            Base.metadata.drop_all(bind=test_engine)

    def test_get_user_by_id(self):
        """Test getting user by ID."""
        # Create test database and user
        Base.metadata.create_all(bind=test_engine)
        session = TestSessionLocal()

        try:
            # Create a test user
            test_user = User(
                email="test@example.com",
                username="testuser",
                hashed_password="hashed_password",
                full_name="Test User",
                is_active=True,
            )
            session.add(test_user)
            session.commit()
            session.refresh(test_user)

            # Test getting user by ID
            user = get_user_by_id(session, test_user.id)
            assert user is not None
            assert user.username == "testuser"
        finally:
            session.close()
            Base.metadata.drop_all(bind=test_engine)

    def test_get_user_by_id_not_found(self):
        """Test getting user by non-existent ID."""
        # Create test database
        Base.metadata.create_all(bind=test_engine)
        session = TestSessionLocal()

        try:
            user = get_user_by_id(session, 999)
            assert user is None
        finally:
            session.close()
            Base.metadata.drop_all(bind=test_engine)

    def test_get_user_by_email(self):
        """Test getting user by email."""
        # Create test database and user
        Base.metadata.create_all(bind=test_engine)
        session = TestSessionLocal()

        try:
            # Create a test user
            test_user = User(
                email="test@example.com",
                username="testuser",
                hashed_password="hashed_password",
                full_name="Test User",
                is_active=True,
            )
            session.add(test_user)
            session.commit()
            session.refresh(test_user)

            # Test getting user by email
            user = get_user_by_email(session, "test@example.com")
            assert user is not None
            assert user.username == "testuser"
        finally:
            session.close()
            Base.metadata.drop_all(bind=test_engine)

    def test_get_user_by_email_not_found(self):
        """Test getting user by non-existent email."""
        # Create test database
        Base.metadata.create_all(bind=test_engine)
        session = TestSessionLocal()

        try:
            user = get_user_by_email(session, "nonexistent@example.com")
            assert user is None
        finally:
            session.close()
            Base.metadata.drop_all(bind=test_engine)

    def test_get_user_by_username(self):
        """Test getting user by username."""
        # Create test database and user
        Base.metadata.create_all(bind=test_engine)
        session = TestSessionLocal()

        try:
            # Create a test user
            test_user = User(
                email="test@example.com",
                username="testuser",
                hashed_password="hashed_password",
                full_name="Test User",
                is_active=True,
            )
            session.add(test_user)
            session.commit()
            session.refresh(test_user)

            # Test getting user by username
            user = get_user_by_username(session, "testuser")
            assert user is not None
            assert user.email == "test@example.com"
        finally:
            session.close()
            Base.metadata.drop_all(bind=test_engine)

    def test_get_user_by_username_not_found(self):
        """Test getting user by non-existent username."""
        # Create test database
        Base.metadata.create_all(bind=test_engine)
        session = TestSessionLocal()

        try:
            user = get_user_by_username(session, "nonexistent")
            assert user is None
        finally:
            session.close()
            Base.metadata.drop_all(bind=test_engine)

    def test_update_user(self):
        """Test updating a user."""
        # Create test database and user
        Base.metadata.create_all(bind=test_engine)
        session = TestSessionLocal()

        try:
            # Create a test user
            test_user = User(
                email="test@example.com",
                username="testuser",
                hashed_password="hashed_password",
                full_name="Test User",
                is_active=True,
            )
            session.add(test_user)
            session.commit()
            session.refresh(test_user)

            # Update user data
            update_data = UserUpdate(
                full_name="Updated Test User",
                is_active=False,
            )

            updated_user = update_user(session, test_user.id, update_data)
            assert updated_user is not None
            assert updated_user.full_name == "Updated Test User"
            assert updated_user.is_active is False
        finally:
            session.close()
            Base.metadata.drop_all(bind=test_engine)

    def test_update_user_not_found(self):
        """Test updating a non-existent user."""
        # Create test database
        Base.metadata.create_all(bind=test_engine)
        session = TestSessionLocal()

        try:
            update_data = UserUpdate(full_name="Updated Test User")
            updated_user = update_user(session, 999, update_data)
            assert updated_user is None
        finally:
            session.close()
            Base.metadata.drop_all(bind=test_engine)

    def test_delete_user(self):
        """Test deleting a user."""
        # Create test database and user
        Base.metadata.create_all(bind=test_engine)
        session = TestSessionLocal()

        try:
            # Create a test user
            test_user = User(
                email="test@example.com",
                username="testuser",
                hashed_password="hashed_password",
                full_name="Test User",
                is_active=True,
            )
            session.add(test_user)
            session.commit()
            session.refresh(test_user)

            # Delete user
            success = delete_user(session, test_user.id)
            assert success is True

            # Verify user is deleted
            user = get_user_by_id(session, test_user.id)
            assert user is None
        finally:
            session.close()
            Base.metadata.drop_all(bind=test_engine)

    def test_delete_user_not_found(self):
        """Test deleting a non-existent user."""
        # Create test database
        Base.metadata.create_all(bind=test_engine)
        session = TestSessionLocal()

        try:
            success = delete_user(session, 999)
            assert success is False
        finally:
            session.close()
            Base.metadata.drop_all(bind=test_engine)


class TestItemCRUD:
    """Test item CRUD operations."""

    def test_create_item(self):
        """Test creating a new item."""
        # Create test database and user
        Base.metadata.create_all(bind=test_engine)
        session = TestSessionLocal()

        try:
            # Create a test user
            test_user = User(
                email="test@example.com",
                username="testuser",
                hashed_password="hashed_password",
                full_name="Test User",
                is_active=True,
            )
            session.add(test_user)
            session.commit()
            session.refresh(test_user)

            # Create item data
            item_data = ItemCreate(
                title="Test Item",
                description="Test Description",
                price=100,
            )

            item = create_item(session, item_data, test_user.id)
            assert item is not None
            assert item.title == "Test Item"
            assert item.description == "Test Description"
            assert item.price == 100
            assert item.owner_id == test_user.id
        finally:
            session.close()
            Base.metadata.drop_all(bind=test_engine)

    def test_get_item_by_id(self):
        """Test getting item by ID."""
        # Create test database, user, and item
        Base.metadata.create_all(bind=test_engine)
        session = TestSessionLocal()

        try:
            # Create a test user
            test_user = User(
                email="test@example.com",
                username="testuser",
                hashed_password="hashed_password",
                full_name="Test User",
                is_active=True,
            )
            session.add(test_user)
            session.commit()
            session.refresh(test_user)

            # Create a test item
            test_item = Item(
                title="Test Item",
                description="Test Description",
                price=100,
                owner_id=test_user.id,
            )
            session.add(test_item)
            session.commit()
            session.refresh(test_item)

            # Test getting item by ID
            item = get_item_by_id(session, test_item.id)
            assert item is not None
            assert item.title == "Test Item"
        finally:
            session.close()
            Base.metadata.drop_all(bind=test_engine)

    def test_get_item_by_id_not_found(self):
        """Test getting item by non-existent ID."""
        # Create test database
        Base.metadata.create_all(bind=test_engine)
        session = TestSessionLocal()
        try:
            item = get_item_by_id(session, 999)
            assert item is None
        finally:
            session.close()
            Base.metadata.drop_all(bind=test_engine)

    def test_update_item(self):
        """Test updating an item."""
        # Create test database, user, and item
        Base.metadata.create_all(bind=test_engine)
        session = TestSessionLocal()
        try:
            # Create a test user
            test_user = User(
                email="test@example.com",
                username="testuser",
                hashed_password="hashed_password",
                full_name="Test User",
                is_active=True,
            )
            session.add(test_user)
            session.commit()
            session.refresh(test_user)
            # Create a test item
            test_item = Item(
                title="Test Item",
                description="Test Description",
                price=100,
                owner_id=test_user.id,
            )
            session.add(test_item)
            session.commit()
            session.refresh(test_item)

            # Update item data
            update_data = ItemUpdate(
                title="Updated Test Item",
                price=200,
            )

            updated_item = update_item(session, test_item.id, update_data)
            assert updated_item is not None
            assert updated_item.title == "Updated Test Item"
            assert updated_item.price == 200
        finally:
            session.close()
            Base.metadata.drop_all(bind=test_engine)

    def test_update_item_not_found(self):
        """Test updating a non-existent item."""
        # Create test database
        Base.metadata.create_all(bind=test_engine)
        session = TestSessionLocal()

        try:
            update_data = ItemUpdate(title="Updated Test Item")
            updated_item = update_item(session, 999, update_data)
            assert updated_item is None
        finally:
            session.close()
            Base.metadata.drop_all(bind=test_engine)

    def test_delete_item(self):
        """Test deleting an item."""
        # Create test database, user, and item
        Base.metadata.create_all(bind=test_engine)
        session = TestSessionLocal()

        try:
            # Create a test user
            test_user = User(
                email="test@example.com",
                username="testuser",
                hashed_password="hashed_password",
                full_name="Test User",
                is_active=True,
            )
            session.add(test_user)
            session.commit()
            session.refresh(test_user)

            # Create a test item
            test_item = Item(
                title="Test Item",
                description="Test Description",
                price=100,
                owner_id=test_user.id,
            )
            session.add(test_item)
            session.commit()
            session.refresh(test_item)

            # Delete item
            success = delete_item(session, test_item.id)
            assert success is True

            # Verify item is deleted
            item = get_item_by_id(session, test_item.id)
            assert item is None
        finally:
            session.close()
            Base.metadata.drop_all(bind=test_engine)

    def test_delete_item_not_found(self):
        """Test deleting a non-existent item."""
        # Create test database
        Base.metadata.create_all(bind=test_engine)
        session = TestSessionLocal()

        try:
            success = delete_item(session, 999)
            assert success is False
        finally:
            session.close()
            Base.metadata.drop_all(bind=test_engine)

    def test_get_items(self):
        """Test getting all items."""
        # Create test database, user, and items
        Base.metadata.create_all(bind=test_engine)
        session = TestSessionLocal()

        try:
            # Create a test user
            test_user = User(
                email="test@example.com",
                username="testuser",
                hashed_password="hashed_password",
                full_name="Test User",
                is_active=True,
            )
            session.add(test_user)
            session.commit()
            session.refresh(test_user)

            # Create test items
            item1 = Item(
                title="Item 1",
                description="Description 1",
                price=100,
                owner_id=test_user.id,
            )
            item2 = Item(
                title="Item 2",
                description="Description 2",
                price=200,
                owner_id=test_user.id,
            )
            session.add_all([item1, item2])
            session.commit()

            # Test getting all items
            items = get_items(session)
            assert len(items) == 2
            assert any(item.title == "Item 1" for item in items)
            assert any(item.title == "Item 2" for item in items)
        finally:
            session.close()
            Base.metadata.drop_all(bind=test_engine)

    def test_get_items_by_owner(self):
        """Test getting items by owner."""
        # Create test database, users, and items
        Base.metadata.create_all(bind=test_engine)
        session = TestSessionLocal()

        try:
            # Create test users
            user1 = User(
                email="user1@example.com",
                username="user1",
                hashed_password="hashed_password",
                full_name="User 1",
                is_active=True,
            )
            user2 = User(
                email="user2@example.com",
                username="user2",
                hashed_password="hashed_password",
                full_name="User 2",
                is_active=True,
            )
            session.add_all([user1, user2])
            session.commit()
            session.refresh(user1)
            session.refresh(user2)

            # Create test items
            item1 = Item(
                title="User1 Item",
                description="Description",
                price=100,
                owner_id=user1.id,
            )
            item2 = Item(
                title="User2 Item",
                description="Description",
                price=200,
                owner_id=user2.id,
            )
            session.add_all([item1, item2])
            session.commit()

            # Test getting items by owner
            user1_items = get_items(session, owner_id=user1.id)
            assert len(user1_items) == 1
            assert user1_items[0].title == "User1 Item"
        finally:
            session.close()
            Base.metadata.drop_all(bind=test_engine)

    def test_get_items_count(self):
        """Test getting items count."""
        # Create test database, user, and items
        Base.metadata.create_all(bind=test_engine)
        session = TestSessionLocal()
        try:
            # Create a test user
            test_user = User(
                email="test@example.com",
                username="testuser",
                hashed_password="hashed_password",
                full_name="Test User",
                is_active=True,
            )
            session.add(test_user)
            session.commit()
            session.refresh(test_user)

            # Create test items
            item1 = Item(
                title="Item 1",
                description="Description 1",
                price=100,
                owner_id=test_user.id,
            )
            item2 = Item(
                title="Item 2",
                description="Description 2",
                price=200,
                owner_id=test_user.id,
            )
            session.add_all([item1, item2])
            session.commit()

            # Test getting items count
            count = get_items_count(session)
            assert count == 2
        finally:
            session.close()
            Base.metadata.drop_all(bind=test_engine)
