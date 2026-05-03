"""
Centralized logging setup for Job Agent Alerter.
"""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


LOGGER_NAME = "JobAgent"
MAX_BYTES = 5 * 1024 * 1024  # 5 MB
BACKUP_COUNT = 5

_LOGGER: logging.Logger | None = None


def _build_handler(path: Path, level: int) -> RotatingFileHandler:
    handler = RotatingFileHandler(
        filename=path,
        maxBytes=MAX_BYTES,
        backupCount=BACKUP_COUNT,
        encoding="utf-8",
    )
    handler.setLevel(level)
    return handler


def get_logger() -> logging.Logger:
    """
    Return a singleton logger configured for console + rotating file logs.
    """
    global _LOGGER
    if _LOGGER is not None:
        return _LOGGER

    root_dir = Path(__file__).resolve().parents[1]
    logs_dir = root_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    app_log_path = logs_dir / "app.log"
    error_log_path = logs_dir / "error.log"
    app_log_path.touch(exist_ok=True)
    error_log_path.touch(exist_ok=True)

    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    if logger.handlers:
        _LOGGER = logger
        return logger

    log_format = "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter(log_format, datefmt=date_format)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    app_handler = _build_handler(app_log_path, logging.INFO)
    app_handler.setFormatter(formatter)

    error_handler = _build_handler(error_log_path, logging.ERROR)
    error_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(app_handler)
    logger.addHandler(error_handler)

    _LOGGER = logger
    return logger
