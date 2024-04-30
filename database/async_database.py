import contextlib
from typing import Annotated, AsyncIterator, override

from fastapi import Depends
from loguru import logger
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
	AsyncConnection,
	AsyncEngine,
	AsyncSession,
	async_sessionmaker,
	create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from utils.database.general import DefineGeneralDb
from utils.fastapi.exceptions.general import ServiceError

from .general import AsyncDatabaseSessionManager, ReadEnvDatabaseSettings


class AsyncDatabaseManager(AsyncDatabaseSessionManager):
	def __init__(self, db_params: DefineGeneralDb) -> None:
		super().__init__(db_params)
		self.engine: AsyncEngine | None = create_async_engine(self.create_url())
		self._sessionmaker: async_sessionmaker[AsyncSession] = async_sessionmaker(
			autocommit=False, bind=self.engine
		)

	@override
	async def async_close(self):
		if self.engine is None:
			raise ServiceError
		await self.engine.dispose()
		self.engine = None
		self._sessionmaker = None  # type: ignore

	@override
	@contextlib.asynccontextmanager
	async def async_connect(self) -> AsyncIterator[AsyncConnection]:
		if self.engine is None:
			raise ServiceError

		async with self.engine.begin() as connection:
			try:
				yield connection
			except SQLAlchemyError:
				await connection.rollback()
				logger.error("Connection error ocurred")
				raise ServiceError

	@override
	@contextlib.asynccontextmanager
	async def async_session(self) -> AsyncIterator[AsyncSession]:
		if not self._sessionmaker:
			logger.error("Sessionmaker is not available.")
			raise ServiceError

		session = self._sessionmaker()
		try:
			yield session
		except SQLAlchemyError as e:
			await session.rollback()
			logger.error(f"Session error could not be established {e}")
			raise ServiceError
		finally:
			await session.close()


_env = ReadEnvDatabaseSettings()
_database: DefineGeneralDb = DefineGeneralDb(**_env.model_dump())
sessionmanager = AsyncDatabaseManager(_database)


async def get_db_session():
	async with sessionmanager.async_session() as session:
		yield session


depend_db_annotated = Annotated[AsyncSession, Depends(get_db_session)]


class Base(DeclarativeBase):
	pass
