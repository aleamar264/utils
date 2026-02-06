import contextlib
from collections.abc import Iterator
from typing import override

from logger.logger import LoggingSetup
from sqlalchemy import Connection, Engine, create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from .general import DatabaseSessionManager, DefineGeneralDb, ServiceError


class SyncDatabaseManager(DatabaseSessionManager):
	"""
	SyncDatabaseManager
	A synchronous database session manager that handles SQLAlchemy engine and session lifecycle.
	Inherits from DatabaseSessionManager and provides context managers for database connections
	and sessions with comprehensive error handling and logging.
	Attributes:
		logger (Logger): Logger instance for database operations.
		engine (Engine | None): SQLAlchemy Engine instance for database connectivity.
		_sessionmaker (sessionmaker[Session]): Factory for creating database sessions.
	Methods:
		__init__(db_params: DefineGeneralDb, logging: LoggingSetup) -> None:
			Initializes the SyncDatabaseManager with database parameters and logging setup.
			Creates and configures the SQLAlchemy engine and sessionmaker.
			Args:
				db_params: Database connection parameters.
				logging: LoggingSetup instance to configure logger.
			Raises:
				Logs info message on successful engine setup.
		close() -> None:
			Disposes of the database engine and cleans up resources.
			Sets engine and sessionmaker to None after disposal.
			Raises:
				ServiceError: If engine is not initialized or disposal fails.
		connect() -> Iterator[Connection]:
			Context manager that provides a raw database connection.
			Automatically handles transaction management and rollback on errors.
			Yields:
				Connection: A SQLAlchemy Connection object.
			Raises:
				ServiceError: If engine is not initialized or database error occurs.
			Example:
				```python
				with manager.connect() as connection:
					result = connection.execute(query)
				```
		session() -> Iterator[Session]:
			Context manager that provides a SQLAlchemy ORM session.
			Handles session lifecycle, transaction management, and automatic rollback.
			Yields:
				Session: A SQLAlchemy Session object.
			Raises:
				ServiceError: If sessionmaker is not initialized or database error occurs.
			Example:
				```python
				with manager.session() as session:
					user = session.query(User).filter_by(id=1).first()
				```
	Example:
		```python
			_env = ReadEnvDatabaseSettings()
			_database: DefineGeneralDb = DefineGeneralDb(**_env.model_dump())
			sessionmanager = DatabaseManager(_database)


			def get_db_session():
				with sessionmanager.async_session() as session:
					yield session


			depend_db_annotated = Annotated[session, Depends(get_db_session)]
	"""

	def __init__(self, db_params: DefineGeneralDb, logging: LoggingSetup) -> None:
		super().__init__(db_params)
		self.logger = logging.get_logger("database")
		self.engine: Engine | None = create_engine(self.create_url())
		self._sessionmaker: sessionmaker[Session] = sessionmaker(
			autocommit=False, bind=self.engine
		)
		self.logger.info("Engine setup correctly")

	@override
	def close(self):
		"""Disposes of the database engine and cleans up resources.
			Sets engine and sessionmaker to None after disposal.
			Raises:
				ServiceError: If engine is not initialized or disposal fails.
		"""
		if self.engine is None:
			self.logger.error("Attempted to close a non-existing engine")
			raise ServiceError("Engine is not initialized")
		try:
			self.engine.dispose()
			self.logger.info("Database engine disposed")

		except SQLAlchemyError as exc:
			self.logger.opt(exception=exc).error(
				"Error while disposing database engine"
			)
			raise ServiceError("Failed to close database engine") from exc

		finally:
			self.engine = None
			self._sessionmaker = None #type: ignore

	@contextlib.contextmanager
	@override
	def connect(self) -> Iterator[Connection]:
		"""
		Context manager that provides a raw database connection.
		Automatically handles transaction management and rollback on errors.
		Yields:
			Connection: A SQLAlchemy Connection object.
		Raises:
			ServiceError: If engine is not initialized or database error occurs.
		Example:
			```python
			with manager.connect() as connection:
				result = connection.execute(query)
			```
		"""
		if self.engine is None:
			self.logger.error("Engine is not available for connection")
			raise ServiceError("Engine is not initialized")
		with self.engine.begin() as connection:
			try:
				yield connection
			except SQLAlchemyError as exc:
				connection.rollback()
				self.logger.opt(exception=exc).error(
					"Database error while using async connection"
				)
				raise ServiceError("Database connection failed") from exc

	@contextlib.contextmanager
	@override
	def session(self) -> Iterator[Session]:
		"""
		Context manager that provides a SQLAlchemy ORM session.
		Handles session lifecycle, transaction management, and automatic rollback.
		Yields:
			Session: A SQLAlchemy Session object.
		Raises:
			ServiceError: If sessionmaker is not initialized or database error occurs.
		Example:
			```python
			with manager.session() as session:
				user = session.query(User).filter_by(id=1).first()
			```
		"""
		if not self._sessionmaker:
			self.logger.error("Sessionmaker is not available")
			raise ServiceError("Sessionmaker is not initialized")
		session = self._sessionmaker()
		try:
			yield session
		except SQLAlchemyError as exc:
			session.rollback()
			self.logger.bind(
				engine=str(self.engine)
			).opt(exception=exc).error(
				"Database error while using async session"
			)

			raise ServiceError("Database session failed") from exc
		finally:
			session.close()
