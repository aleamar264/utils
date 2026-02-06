from database.general import ServiceError
import atexit
import datetime as dt
import json
import logging
import logging.config
import sys
from logging import LogRecord
from pathlib import Path
from typing import Any, Protocol, TypeVar, override, runtime_checkable

from loguru import logger as _logger
from loguru._logger import Logger as LoguruLogger

T = TypeVar("T", covariant=True)


class MyJSONFormatter(logging.Formatter):
	def __init__(self, *, fmt: dict[str, str] | None = None):
		super().__init__()
		self.fmt = fmt if fmt is not None else {}

	@override
	def format(self, record: LogRecord) -> str:
		message = self._prepare_log_dict(record)
		return json.dumps(message, default=str)

	def _prepare_log_dict(self, record: LogRecord):
		always_fields = {
			"message": record.getMessage(),
			"timestamp": dt.datetime.fromtimestamp(
				record.created, tz=dt.UTC
			).isoformat(),
		}

		if record.exc_info is not None:
			always_fields["exc_info"] = self.formatException(record.exc_info)

		if record.stack_info is not None:
			always_fields["stack_info"] = self.formatStack(record.stack_info)

		message = {
			key: msg_val
			if (msg_val := always_fields.pop(val, None)) is not None
			else getattr(record, val)
			for key, val in self.fmt.items()
		}
		message.update(always_fields)
		return message


@runtime_checkable
class LoggingSetup(Protocol[T]):
	def setup(self, **kwargs) -> None:
		"""
		Docstring for setup

		:param self: Description
		:param config_path: Description
		:type config_path: Path

		Example:
            ```python
            config_path = Path.cwd() / "logger.config.json"
            LoguruLoggin().setup(config_path)
            ```
		"""

	def get_logger(self, name: str) -> T: ...


class BuiltinLogging:
	_configured = False

	def setup(self, config_path: Path, default_config: bool = True) -> None:
		"""
        Docstring for setup

        :param config_path: For the builtin logging you can use
        a file to setup the logger. The file logger.config.json is used by default
        :type config_path: Path
        :param default_config: If this enabled, the file used is logger.config.json.
        If this is enabled, the config_path is ignored and use the default.\
        To use the user config_path, set this in *False*
        :type default_config: bool

        Example:
            ```python
            config_path = Path.cwd() / "logger.config.json"
            BuiltinLogging().setup(config_path=config_path, default_path=False)
            ```
        """
		if self._configured:
			return

		if default_config:
			_config_path = Path.cwd() / "logger.config.json"
		else:
			_config_path = config_path
		with _config_path.open(encoding="utf-8") as f:
			config = json.load(f)

		logging.config.dictConfig(config)

		if (qh := logging.getHandlerByName("queue_handler")) is not None:
			qh.listener.start()
			atexit.register(qh.listener.stop)

		self._configured = True

	def get_logger(self, name: str) -> logging.Logger:
		return logging.getLogger(name)


class LoguruLogging:
	_configured = False

	def setup(
		self, logs_sinks: list[dict[str, Any]] | None = None, 
		default_config: bool = False,
		default_path: Path = Path().parent / "log"
	) -> None:
		"""
		Docstring for setup

		:param self: Description
		:param logs_sinks: A list of dictionary with the configuration for each configuration for the logger.
		:type logs_sinks: list[dict[str, Any]
		:param default_config: If this is set True, this will use the following configuration:
            ```python
            # 1️⃣ STDERR — human readable, WARNING+
            logger.add(
                sys.stderr,
                level="WARNING",
                format="<level>{level}</level>: {message}",
                enqueue=True,  # async & multiprocess-safe
            )

            # 2️⃣ FILE — JSON logs, DEBUG+, rotating
            # Where the LOG_DIR will be a folder call log
            logger.add(
                LOG_DIR / "my_app.log.jsonl",
                level="DEBUG",
                serialize=True,  # JSON output
                rotation="10 KB",  # maxBytes: 10000
                retention=7,  # backupCount: 7
                enqueue=True,
            )
            ```
		:type default_config: bool

		Example:
            ```python
            config_path = Path.cwd() / "logger.config.json"
            LoguruLoggin().setup(config_path)
            ```
		"""
		if self._configured:
			return
		if default_config:
			_logger.add(
				sys.stderr,
				level="INFO",
				format="<level>{level}</level>: {message}",
				enqueue=True,  # async & multiprocess-safe
			)
			default_path.mkdir(exist_ok=True, parents=True)
			_logger.add(
				default_path / "my_log.log.jsonl",
				level="DEBUG",
				serialize=True,  # JSON output
				rotation="10 KB",  # maxBytes: 10000
				retention=7,  # backupCount: 7
				enqueue=True,
			)
			self._configured = True
			return
		if logs_sinks is None:
			raise ServiceError("log_sinks should be a valid list of dictionary \
				with loguru configurations")
		for i, log_sink in enumerate(logs_sinks, start=1):
			try:
				_logger.add(**log_sink)
			except Exception as exc:
				raise RuntimeError(
					f"Invalid log sink configuration at index {i}: {log_sink}"
				) from exc

		self._configured = True

	def get_logger(self, name: str) -> LoguruLogger:
		# Context, not identity
		return _logger.bind(service=name)
