from abc import ABC, abstractmethod
from contextlib import asynccontextmanager, contextmanager
from typing import AsyncIterator, Iterator

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL, Connection
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncSession
from sqlalchemy.orm import Session, declared_attr


class ReadEnvDatabaseSettings(BaseSettings):
	drivername: str = Field(..., description="Database Driver")
	username: str = Field(..., description="Database Username")
	password: str = Field(..., description="Database Password")
	host: str = Field(..., description="Database Host")
	database: str = Field(..., description="Database Name")
	port: int = Field(..., description="Database Port")

	model_config = SettingsConfigDict(
		env_file=".database.env", env_file_encoding="utf-8"
	)


class DefineGeneralDb(BaseModel):
	drivername: str = Field(
		...,
		description="Database Driver",
		examples=["mysql+pymysql", "postgresql+psycopg2", "postgresql+asyncpg"],
	)
	username: str = Field(..., description="Database Username")
	password: str = Field(..., description="Database Password")
	host: str = Field(..., description="Database Host")
	database: str = Field(..., description="Database Name")
	port: int = Field(..., description="Database Port")


class BaseSessionManager(ABC):
	def __init__(self, db_params: DefineGeneralDb) -> None:
		self.db_params = db_params

	def create_url(self) -> URL:
		return URL.create(**self.db_params.model_dump())


class DatabaseSessionManager(BaseSessionManager):
	@abstractmethod
	def close(self):
		pass

	@abstractmethod
	@contextmanager
	def connect(self) -> Iterator[Connection]:
		pass

	@abstractmethod
	@contextmanager
	def session(self) -> Iterator[Session]:
		pass


class AsyncDatabaseSessionManager(BaseSessionManager):
	@abstractmethod
	def async_close(self):
		pass

	@abstractmethod
	@asynccontextmanager
	def async_connect(self) -> AsyncIterator[AsyncConnection]:
		pass

	@abstractmethod
	@asynccontextmanager
	def async_session(self) -> AsyncIterator[AsyncSession]:
		pass


class MixInNameTable:
	@declared_attr.directive
	def __tablename__(cls):
		return cls.__name__.lower()
