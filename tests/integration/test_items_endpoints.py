"""
Integration tests for items endpoints.
"""

from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth import get_password_hash
from app.database import get_db
from app.main import app
from app.models import Base, Item, User

# Create a test database for these tests
test_engine = create_engine(
    "sqlite:///./test_integration_items.db",
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


# Override the database dependency
app.dependency_overrides[get_db] = override_get_db

# Create test client
client = TestClient(app)


class TestItemsEndpoints:
    """Test items endpoints integration."""

    def setup_method(self):
        """Set up test database before each test."""
        # Create all tables using the test engine
        Base.metadata.create_all(bind=test_engine)

    def teardown_method(self):
        """Clean up test database after each test."""
        Base.metadata.drop_all(bind=test_engine)

    def create_test_user_and_token(self):
        """Helper method to create a test user and get authentication token."""
        # Create a test user
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
        session.close()

        # Login to get token
        login_data = {
            "username": test_user.username,
            "password": "testpassword",
        }
        login_response = client.post("/api/v1/auth/token", data=login_data)
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        return test_user, headers

    def test_create_item_success(self):
        """Test successful item creation."""
        test_user, headers = self.create_test_user_and_token()

        item_data = {
            "title": "Test Item",
            "description": "Test Description",
            "price": 100,
        }

        response = client.post("/api/v1/items/", json=item_data, headers=headers)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["title"] == item_data["title"]
        assert data["description"] == item_data["description"]
        assert data["price"] == item_data["price"]
        assert data["owner_id"] == test_user.id
        assert data["id"] is not None

    def test_create_item_unauthorized(self):
        """Test item creation without authentication."""
        item_data = {
            "title": "Test Item",
            "description": "Test Description",
            "price": 100,
        }

        response = client.post("/api/v1/items/", json=item_data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_item_invalid_data(self):
        """Test item creation with invalid data."""
        test_user, headers = self.create_test_user_and_token()

        item_data = {
            "title": "",  # Empty title
            "price": -10,  # Negative price
        }

        response = client.post("/api/v1/items/", json=item_data, headers=headers)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_get_items_success(self):
        """Test getting items list."""
        test_user, headers = self.create_test_user_and_token()

        # Create some test items
        session = TestSessionLocal()
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
        session.close()

        response = client.get("/api/v1/items/", headers=headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # The response is paginated, so check the items array
        assert "items" in data
        items = data["items"]
        assert len(items) >= 2  # There might be more items from other tests
        # Check that our items are in the response
        item_titles = [item["title"] for item in items]
        assert "Item 1" in item_titles
        assert "Item 2" in item_titles

    def test_get_items_unauthorized(self):
        """Test getting items without authentication."""
        response = client.get("/api/v1/items/")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_item_by_id_success(self):
        """Test getting item by ID."""
        test_user, headers = self.create_test_user_and_token()

        # Create a test item
        session = TestSessionLocal()
        test_item = Item(
            title="Test Item",
            description="Test Description",
            price=100,
            owner_id=test_user.id,
        )
        session.add(test_item)
        session.commit()
        session.refresh(test_item)
        session.close()

        response = client.get(f"/api/v1/items/{test_item.id}", headers=headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["title"] == test_item.title
        assert data["description"] == test_item.description
        assert data["price"] == test_item.price

    def test_get_item_by_id_not_found(self):
        """Test getting non-existent item."""
        test_user, headers = self.create_test_user_and_token()

        response = client.get("/api/v1/items/999", headers=headers)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_item_by_id_unauthorized(self):
        """Test getting item without authentication."""
        response = client.get("/api/v1/items/1")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_item_success(self):
        """Test successful item update."""
        test_user, headers = self.create_test_user_and_token()

        # Create a test item
        session = TestSessionLocal()
        test_item = Item(
            title="Original Title",
            description="Original Description",
            price=100,
            owner_id=test_user.id,
        )
        session.add(test_item)
        session.commit()
        session.refresh(test_item)
        session.close()

        update_data = {
            "title": "Updated Title",
            "price": 200,
        }

        response = client.put(
            f"/api/v1/items/{test_item.id}", json=update_data, headers=headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["price"] == 200
        assert data["description"] == "Original Description"  # Unchanged

    def test_update_item_not_found(self):
        """Test updating non-existent item."""
        test_user, headers = self.create_test_user_and_token()

        update_data = {"title": "Updated Title"}

        response = client.put("/api/v1/items/999", json=update_data, headers=headers)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_item_unauthorized(self):
        """Test updating item without authentication."""
        update_data = {"title": "Updated Title"}

        response = client.put("/api/v1/items/1", json=update_data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_delete_item_success(self):
        """Test successful item deletion."""
        test_user, headers = self.create_test_user_and_token()

        # Create a test item
        session = TestSessionLocal()
        test_item = Item(
            title="Test Item",
            description="Test Description",
            price=100,
            owner_id=test_user.id,
        )
        session.add(test_item)
        session.commit()
        session.refresh(test_item)
        session.close()

        response = client.delete(f"/api/v1/items/{test_item.id}", headers=headers)

        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify item is deleted
        get_response = client.get(f"/api/v1/items/{test_item.id}", headers=headers)
        assert get_response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_item_not_found(self):
        """Test deleting non-existent item."""
        test_user, headers = self.create_test_user_and_token()

        response = client.delete("/api/v1/items/999", headers=headers)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_item_unauthorized(self):
        """Test deleting item without authentication."""
        response = client.delete("/api/v1/items/1")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_my_items_success(self):
        """Test getting current user's items."""
        test_user, headers = self.create_test_user_and_token()

        # Create items for the test user
        session = TestSessionLocal()
        item1 = Item(
            title="My Item 1",
            description="Description 1",
            price=100,
            owner_id=test_user.id,
        )
        item2 = Item(
            title="My Item 2",
            description="Description 2",
            price=200,
            owner_id=test_user.id,
        )
        session.add_all([item1, item2])
        session.commit()
        session.close()

        # Try the correct endpoint path
        response = client.get("/api/v1/items/my-items", headers=headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) >= 2  # There might be more items from other tests
        # Check that our items are in the response
        item_titles = [item["title"] for item in data]
        assert "My Item 1" in item_titles
        assert "My Item 2" in item_titles

    def test_get_my_items_unauthorized(self):
        """Test getting current user's items without authentication."""
        response = client.get("/api/v1/items/my-items")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
