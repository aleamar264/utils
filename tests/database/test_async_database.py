from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest
from _pytest.logging import LogCaptureFixture
from database.async_database import AsyncDatabaseManager
from database.general import DefineGeneralDb, ServiceError
from logger.logger import LoguruLogging
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
	AsyncConnection,
	AsyncEngine,
	AsyncSession,
	async_sessionmaker,
)


def test_callable_functions(
	async_db_params: DefineGeneralDb, caplog: LogCaptureFixture, tmp_path: Path
):
	with patch("database.async_database.create_async_engine", Mock(spec=AsyncEngine)):
		with patch(
			"database.async_database.async_sessionmaker",
			Mock(spec=async_sessionmaker[AsyncSession]),
		):
			logger = LoguruLogging()
			logger.setup(default_path=tmp_path, default_config=True)
			async_db_manager = AsyncDatabaseManager(
				db_params=async_db_params, logging=logger
			)
			assert callable(async_db_manager.async_close)
			assert callable(async_db_manager.async_connect)
			assert callable(async_db_manager.async_session)
		assert "Engine setup correctly" in caplog.text


@pytest.mark.asyncio
async def test_async_connect(
	db_params: DefineGeneralDb, caplog: LogCaptureFixture, tmp_path: Path
):
	mock_engine = AsyncMock(spec=AsyncEngine)
	mock_connection = AsyncMock(spec=AsyncConnection)

	# Create a proper async context manager mock
	mock_context_manager = AsyncMock()
	mock_context_manager.__aenter__.return_value = mock_connection
	mock_context_manager.__aexit__.return_value = None
	# Make engine.begin() return the async context manager
	mock_engine.begin.return_value = mock_context_manager

	with patch("database.async_database.create_async_engine", return_value=mock_engine):
		with patch(
			"database.async_database.async_sessionmaker",
			Mock(spec=async_sessionmaker[AsyncSession]),
		):
			logger = LoguruLogging()
			logger.setup(default_path=tmp_path, default_config=True)
			async_db_manager = AsyncDatabaseManager(db_params=db_params, logging=logger)

			async with async_db_manager.async_connect() as conn:
				assert conn == mock_connection

			# Verify the context manager was used properly
			mock_engine.begin.assert_called_once()
			mock_context_manager.__aenter__.assert_called_once()
			mock_context_manager.__aexit__.assert_called_once()

	assert "Engine setup correctly" in caplog.text


@pytest.mark.asyncio
async def test_async_connect_error(
	db_params: DefineGeneralDb, caplog: LogCaptureFixture, tmp_path: Path
):
	with patch("database.async_database.create_async_engine", return_value=None):
		with patch(
			"database.async_database.async_sessionmaker",
			Mock(spec=async_sessionmaker[AsyncSession]),
		):
			logger = LoguruLogging()
			logger.setup(default_path=tmp_path, default_config=True)
			async_db_manager = AsyncDatabaseManager(db_params=db_params, logging=logger)
			with pytest.raises(ServiceError):
				async with async_db_manager.async_connect():
					pass

	assert "Engine is not available for connection" in caplog.text


@pytest.mark.asyncio
async def test_async_connect_exception(
	db_params: DefineGeneralDb, caplog: LogCaptureFixture, tmp_path: Path
):
    mock_engine = AsyncMock(spec=AsyncEngine)
    mock_connection = AsyncMock(spec=AsyncConnection)

    # # Create a proper async context manager mock
    mock_context_manager = AsyncMock()
    mock_context_manager.__aenter__.return_value = mock_connection
    mock_context_manager.__aexit__.return_value = None
    # Make engine.begin() return the async context manager
    mock_engine.begin.return_value = mock_context_manager


    with patch("database.async_database.create_async_engine", return_value=mock_engine):
        with patch(
            "database.async_database.async_sessionmaker",
            Mock(spec=async_sessionmaker[AsyncSession]),
        ):
            logger = LoguruLogging()
            logger.setup(default_path=tmp_path, default_config=True)
            async_db_manager = AsyncDatabaseManager(db_params=db_params, logging=logger)

            with pytest.raises(ServiceError):
                async with async_db_manager.async_connect():
                    raise SQLAlchemyError("Simulated error")
            mock_connection.rollback.assert_called_once()

    assert "Database error while using async connection" in caplog.text

@pytest.mark.asyncio
async def test_async_session(
	db_params: DefineGeneralDb, caplog: LogCaptureFixture, tmp_path: Path
):
	mock_engine = AsyncMock(spec=AsyncEngine)
	mock_session = AsyncMock(spec=AsyncSession)

	# Create a mock sessionmaker that returns the mock session when called
	mock_sessionmaker = Mock(return_value=mock_session)

	with patch("database.async_database.create_async_engine", return_value=mock_engine):
		with patch(
			"database.async_database.async_sessionmaker",
			return_value=mock_sessionmaker,
		):
			logger = LoguruLogging()
			logger.setup(default_path=tmp_path, default_config=True)
			async_db_manager = AsyncDatabaseManager(db_params=db_params, logging=logger)
			async with async_db_manager.async_session() as session:
				assert session == mock_session

			# Verify session lifecycle
			mock_sessionmaker.assert_called_once()
			mock_session.close.assert_called_once()
	assert "Engine setup correctly" in caplog.text


