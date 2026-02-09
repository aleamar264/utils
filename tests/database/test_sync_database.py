from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
from _pytest.logging import LogCaptureFixture
from database.general import DefineGeneralDb, ServiceError
from database.sync_database import SyncDatabaseManager
from logger.logger import LoguruLogging
from sqlalchemy import Connection, Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

SYNC_DATABASE_PATH = "database.sync_database"


def test_callable_functions(
	db_params: DefineGeneralDb, caplog: LogCaptureFixture, tmp_path: Path
):
	with patch(f"{SYNC_DATABASE_PATH}.create_engine", Mock(spec=Engine)):
		with patch(
			f"{SYNC_DATABASE_PATH}.sessionmaker",
			Mock(spec=sessionmaker[Session]),
		):
			logger = LoguruLogging()
			logger.setup(default_path=tmp_path, default_config=True)
			db_manager = SyncDatabaseManager(db_params=db_params, logging=logger)
			assert callable(db_manager.close)
			assert callable(db_manager.connect)
			assert callable(db_manager.session)
		assert "Engine setup correctly" in caplog.text

def test_connect(db_params: DefineGeneralDb, caplog: LogCaptureFixture, tmp_path: Path):
    mock_engine= Mock(spec=Engine)
    mock_connection = Mock(spec=Connection)

    # Create a proper context manager mock
    mock_context_manager = MagicMock()
    mock_context_manager.__enter__.return_value = mock_connection
    mock_context_manager.__exit__.return_value = None
    # Make engine.begin() return the context manager
    mock_engine.begin.return_value = mock_context_manager

    with patch(f"{SYNC_DATABASE_PATH}.create_engine", return_value=mock_engine):
        with patch(
            f"{SYNC_DATABASE_PATH}.sessionmaker",
            Mock(spec=sessionmaker[Session]),
        ):
            logger = LoguruLogging()
            logger.setup(default_path=tmp_path, default_config=True)
            sync_db_manager = SyncDatabaseManager(db_params=db_params, logging=logger)

            with sync_db_manager.connect() as conn:
                assert conn == mock_connection

            # Verify the context manager was used properly
            mock_engine.begin.assert_called_once()
            mock_context_manager.__enter__.assert_called_once()
            mock_context_manager.__exit__.assert_called_once()

    assert "Engine setup correctly" in caplog.text


def test_sync_connect_error(
	db_params: DefineGeneralDb, caplog: LogCaptureFixture, tmp_path: Path
):
	with patch(f"{SYNC_DATABASE_PATH}.create_engine", return_value=None):
		with patch(
			f"{SYNC_DATABASE_PATH}.sessionmaker",
			Mock(spec=sessionmaker[Session]),
		):
			logger = LoguruLogging()
			logger.setup(default_path=tmp_path, default_config=True)
			sync_db_manager = SyncDatabaseManager(db_params=db_params, logging=logger)
			with pytest.raises(ServiceError):
				with sync_db_manager.connect():
					pass

	assert "Engine is not available for connection" in caplog.text


def test_sync_connect_exception(
	db_params: DefineGeneralDb, caplog: LogCaptureFixture, tmp_path: Path
):
    mock_engine = Mock(spec=Engine)
    mock_connection = Mock(spec=Connection)

    # # Create a proper context manager mock
    mock_context_manager = MagicMock()
    mock_context_manager.__enter__.return_value = mock_connection
    mock_context_manager.__exit__.return_value = None
    # Make engine.begin() return the context manager
    mock_engine.begin.return_value = mock_context_manager


    with patch(f"{SYNC_DATABASE_PATH}.create_engine", return_value=mock_engine):
        with patch(
            f"{SYNC_DATABASE_PATH}.sessionmaker",
            Mock(spec=sessionmaker[Session]),
        ):
            logger = LoguruLogging()
            logger.setup(default_path=tmp_path, default_config=True)
            sync_db_manager = SyncDatabaseManager(db_params=db_params, logging=logger)

            with pytest.raises(ServiceError):
                with sync_db_manager.connect():
                    raise SQLAlchemyError("Simulated error")
            mock_connection.rollback.assert_called_once()

    assert "Database error while using sync connection" in caplog.text


def test_session(db_params: DefineGeneralDb, caplog: LogCaptureFixture, tmp_path: Path):
    mock_engine = Mock(spec=Engine)
    mock_session = Mock(spec=Session)

    # Create a mock sessionmaker that returns the mock session when called
    mock_sessionmaker = Mock(return_value=mock_session)

    with patch(f"{SYNC_DATABASE_PATH}.create_engine", return_value=mock_engine):
        with patch(
            f"{SYNC_DATABASE_PATH}.sessionmaker",
            return_value=mock_sessionmaker,
        ):
            logger = LoguruLogging()
            logger.setup(default_path=tmp_path, default_config=True)
            sync_db_manager = SyncDatabaseManager(db_params=db_params, logging=logger)
            with sync_db_manager.session() as session:
                assert session == mock_session

            # Verify session lifecycle
            mock_sessionmaker.assert_called_once()
            mock_session.close.assert_called_once()
    assert "Engine setup correctly" in caplog.text


