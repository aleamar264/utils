from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import TypeVar
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

TSchema = TypeVar("TSchema", bound=BaseModel)
TModel = TypeVar("TModel")

class GeneralCrudSync[TModel, TSchema: BaseModel](ABC):
	def __init__(self, model: type[TModel], session: Session) -> None:
		self.model = model
		self.session = session

	@abstractmethod
	def get_objects(self) -> Sequence[TModel]:
		pass

	@abstractmethod
	def create_object(self, object: TSchema) -> TModel:
		pass

	@abstractmethod
	def update_object(self, object: TSchema, object_id: UUID) -> TModel:
		pass

	@abstractmethod
	def delete_object(self, id: UUID) -> None:
		pass

	@abstractmethod
	def get_object_by_id(self, id: UUID) -> TModel:
		pass

class GeneralCrudAsync[TModel, TSchema: BaseModel](ABC):
	def __init__(self, model: type[TModel], session: AsyncSession) -> None:
		self.model = model
		self.session = session

	@abstractmethod
	async def get_object(self) -> Sequence[TModel]:
		pass

	@abstractmethod
	async def create_object(self, object: TSchema) -> TModel:
		pass

	@abstractmethod
	async def update_object(self, id: UUID, object: TSchema) -> TModel:
		pass

	@abstractmethod
	async def delete_object(self, id: UUID) -> None:
		pass

	@abstractmethod
	async def get_object_by_id(self, id: UUID) -> TModel:
		pass
