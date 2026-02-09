from contextlib import asynccontextmanager, contextmanager
from unittest.mock import Mock

import pytest
from database.general import (
    AsyncDatabaseSessionManager,
    BaseSessionManager,
    DatabaseSessionManager,
    DefineGeneralDb,
    MixInNameTable,
    ReadEnvDatabaseSettings,
    ServiceError,
)
from sqlalchemy import URL, Connection
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncSession
from sqlalchemy.orm import Session


# Tests for ReadEnvDatabaseSettings
class TestReadEnvDatabaseSettings:
    def test_settings_with_valid_env_file(self, tmp_path):
        """Test loading settings from .database.env file."""
        env_file = tmp_path / ".database.env"
        env_content = """
DRIVERNAME=postgresql+psycopg2
USERNAME=testuser
PASSWORD=testpass
HOST=localhost
DATABASE=testdb
PORT=5432
"""
        env_file.write_text(env_content)

        settings = ReadEnvDatabaseSettings(
            _env_file=str(env_file),
            _env_file_encoding="utf-8",
        )

        assert settings.drivername == "postgresql+psycopg2"
        assert settings.username == "testuser"
        assert settings.password == "testpass"
        assert settings.host == "localhost"
        assert settings.database == "testdb"
        assert settings.port == 5432

    def test_settings_direct_initialization(self):
        """Test direct initialization with parameters."""
        settings = ReadEnvDatabaseSettings(
            drivername="mysql+pymysql",
            username="user",
            password="pass",
            host="db.example.com",
            database="mydb",
            port=3306,
        )

        assert settings.drivername == "mysql+pymysql"
        assert settings.username == "user"
        assert settings.password == "pass"
        assert settings.host == "db.example.com"
        assert settings.database == "mydb"
        assert settings.port == 3306


# Tests for DefineGeneralDb
class TestDefineGeneralDb:
    def test_valid_db_config(self, async_db_params: DefineGeneralDb):
        """Test valid database configuration."""
        assert async_db_params.drivername == "postgresql+asyncpg"
        assert async_db_params.username == "user"
        assert async_db_params.password == "pass"
        assert async_db_params.host == "localhost"
        assert async_db_params.database == "testdb"
        assert async_db_params.port == 5432

    def test_model_dump(self, db_params: DefineGeneralDb):
        """Test model_dump returns correct dictionary."""
        dumped = db_params.model_dump()
        assert dumped == {
            "drivername": "postgresql+psycopg2",
            "username": "user",
            "password": "pass",
            "host": "localhost",
            "database": "testdb",
            "port": 5432,
        }


# Tests for BaseSessionManager
class TestBaseSessionManager:
    def test_initialization(self,db_params: DefineGeneralDb):
        """Test BaseSessionManager initialization."""

        manager = BaseSessionManager(db_params)
        assert manager.db_params == db_params

    def test_create_url(self, async_db_params: DefineGeneralDb):
        """Test URL creation from db_params."""

        manager = BaseSessionManager(async_db_params)
        url = manager.create_url()

        assert isinstance(url, URL)
        assert url.drivername == "postgresql+asyncpg"
        assert url.username == "user"
        assert url.password == "pass"
        assert url.host == "localhost"
        assert url.database == "testdb"
        assert url.port == 5432


# Tests for DatabaseSessionManager
class TestDatabaseSessionManager:
    def test_is_abstract(self, db_params: DefineGeneralDb):
        """Test that DatabaseSessionManager cannot be instantiated directly."""
        with pytest.raises(TypeError):
            DatabaseSessionManager(db_params)

    def test_concrete_implementation(self, db_params: DefineGeneralDb):
        """Test concrete implementation of DatabaseSessionManager."""
        class ConcreteDatabaseSessionManager(DatabaseSessionManager):
            def close(self):
                pass

            @contextmanager
            def connect(self):
                yield Mock(spec=Connection)

            @contextmanager
            def session(self):
                yield Mock(spec=Session)

        manager = ConcreteDatabaseSessionManager(db_params)
        assert isinstance(manager, DatabaseSessionManager)
        assert manager.db_params == db_params

    def test_concrete_connect_context_manager(self, db_params: DefineGeneralDb):
        """Test connect context manager."""
        class ConcreteDatabaseSessionManager(DatabaseSessionManager):
            def close(self):
                pass

            @contextmanager
            def connect(self):
                conn = Mock(spec=Connection)
                yield conn

            @contextmanager
            def session(self):
                yield Mock(spec=Session)

        manager = ConcreteDatabaseSessionManager(db_params)
        with manager.connect() as conn:
            assert isinstance(conn, Mock)

    def test_concrete_session_context_manager(self, db_params: DefineGeneralDb):
        """Test session context manager."""
        class ConcreteDatabaseSessionManager(DatabaseSessionManager):
            def close(self):
                pass

            @contextmanager
            def connect(self):
                yield Mock(spec=Connection)

            @contextmanager
            def session(self):
                sess = Mock(spec=Session)
                yield sess

        manager = ConcreteDatabaseSessionManager(db_params)
        with manager.session() as sess:
            assert isinstance(sess, Mock)


