"""Application logging setup with rotating file handler."""
from __future__ import annotations

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


_logger: logging.Logger | None = None

LOG_FORMAT = "[%(asctime)s] %(levelname)s: %(message)s"
LOG_FILE_NAME = "ts2mp4.log"
LOG_MAX_BYTES = 5 * 1024 * 1024  # 5 MB
LOG_BACKUP_COUNT = 3


def _get_log_dir() -> Path:
    """Determine the log file directory.

    When running as a frozen PyInstaller bundle, log lives next to the exe.
    Otherwise, log in the project root or current working directory.
    """
    if getattr(sys, "frozen", False):
        # Running as PyInstaller bundle
        return Path(sys.executable).parent
    else:
        # Development mode — use project root
        return Path.cwd()


def setup_logger() -> logging.Logger:
    """Set up and return the application-wide logger.

    Configures a RotatingFileHandler (5MB max, 3 backups) with the
    format: [%(asctime)s] %(levelname)s: %(message)s

    Returns:
        The configured logger instance.
    """
    global _logger
    if _logger is not None:
        return _logger

    logger = logging.getLogger("ts2mp4")
    logger.setLevel(logging.INFO)

    # Avoid duplicate handlers if called multiple times
    if not logger.handlers:
        log_dir = _get_log_dir()
        log_file = log_dir / LOG_FILE_NAME

        try:
            file_handler = RotatingFileHandler(
                str(log_file),
                maxBytes=LOG_MAX_BYTES,
                backupCount=LOG_BACKUP_COUNT,
                encoding="utf-8",
            )
            file_handler.setLevel(logging.INFO)
            file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
            logger.addHandler(file_handler)
        except OSError:
            # If we can't write to the log file, fall back to stderr
            pass

        # Also log to stderr in development mode
        if not getattr(sys, "frozen", False):
            console_handler = logging.StreamHandler(sys.stderr)
            console_handler.setLevel(logging.WARNING)
            console_handler.setFormatter(logging.Formatter(LOG_FORMAT))
            logger.addHandler(console_handler)

    _logger = logger
    return logger


def get_logger() -> logging.Logger:
    """Get the application logger, initializing it if needed.

    Returns:
        The application logger instance.
    """
    global _logger
    if _logger is None:
        return setup_logger()
    return _logger
