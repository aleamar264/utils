import contextlib
from typing import Annotated, Iterator, override

from loguru import logger
from sqlalchemy import Connection, Engine, create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from user.utils.fastapi.exceptions.general import ServiceError

from .general import DatabaseSessionManager, DefineGeneralDb, ReadEnvDatabaseSettings


class SyncDatabaseManager(DatabaseSessionManager):
	def __init__(self, db_params: DefineGeneralDb) -> None:
		super().__init__(db_params)
		self.engine: Engine | None = create_engine(self.create_url())
		self._sessionmaker: sessionmaker[Session] = sessionmaker(
			autocommit=False, bind=self.engine
		)

	@override
	def close(self):
		if self.engine is None:
			raise ServiceError
		self.engine.dispose()
		self.engine = None
		self._sessionmaker = None  # type: ignore

	@contextlib.contextmanager
	@override
	def connect(self) -> Iterator[Connection]:
		if self.engine is None:
			raise ServiceError
		with self.engine.begin() as connection:
			try:
				yield connection
			except SQLAlchemyError:
				connection.rollback()
				logger.error("Connection error ocurred.")
				raise ServiceError

	@contextlib.contextmanager
	@override
	def session(self) -> Iterator[Session]:
		if not self._sessionmaker:
			logger.error("Sessionmaker is not available.")
			raise ServiceError
		session = self._sessionmaker()
		try:
			yield session
		except SQLAlchemyError:
			session.rollback()
			logger.error("Session error, connection coiuld not be established {e}.")
			raise ServiceError
		finally:
			session.close()


_env = ReadEnvDatabaseSettings()
_database: DefineGeneralDb = DefineGeneralDb(**_env.model_dump())
sessionmanager = SyncDatabaseManager(_database)


def get_db_session():
	with sessionmanager.session() as session:
		yield session


depend_db_annotated = Annotated[Session, get_db_session()]


class Base(DeclarativeBase):
	pass
