import io
import json
import logging
import sys

import pytest
from database.general import ServiceError
from logger.logger import BuiltinLogging, LoguruLogging, MyJSONFormatter


def test_myjsonformatter_formats_json():
    logger = logging.getLogger("test_myjsonformatter")
    logger.setLevel(logging.DEBUG)

    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    fmt = {"msg": "message", "time": "timestamp"}
    handler.setFormatter(MyJSONFormatter(fmt=fmt))
    logger.addHandler(handler)

    logger.info("hello world")

    handler.flush()
    text = stream.getvalue().strip()
    assert text
    data = json.loads(text)
    assert data["msg"] == "hello world"
    assert "time" in data

    logger.removeHandler(handler)


def test_builtin_logging_setup_and_get_logger(tmp_path):
    config = {
        "version": 1,
        "formatters": {"simple": {"format": "%(levelname)s:%(name)s:%(message)s"}},
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "DEBUG",
                "formatter": "simple",
                "stream": "ext://sys.stdout",
            }
        },
        "root": {"level": "DEBUG", "handlers": ["console"]},
    }

    config_path = tmp_path / "logger.config.json"
    config_path.write_text(__import__("json").dumps(config))

    bl = BuiltinLogging()
    bl.setup(config_path=config_path, default_config=False)
    lg = bl.get_logger("unit_test")
    assert isinstance(lg, logging.Logger)


def test_loguru_logging_setup_and_get_logger():
    ll = LoguruLogging()
    # provide a simple sink to avoid touching filesystem
    ll.setup(logs_sinks=[{"sink": sys.stderr, "level": "INFO"}], default_config=False)
    logger = ll.get_logger("svc")
    from loguru._logger import Logger as LoguruLogger

    assert isinstance(logger, LoguruLogger)
    # should be able to call logging methods
    logger.info("loguru test message")


def test_loguru_default_path(tmp_path):
    l1 = LoguruLogging()
    l1.setup(default_config=True, default_path=tmp_path / 'log')


def test_error_sinks():
    l1 = LoguruLogging()
    with pytest.raises(ServiceError) as exc:
        l1.setup(logs_sinks=None)
    assert exc.value.args[0] == "log_sinks should be a valid list of dictionary \
				with loguru configurations"

def test_invalid_sink_config():
    ll = LoguruLogging()
    # provide a simple sink to avoid touching filesystem
    with pytest.raises(RuntimeError) as exc:
        ll.setup(logs_sinks=[{}], default_config=False)
    assert exc.value.args[0] == "Invalid log sink configuration at index 1: {}"

def test_loggiing_setup_protocol():
    """Test that implementations satisfy the LoggingSetup protocol."""
    from logger.logger import LoggingSetup

    # Test BuiltinLogging satisfies the protocol
    bl = BuiltinLogging()
    assert isinstance(bl, LoggingSetup)

    # Test LoguruLogging satisfies the protocol
    ll = LoguruLogging()
    assert isinstance(ll, LoggingSetup)

def test_protocol_methods_exist():
    """Verify protocol methods are callable."""
    bl = BuiltinLogging()
    assert callable(bl.setup)
    assert callable(bl.get_logger)

