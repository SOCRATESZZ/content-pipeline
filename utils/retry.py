"""Exponential backoff retry decorator for external API calls."""

import time
import functools
from typing import Callable, Type, TypeVar

from loguru import logger

INITIAL_DELAY_SECONDS = 1.0
BACKOFF_MULTIPLIER = 2.0
MAX_DELAY_SECONDS = 60.0

F = TypeVar("F", bound=Callable)


def retry_with_backoff(
    max_attempts: int = 3,
    base_delay_seconds: float = INITIAL_DELAY_SECONDS,
    exceptions: tuple[Type[Exception], ...] = (Exception,),
) -> Callable[[F], F]:
    """Decorate a function with exponential backoff retry logic.

    Args:
        max_attempts: Total number of attempts before raising.
        base_delay_seconds: Initial delay between retries.
        exceptions: Exception types that trigger a retry.

    Returns:
        Decorator that wraps the target function with retry logic.
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            delay = base_delay_seconds
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as error:
                    if attempt == max_attempts:
                        logger.error(
                            "All {} attempts failed for {}: {}",
                            max_attempts, func.__name__, error,
                        )
                        raise
                    logger.warning(
                        "Attempt {}/{} failed for {}: {}. Retrying in {:.1f}s.",
                        attempt, max_attempts, func.__name__, error, delay,
                    )
                    time.sleep(delay)
                    delay = min(delay * BACKOFF_MULTIPLIER, MAX_DELAY_SECONDS)
        return wrapper  # type: ignore[return-value]
    return decorator