def test_session_none_sessionmaker(
	db_params: DefineGeneralDb, caplog: LogCaptureFixture, tmp_path: Path
):
    mock_engine = Mock(spec=Engine)

    with patch(f"{SYNC_DATABASE_PATH}.create_engine", return_value=mock_engine):
        with patch(
            f"{SYNC_DATABASE_PATH}.sessionmaker",
            return_value=None,
        ):
            logger = LoguruLogging()
            logger.setup(default_path=tmp_path, default_config=True)
            db_manager = SyncDatabaseManager(db_params=db_params, logging=logger)
            with pytest.raises(ServiceError):
                with db_manager.session():
                    pass



    assert "Sessionmaker is not available" in caplog.text


def test_session_exception(
	db_params: DefineGeneralDb, caplog: LogCaptureFixture, tmp_path: Path
):
    mock_engine = Mock(spec=Engine)
    mock_session = Mock(spec=Session)

    # Create a mock sessionmaker that returns the mock session when called
    mock_sessionmaker = Mock(return_value=mock_session)

    with patch(f"{SYNC_DATABASE_PATH}.create_engine", return_value=mock_engine):
        with patch(
            f"{SYNC_DATABASE_PATH}.sessionmaker",
            return_value=mock_sessionmaker,
        ):
            logger = LoguruLogging()
            logger.setup(default_path=tmp_path, default_config=True)
            db_manager = SyncDatabaseManager(db_params=db_params, logging=logger)
            with pytest.raises(ServiceError):
                with db_manager.session():
                    raise SQLAlchemyError("Simulated error")

            # Verify session lifecycle
            mock_sessionmaker.assert_called_once()
            mock_session.close.assert_called_once()
    assert "Database error while using sync session" in caplog.text

def test_close(
	db_params: DefineGeneralDb, caplog: LogCaptureFixture, tmp_path: Path
):
	mock_engine = Mock(spec=Engine)
	mock_engine.dispose.return_value = None
	mock_session = Mock(spec=Session)

	# Create a mock sessionmaker that returns the mock session when called
	mock_sessionmaker = Mock(return_value=mock_session)

	with patch(f"{SYNC_DATABASE_PATH}.create_engine", return_value=mock_engine):
		with patch(
			f"{SYNC_DATABASE_PATH}.sessionmaker",
			return_value=mock_sessionmaker,
		):
			logger = LoguruLogging()
			logger.setup(default_path=tmp_path, default_config=True)
			sync_db_manager = SyncDatabaseManager(db_params=db_params, logging=logger)
			sync_db_manager.close()

			# Verify session lifecycle
			mock_engine.dispose.assert_called_once()
	assert "Database engine disposed" in caplog.text


def test_close_engine_none(
	db_params: DefineGeneralDb,
	caplog: LogCaptureFixture,
	tmp_path: Path,
):
	mock_session = Mock(spec=Session)

	# Create a mock sessionmaker that returns the mock session when called
	mock_sessionmaker = Mock(return_value=mock_session)

	with patch(
		f"{SYNC_DATABASE_PATH}.create_engine", return_value=None
	):
		with patch(
			f"{SYNC_DATABASE_PATH}.sessionmaker",
			return_value=mock_sessionmaker,
		):
			logger = LoguruLogging()
			logger.setup(default_path=tmp_path, default_config=True)
			sync_db_manager = SyncDatabaseManager(db_params=db_params, logging=logger)
			with pytest.raises(ServiceError):
				sync_db_manager.close()

	assert "Attempted to close a non-existing engine" in caplog.text


async def test_async_close_engine_exception(
	db_params: DefineGeneralDb,
	caplog: LogCaptureFixture,
	tmp_path: Path,
):
	mock_engine = Mock(spec=Engine)
	mock_engine.dispose.side_effect = SQLAlchemyError()
	mock_session = Mock(spec=Session)

	# Create a mock sessionmaker that returns the mock session when called
	mock_sessionmaker = Mock(return_value=mock_session)

	with patch(
		f"{SYNC_DATABASE_PATH}.create_engine", return_value=mock_engine
	):
		with patch(
			f"{SYNC_DATABASE_PATH}.sessionmaker",
			return_value=mock_sessionmaker,
		):
			logger = LoguruLogging()
			logger.setup(default_path=tmp_path, default_config=True)
			sync_db_manager = SyncDatabaseManager(db_params=db_params, logging=logger)
			with pytest.raises(ServiceError):
				sync_db_manager.close()

	assert "Error while disposing database engine" in caplog.text
