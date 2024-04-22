from abc import ABC, abstractmethod
from typing import Sequence
from uuid import UUID

from schemas.user import User as user_schema
from utils.database.async_database import depend_db_annotated as async_depend_db
from utils.database.sync_database import depend_db_annotated


class GeneralCrudSync[T](ABC):
	def __init__(self, model: T, session: depend_db_annotated) -> None:
		self.model = model
		self.session = session

	@abstractmethod
	def get_users(self) -> Sequence[T]:
		pass

	@abstractmethod
	def create_user(self, user: user_schema) -> T:
		pass

	@abstractmethod
	def update_user(self, user: user_schema) -> T:
		pass

	@abstractmethod
	def delete_user(self, user_id: UUID) -> None:
		pass

	@abstractmethod
	def get_user_by_id(self, user_id: UUID) -> T:
		pass

	@abstractmethod
	def get_user_by_username(self, username: str) -> T:
		pass

	@abstractmethod
	def get_user_by_email(self, email: str) -> T:
		pass


class GeneralCrudAsync[T](ABC):
	def __init__(self, model: T, session: async_depend_db) -> None:
		self.model = model
		self.session = session

	@abstractmethod
	async def get_users(self) -> Sequence[T]:
		pass

	@abstractmethod
	async def create_user(self, user: user_schema) -> T:
		pass

	@abstractmethod
	async def update_user(self, user: user_schema) -> T:
		pass

	@abstractmethod
	async def delete_user(self, user_id: UUID) -> None:
		pass

	@abstractmethod
	async def get_user_by_id(self, user_id: UUID) -> T:
		pass

	@abstractmethod
	async def get_user_by_username(self, username: str) -> T:
		pass

	@abstractmethod
	async def get_user_by_email(self, email: str) -> T:
		pass
