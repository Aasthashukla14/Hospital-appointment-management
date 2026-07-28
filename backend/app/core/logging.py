"""
Centralized logging configuration.

Provides a `configure_logging()` entry point called once at app startup,
and a `get_logger(name)` helper used throughout the codebase so all
modules share consistent formatting.
"""
import logging
import sys
from logging.config import dictConfig

from app.core.config import settings


class RequestIdFilter(logging.Filter):
    """Injects the current request id (set by middleware) into log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        from app.middleware.request_id_middleware import request_id_ctx_var

        record.request_id = request_id_ctx_var.get()
        return True


def configure_logging() -> None:
    log_format = (
        '{"time": "%(asctime)s", "level": "%(levelname)s", '
        '"request_id": "%(request_id)s", "logger": "%(name)s", '
        '"message": "%(message)s"}'
        if settings.LOG_JSON
        else "%(asctime)s | %(levelname)-8s | req=%(request_id)s | %(name)s | %(message)s"
    )

    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "filters": {
                "request_id": {"()": RequestIdFilter},
            },
            "formatters": {
                "default": {"format": log_format},
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "stream": sys.stdout,
                    "formatter": "default",
                    "filters": ["request_id"],
                    "level": settings.LOG_LEVEL,
                },
            },
            "root": {
                "handlers": ["console"],
                "level": settings.LOG_LEVEL,
            },
            "loggers": {
                "uvicorn": {"handlers": ["console"], "level": settings.LOG_LEVEL, "propagate": False},
                "uvicorn.access": {"handlers": ["console"], "level": settings.LOG_LEVEL, "propagate": False},
                "sqlalchemy.engine": {
                    "handlers": ["console"],
                    "level": "INFO" if settings.DB_ECHO else "WARNING",
                    "propagate": False,
                },
            },
        }
    )


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