@pytest.mark.asyncio
async def test_async_session_none_sessionmaker(
	db_params: DefineGeneralDb, caplog: LogCaptureFixture, tmp_path: Path
):
    mock_engine = AsyncMock(spec=AsyncEngine)

    with patch("database.async_database.create_async_engine", return_value=mock_engine):
        with patch(
            "database.async_database.async_sessionmaker",
            return_value=None,
        ):
            logger = LoguruLogging()
            logger.setup(default_path=tmp_path, default_config=True)
            async_db_manager = AsyncDatabaseManager(db_params=db_params, logging=logger)
            with pytest.raises(ServiceError):
                async with async_db_manager.async_session():
                    pass



    assert "Sessionmaker is not available" in caplog.text


@pytest.mark.asyncio
async def test_async_session_exception(
	db_params: DefineGeneralDb, caplog: LogCaptureFixture, tmp_path: Path
):
    mock_engine = AsyncMock(spec=AsyncEngine)
    mock_session = AsyncMock(spec=AsyncSession)

    # Create a mock sessionmaker that returns the mock session when called
    mock_sessionmaker = Mock(return_value=mock_session)

    with patch("database.async_database.create_async_engine", return_value=mock_engine):
        with patch(
            "database.async_database.async_sessionmaker",
            return_value=mock_sessionmaker,
        ):
            logger = LoguruLogging()
            logger.setup(default_path=tmp_path, default_config=True)
            async_db_manager = AsyncDatabaseManager(db_params=db_params, logging=logger)
            with pytest.raises(ServiceError):
                async with async_db_manager.async_session() as session:
                    raise SQLAlchemyError("Simulated error")

            # Verify session lifecycle
            mock_sessionmaker.assert_called_once()
            mock_session.close.assert_called_once()
    assert "Database error while using async session" in caplog.text



@pytest.mark.asyncio
async def test_async_close(
	db_params: DefineGeneralDb, caplog: LogCaptureFixture, tmp_path: Path
):
	mock_engine = AsyncMock(spec=AsyncEngine)
	mock_engine.dispose.return_value = None
	mock_session = AsyncMock(spec=AsyncSession)

	# Create a mock sessionmaker that returns the mock session when called
	mock_sessionmaker = Mock(return_value=mock_session)

	with patch("database.async_database.create_async_engine", return_value=mock_engine):
		with patch(
			"database.async_database.async_sessionmaker",
			return_value=mock_sessionmaker,
		):
			logger = LoguruLogging()
			logger.setup(default_path=tmp_path, default_config=True)
			async_db_manager = AsyncDatabaseManager(db_params=db_params, logging=logger)
			await async_db_manager.async_close()

			# Verify session lifecycle
			mock_engine.dispose.assert_called_once()
	assert "Database engine disposed" in caplog.text


@pytest.mark.asyncio
async def test_async_close_engine_none(
	db_params: DefineGeneralDb,
	caplog: LogCaptureFixture,
	tmp_path: Path,
):
	mock_session = AsyncMock(spec=AsyncSession)

	# Create a mock sessionmaker that returns the mock session when called
	mock_sessionmaker = Mock(return_value=mock_session)

	with patch(
		"database.async_database.create_async_engine", return_value=None
	):
		with patch(
			"database.async_database.async_sessionmaker",
			return_value=mock_sessionmaker,
		):
			logger = LoguruLogging()
			logger.setup(default_path=tmp_path, default_config=True)
			async_db_manager = AsyncDatabaseManager(db_params=db_params, logging=logger)
			with pytest.raises(ServiceError):
				await async_db_manager.async_close()

	assert "Attempted to close a non-existing engine" in caplog.text


async def test_async_close_engine_exception(
	db_params: DefineGeneralDb,
	caplog: LogCaptureFixture,
	tmp_path: Path,
):
	mock_engine = AsyncMock(spec=AsyncEngine)
	mock_engine.dispose.side_effect = SQLAlchemyError()
	mock_session = AsyncMock(spec=AsyncSession)

	# Create a mock sessionmaker that returns the mock session when called
	mock_sessionmaker = Mock(return_value=mock_session)

	with patch(
		"database.async_database.create_async_engine", return_value=mock_engine
	):
		with patch(
			"database.async_database.async_sessionmaker",
			return_value=mock_sessionmaker,
		):
			logger = LoguruLogging()
			logger.setup(default_path=tmp_path, default_config=True)
			async_db_manager = AsyncDatabaseManager(db_params=db_params, logging=logger)
			with pytest.raises(ServiceError):
				await async_db_manager.async_close()

	assert "Error while disposing database engine" in caplog.text
