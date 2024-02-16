import atexit
from logging import LogRecord
import datetime as dt
import logging
import logging.config
import pathlib
import json
from typing import Any, override


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
                record.created, tz=dt.timezone.utc
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


# get logger
logger = logging.getLogger("my_app")


def setup_logging() -> None:
    config_file = pathlib.Path("tools/logger.config.json")
    with open(config_file) as f_in:
        config: dict[str, Any] = json.load(f_in)
    logging.config.dictConfig(config)
    if (queue_handler := logging.getHandlerByName("queue_handler")) is not None:
        queue_handler.listener.start()
        atexit.register(queue_handler.listener.stop)
