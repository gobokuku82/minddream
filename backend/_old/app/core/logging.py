"""Logging Utilities

Agent 실행에 필요한 로깅 유틸리티.
"""

import logging
import sys
from typing import Optional, Any
from contextlib import contextmanager


def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """Get or create a logger with the specified name."""
    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)s [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    logger.setLevel(level)
    return logger


class LogContext:
    """Context manager for structured logging."""

    def __init__(
        self,
        logger: logging.Logger,
        operation: Optional[str] = None,
        session_id: Optional[str] = None,
        *,
        node: Optional[str] = None,
        **extra: Any
    ):
        self.logger = logger
        self.operation = operation or node or "unknown"
        self.session_id = session_id
        self.extra = extra

    def __enter__(self):
        msg = f"Starting: {self.operation}"
        if self.session_id:
            msg += f" [session={self.session_id}]"
        self.logger.info(msg)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.logger.error(
                f"Failed: {self.operation} - {exc_type.__name__}: {exc_val}"
            )
        else:
            self.logger.info(f"Completed: {self.operation}")
        return False

    def log(self, message: str, level: int = logging.INFO):
        """Log a message within this context."""
        self.logger.log(level, f"[{self.operation}] {message}")

    def info(self, message: str):
        self.logger.info(f"[{self.operation}] {message}")

    def warning(self, message: str):
        self.logger.warning(f"[{self.operation}] {message}")

    def error(self, message: str, exc_info: bool = False):
        self.logger.error(f"[{self.operation}] {message}", exc_info=exc_info)

    def debug(self, message: str):
        self.logger.debug(f"[{self.operation}] {message}")
