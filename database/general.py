from sqlalchemy import create_engine, URL
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Session
from sqlalchemy.engine.base import Engine


class ReadEnvDatabaseSettings(BaseSettings):
    drivername: str = Field(..., description="Database Driver")
    username: str = Field(..., description="Database Username")
    password: str = Field(..., description="Database Password")
    host: str = Field(..., description="Database Host")
    database: str = Field(..., description="Database Name")
    port: int = Field(..., description="Database Port")

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8"
    )


class DefineGeneralDb(BaseModel):
    drivername: str = Field(
        ...,
        description="Database Driver",
        examples=["mysql+pymysql", "postgresql+psycopg2"],
    )
    username: str = Field(..., description="Database Username")
    password: str = Field(..., description="Database Password")
    host: str = Field(..., description="Database Host")
    database: str = Field(..., description="Database Name")
    port: int = Field(..., description="Database Port")

    def create_url(self) -> URL:
        return URL.create(
            drivername=self.drivername,
            username=self.username,
            password=self.password,
            host=self.host,
            database=self.database,
            port=self.port,
        )

    def create_engine_(self) -> Engine:
        return create_engine(self.create_url(), echo=False)

    @staticmethod
    def create_session(engine: Engine):
        return sessionmaker(autocommit=False, autoflush=False, bind=engine)


_env = ReadEnvDatabaseSettings()
_database: DefineGeneralDb = DefineGeneralDb(**_env.model_dump())
_engine = _database.create_engine_()
_session: Session = _database.create_session(_engine)


class Base(DeclarativeBase):
    pass
