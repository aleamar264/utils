import contextlib
from typing import AsyncIterator, override

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from general import DefineGeneralDb, ServiceError

from .general import AsyncDatabaseSessionManager
from logger.logger import LoggingSetup


class AsyncDatabaseManager(AsyncDatabaseSessionManager):
	def __init__(self, db_params: DefineGeneralDb, logging: LoggingSetup) -> None:
		"""
		AsyncDatabaseManager

		A comprehensive async database management class that handles SQLAlchemy async engine creation,
		session management, and connection lifecycle. Inherits from AsyncDatabaseSessionManager and
		provides context managers for safe database operations with automatic error handling and rollback
		on failures.

		Attributes:
			logger (Logger): Logger instance for database operations.
			engine (AsyncEngine | None): SQLAlchemy async engine instance. Set to None after disposal.
			_sessionmaker (async_sessionmaker[AsyncSession]): Factory for creating async database sessions.

		Methods:
			__init__(db_params: DefineGeneralDb, logging: LoggingSetup) -> None:
				Initializes the AsyncDatabaseManager with database parameters and logging configuration.
				Creates and configures the async engine and sessionmaker.
				
				Args:
					db_params: Database configuration parameters.
					logging: Logging setup instance to configure logger.
					
				Raises:
					Logs "Engine setup correctly" upon successful initialization.

			async def async_close() -> None:
				Disposes of the database engine and releases all resources.
				Sets engine and sessionmaker to None after disposal.
				
				Raises:
					ServiceError: If engine is not initialized or if SQLAlchemy errors occur during disposal.
					
				Example:
					```python
					await manager.async_close()
					```

			async def async_connect() -> AsyncIterator[AsyncConnection]:
				Context manager that provides an async database session with ORM support.
				Automatically rolls back on errors and closes the session on exit.
				
				Yields:
					AsyncSession: A SQLAlchemy async session object for ORM operations.
					
				Raises:
					ServiceError: If sessionmaker is not initialized or if session operations fail.
					
				Example:
				```python
					async with manager.async_session() as session:
						user = await session.add(User, user_id)
						await session.commit()
				```

				Example Usage:
					```python
					app = FastAPI()

					
					async def get_db_session():
						async with sessionmanager.async_session() as session:
							yield session


					@app.get("/users/{user_id}")
					async def get_user(user_id: int, session: Annotated[AsyncSession, Depends(get_db_session)]):
						user = session.query(User).filter_by(id=1).first()
						return user
					```

		Example:
		```python
			_env = ReadEnvDatabaseSettings()
			_database: DefineGeneralDb = DefineGeneralDb(**_env.model_dump())
			sessionmanager = AsyncDatabaseManager(_database)


			async def get_db_session():
				async with sessionmanager.async_session() as session:
					yield session


			depend_db_annotated = Annotated[AsyncSession, Depends(get_db_session)]
		```


		"""
		super().__init__(db_params)
		self.logger = logging.get_logger("database")
		self.engine: AsyncEngine | None = create_async_engine(self.create_url())
		self._sessionmaker: async_sessionmaker[AsyncSession] = async_sessionmaker(
			autocommit=False, bind=self.engine
		)
		self.logger.info("Engine setup correctly")

	@override
	async def async_close(self):
		"""
		Disposes of the database engine and releases all resources.
		Sets engine and sessionmaker to None after disposal.
		
		Raises:
			ServiceError: If engine is not initialized or if SQLAlchemy errors occur during disposal.
			
		Example:
			```python
			await manager.async_close()
			```
		"""
		if self.engine is None:
			self.logger.error("Attempted to close a non-existing engine")
			raise ServiceError("Engine is not initialized")

		try:
			await self.engine.dispose()
			self.logger.info("Database engine disposed")

		except SQLAlchemyError as exc:
			self.logger.opt(exception=exc).error(
				"Error while disposing database engine"
			)
			raise ServiceError("Failed to close database engine") from exc

		finally:
			self.engine = None
			self._sessionmaker = None #type: ignore

	@override
	@contextlib.asynccontextmanager
	async def async_connect(self) -> AsyncIterator[AsyncConnection]:
		"""Context manager that provides a raw database connection with transaction support.
			Automatically rolls back on SQLAlchemy errors.
			
			Yields:
				AsyncConnection: A SQLAlchemy async connection object.
				
			Raises:
				ServiceError: If engine is not initialized or if connection operations fail.
				
			Example:
			```python
				async with manager.async_connect() as connection:
					result = await connection.execute(query)
			```
		"""
		if self.engine is None:
			self.logger.error("Engine is not available for connection")
			raise ServiceError("Engine is not initialized")
		async with self.engine.begin() as connection:
			try:
				yield connection
			except SQLAlchemyError as exc:
				await connection.rollback()
				self.logger.opt(exception=exc).error(
					"Database error while using async connection"
				)
				raise ServiceError("Database connection failed") from exc

	@override
	@contextlib.asynccontextmanager
	async def async_session(self) -> AsyncIterator[AsyncSession]:
		"""
		Context manager that provides an async database session with ORM support.
				Automatically rolls back on errors and closes the session on exit.
				
				Yields:
					AsyncSession: A SQLAlchemy async session object for ORM operations.
					
				Raises:
					ServiceError: If sessionmaker is not initialized or if session operations fail.
					
				Example:
				```python
					async with manager.async_session() as session:
						user = await session.get(User, user_id)
						await session.commit()
				```

		Example Usage:
			```python
			app = FastAPI()

			
			async def get_db_session():
    			async with sessionmanager.async_session() as session:
        			yield session


			@app.get("/users/{user_id}")
			async def get_user(user_id: int, session: Annotated[AsyncSession, Depends(get_db_session)]):
				user = session.query(User).filter_by(id=1).first()
				return user
			```
			"""
		if not self._sessionmaker:
			self.logger.error("Sessionmaker is not available")
			raise ServiceError("Sessionmaker is not initialized")
		session = self._sessionmaker()
		try:
			yield session
		except SQLAlchemyError as exc:
			await session.rollback()
			self.logger.bind(
				engine=str(self.engine)
			).opt(exception=exc).error(
				"Database error while using async session"
			)

			raise ServiceError("Database session failed") from exc
		finally:
			await session.close()




class Base(DeclarativeBase):
    pass
