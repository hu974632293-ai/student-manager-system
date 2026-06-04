import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

from dotenv import load_dotenv


DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_LOG_DIR = "logs"
DEFAULT_LOG_MAX_BYTES = 10 * 1024 * 1024
DEFAULT_LOG_BACKUP_COUNT = 5


def _get_log_level() -> int:
    level_name = os.getenv("LOG_LEVEL", DEFAULT_LOG_LEVEL).strip().upper()
    return getattr(logging, level_name, logging.INFO)


def _get_positive_int(env_name: str, default: int) -> int:
    value = os.getenv(env_name)
    if value is None:
        return default
    try:
        parsed_value = int(value)
    except ValueError:
        return default
    return parsed_value if parsed_value > 0 else default


def _create_file_handler(
    log_file: Path,
    formatter: logging.Formatter,
    level: int,
    max_bytes: int,
    backup_count: int,
) -> RotatingFileHandler:
    handler = RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    handler.setLevel(level)
    handler.setFormatter(formatter)
    return handler


def configure_logging() -> logging.Logger:
    load_dotenv()

    app_logger = logging.getLogger("student_manager")
    app_logger.setLevel(_get_log_level())
    app_logger.propagate = False

    if app_logger.handlers:
        for handler in app_logger.handlers:
            handler.setLevel(logging.ERROR if getattr(handler, "_error_only", False) else _get_log_level())
        return app_logger

    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    log_dir = Path(os.getenv("LOG_DIR", DEFAULT_LOG_DIR))
    log_dir.mkdir(parents=True, exist_ok=True)

    max_bytes = _get_positive_int("LOG_MAX_BYTES", DEFAULT_LOG_MAX_BYTES)
    backup_count = _get_positive_int("LOG_BACKUP_COUNT", DEFAULT_LOG_BACKUP_COUNT)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(_get_log_level())
    console_handler.setFormatter(formatter)
    app_logger.addHandler(console_handler)

    app_handler = _create_file_handler(
        log_dir / "app.log",
        formatter,
        _get_log_level(),
        max_bytes,
        backup_count,
    )
    app_logger.addHandler(app_handler)

    error_handler = _create_file_handler(
        log_dir / "error.log",
        formatter,
        logging.ERROR,
        max_bytes,
        backup_count,
    )
    error_handler._error_only = True
    app_logger.addHandler(error_handler)

    return app_logger


def get_logger(name: str) -> logging.Logger:
    configure_logging()
    return logging.getLogger(f"student_manager.{name}")


logger = configure_logging()