# Tests for AsyncDatabaseSessionManager
class TestAsyncDatabaseSessionManager:
    def test_is_abstract(self, db_params: DefineGeneralDb):
        """Test that AsyncDatabaseSessionManager cannot be instantiated directly."""
        with pytest.raises(TypeError):
            AsyncDatabaseSessionManager(db_params)

    def test_concrete_implementation(self, db_params: DefineGeneralDb):
        """Test concrete implementation of AsyncDatabaseSessionManager."""
        class ConcreteAsyncDatabaseSessionManager(AsyncDatabaseSessionManager):
            def async_close(self):
                pass

            @asynccontextmanager
            async def async_connect(self):
                yield Mock(spec=AsyncConnection)

            @asynccontextmanager
            async def async_session(self):
                yield Mock(spec=AsyncSession)

        manager = ConcreteAsyncDatabaseSessionManager(db_params)
        assert isinstance(manager, AsyncDatabaseSessionManager)
        assert manager.db_params == db_params

    @pytest.mark.asyncio
    async def test_concrete_async_connect_context_manager(self, db_params: DefineGeneralDb):
        """Test async_connect context manager."""
        class ConcreteAsyncDatabaseSessionManager(AsyncDatabaseSessionManager):
            def async_close(self):
                pass

            @asynccontextmanager
            async def async_connect(self):
                conn = Mock(spec=AsyncConnection)
                yield conn

            @asynccontextmanager
            async def async_session(self):
                yield Mock(spec=AsyncSession)

        manager = ConcreteAsyncDatabaseSessionManager(db_params)
        async with manager.async_connect() as conn:
            assert isinstance(conn, Mock)

    @pytest.mark.asyncio
    async def test_concrete_async_session_context_manager(self, db_params: DefineGeneralDb):
        """Test async_session context manager."""

        class ConcreteAsyncDatabaseSessionManager(AsyncDatabaseSessionManager):
            def async_close(self):
                pass

            @asynccontextmanager
            async def async_connect(self):
                yield Mock(spec=AsyncConnection)

            @asynccontextmanager
            async def async_session(self):
                sess = Mock(spec=AsyncSession)
                yield sess

        manager = ConcreteAsyncDatabaseSessionManager(db_params)
        async with manager.async_session() as sess:
            assert isinstance(sess, Mock)


# Tests for MixInNameTable
class TestMixInNameTable:
    def test_tablename_from_class_name(self):
        """Test that __tablename__ is derived from class name in lowercase."""
        class User(MixInNameTable):
            pass

        assert User.__tablename__ == "user"

    def test_tablename_multiple_classes(self):
        """Test tablename for multiple classes."""
        class Product(MixInNameTable):
            pass

        class Order(MixInNameTable):
            pass

        assert Product.__tablename__ == "product"
        assert Order.__tablename__ == "order"

    def test_tablename_with_camelcase(self):
        """Test tablename with CamelCase class names."""
        class UserProfile(MixInNameTable):
            pass

        class OrderItem(MixInNameTable):
            pass

        assert UserProfile.__tablename__ == "userprofile"
        assert OrderItem.__tablename__ == "orderitem"


# Tests for ServiceError
class TestServiceError:
    def test_service_error_with_message(self):
        """Test ServiceError with a message."""
        error = ServiceError("Database connection failed")
        assert error.msg == "Database connection failed"
        assert str(error) == "Database connection failed"

    def test_service_error_without_message(self):
        """Test ServiceError without a message."""
        error = ServiceError()
        assert error.msg is None
        assert str(error) == "None"

    def test_service_error_is_exception(self):
        """Test that ServiceError is an Exception."""
        error = ServiceError("Test error")
        assert isinstance(error, Exception)

    def test_service_error_can_be_raised(self):
        """Test that ServiceError can be raised and caught."""
        with pytest.raises(ServiceError) as exc_info:
            raise ServiceError("Custom error message")

        assert exc_info.value.msg == "Custom error message"

    def test_service_error_with_none_message(self):
        """Test ServiceError initialized with None."""
        error = ServiceError(None)
        assert error.msg is None
