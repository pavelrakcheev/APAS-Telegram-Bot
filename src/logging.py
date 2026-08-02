"""Structured logging configuration for APAS."""

import logging
import sys
from typing import Any


def setup_logging(level: str = "INFO", json_output: bool = False) -> None:
    """
    Configure structured logging for APAS.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_output: If True, output logs in JSON format
    """
    try:
        import structlog
        HAS_STRUCTLOG = True
    except ImportError:
        HAS_STRUCTLOG = False

    if HAS_STRUCTLOG:
        # Configure structlog
        structlog.configure(
            processors=[
                structlog.contextvars.merge_contextvars,
                structlog.processors.add_log_level,
                structlog.processors.StackInfoRenderer(),
                structlog.dev.set_exc_info,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.JSONRenderer() if json_output else structlog.dev.ConsoleRenderer(),
            ],
            wrapper_class=structlog.make_filtering_bound_logger(
                getattr(logging, level.upper(), logging.INFO)
            ),
            context_class=dict,
            logger_factory=structlog.PrintLoggerFactory(),
            cache_logger_on_first_use=True,
        )
    else:
        # Fallback to standard logging
        logging.basicConfig(
            format="%(asctime)s | %(levelname)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            level=getattr(logging, level.upper(), logging.INFO),
            stream=sys.stdout,
        )


def get_logger(name: str) -> Any:
    """
    Get a logger instance.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    try:
        import structlog
        return structlog.get_logger(name)
    except ImportError:
        return logging.getLogger(name)


# Convenience logger for the project
logger = get_logger("apas")
