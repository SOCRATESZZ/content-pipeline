"""Structured logging configuration using loguru."""

import sys
from loguru import logger

LOG_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
    "<level>{message}</level>"
)

LOG_FILE_PATH = "logs/pipeline_{time:YYYY-MM-DD}.log"
LOG_FILE_ROTATION = "00:00"
LOG_FILE_RETENTION = "7 days"
LOG_LEVEL = "DEBUG"


def configure_logger() -> None:
    """Configure loguru with console and rotating file sinks."""
    logger.remove()
    logger.add(sys.stderr, format=LOG_FORMAT, level=LOG_LEVEL, colorize=True)
    logger.add(
        LOG_FILE_PATH,
        format=LOG_FORMAT,
        level=LOG_LEVEL,
        rotation=LOG_FILE_ROTATION,
        retention=LOG_FILE_RETENTION,
        serialize=False,
    )


__all__ = ["configure_logger", "logger"]
