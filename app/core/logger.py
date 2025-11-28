import uuid
import logging
import json
import sys
from datetime import datetime
from contextvars import ContextVar
from logging.handlers import RotatingFileHandler

request_id_ctx: ContextVar[str] = ContextVar("request_id", default="client")


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_record = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "request_id": request_id_ctx.get(),
        }

        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)

        if hasattr(record, "extras"):
            log_record["extras"] = record.extras

        return json.dumps(log_record)


def setup_logging(log_level: str = "INFO", log_file: str = "app.log") -> None:
    logger = logging.getLogger()
    logger.setLevel(log_level.upper())
    logger.handlers.clear()

    formatter = JsonFormatter()

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    file_handler = logging.FileHandler(log_file)
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024, # 10 MB
        backupCount=5
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)


def set_request_id(request_id: str | None= None) -> str:
    if not request_id:
        request_id = str(uuid.uuid4())
    request_id_ctx.set(request_id)
    return request_id

def get_request_id() -> str:
    return request_id_ctx.get()
