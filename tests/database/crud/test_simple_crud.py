# tests/test_general_crud.py
from collections.abc import Sequence
from typing import override
from uuid import UUID, uuid4

import pytest
from database.crud.simple_crud import GeneralCrudAsync, GeneralCrudSync
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session


# Test models
class UserSchema(BaseModel):
	name: str
	email: str


class User:
	"""Mock SQLAlchemy model"""

	def __init__(self, id: UUID, name: str, email: str):
		self.id = id
		self.name = name
		self.email = email


# Concrete implementations for testing
class TestCrudSync(GeneralCrudSync[User, UserSchema]):
	"""Concrete implementation for testing sync CRUD."""

	@override
	def get_objects(self) -> Sequence[User]:
		# Mock implementation
		return [
			User(uuid4(), "Alice", "alice@example.com"),
			User(uuid4(), "Bob", "bob@example.com"),
		]

	def create_object(self, object: UserSchema) -> User:
		return User(uuid4(), object.name, object.email)

	def update_object(self, object: UserSchema, object_id: UUID) -> User:
		return User(object_id, object.name, object.email)

	def delete_object(self, id: UUID) -> None:
		pass  # Mock deletion

	def get_object_by_id(self, id: UUID) -> User:
		return User(id, "Test User", "test@example.com")


class TestCrudAsync(GeneralCrudAsync[User, UserSchema]):
	"""Concrete implementation for testing async CRUD."""

	async def get_object(self) -> Sequence[User]:
		return [
			User(uuid4(), "Alice", "alice@example.com"),
			User(uuid4(), "Bob", "bob@example.com"),
		]

	async def create_object(self, object: UserSchema) -> User:
		return User(uuid4(), object.name, object.email)

	async def update_object(self, id: UUID, object: UserSchema) -> User:
		return User(id, object.name, object.email)

	async def delete_object(self, id: UUID) -> None:
		pass

	async def get_object_by_id(self, id: UUID) -> User:
		return User(id, "Test User", "test@example.com")


# Fixtures
@pytest.fixture
def mock_session():
	"""Mock SQLAlchemy session."""
	return Session()


@pytest.fixture
def mock_async_session():
	"""Mock async SQLAlchemy session."""
	return AsyncSession()


@pytest.fixture
def sync_crud(mock_session):
	"""Fixture for sync CRUD implementation."""
	return TestCrudSync(model=User, session=mock_session)


@pytest.fixture
def async_crud(mock_async_session):
	"""Fixture for async CRUD implementation."""
	return TestCrudAsync(model=User, session=mock_async_session)


# Tests for Sync CRUD
class TestGeneralCrudSync:
	def test_get_objects(self, sync_crud):
		"""Test getting all objects."""
		objects = sync_crud.get_objects()

		# assert issubclass(objects, Sequence[User])
		assert len(objects) == 2
		assert objects[0].name == "Alice"
		assert objects[1].name == "Bob"

	def test_create_object(self, sync_crud):
		"""Test creating an object."""
		user_data = UserSchema(name="Charlie", email="charlie@example.com")
		user = sync_crud.create_object(user_data)

		# assert isinstance(user, User)
		assert user.name == "Charlie"
		assert user.email == "charlie@example.com"
		assert isinstance(user.id, UUID)

	def test_update_object(self, sync_crud):
		"""Test updating an object."""
		user_id = uuid4()
		updated_data = UserSchema(name="Updated", email="updated@example.com")
		user = sync_crud.update_object(updated_data, user_id)

		assert user.id == user_id
		assert user.name == "Updated"
		assert user.email == "updated@example.com"

	def test_delete_object(self, sync_crud):
		"""Test deleting an object."""
		user_id = uuid4()
		# Should not raise an exception
		sync_crud.delete_object(user_id)

	def test_get_object_by_id(self, sync_crud):
		"""Test getting object by ID."""
		user_id = uuid4()
		user = sync_crud.get_object_by_id(user_id)

		assert user.id == user_id
		assert isinstance(user, User)


# Tests for Async CRUD
class TestGeneralCrudAsync:
	@pytest.mark.asyncio
	async def test_get_object(self, async_crud):
		"""Test getting all objects."""
		objects = await async_crud.get_object()

		assert isinstance(objects, Sequence)
		assert len(objects) == 2
		assert objects[0].name == "Alice"

	@pytest.mark.asyncio
	async def test_create_object(self, async_crud):
		"""Test creating an object."""
		user_data = UserSchema(name="Charlie", email="charlie@example.com")
		user = await async_crud.create_object(user_data)

		assert isinstance(user, User)
		assert user.name == "Charlie"
		assert isinstance(user.id, UUID)

	@pytest.mark.asyncio
	async def test_update_object(self, async_crud):
		"""Test updating an object."""
		user_id = uuid4()
		updated_data = UserSchema(name="Updated", email="updated@example.com")
		user = await async_crud.update_object(user_id, updated_data)

		assert user.id == user_id
		assert user.name == "Updated"

	@pytest.mark.asyncio
	async def test_delete_object(self, async_crud):
		"""Test deleting an object."""
		user_id = uuid4()
		await async_crud.delete_object(user_id)

	@pytest.mark.asyncio
	async def test_get_object_by_id(self, async_crud):
		"""Test getting object by ID."""
		user_id = uuid4()
		user = await async_crud.get_object_by_id(user_id)

		assert user.id == user_id
		assert isinstance(user, User)
