"""Shared async HTTP client factory using httpx."""

from typing import Optional
import httpx

DEFAULT_TIMEOUT_SECONDS = 30.0
DEFAULT_MAX_CONNECTIONS = 20


def build_async_client(
    base_url: str = "",
    headers: Optional[dict[str, str]] = None,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
) -> httpx.AsyncClient:
    """Build and return a configured async HTTP client.

    Args:
        base_url: Optional base URL prepended to all requests.
        headers: Optional default headers sent with every request.
        timeout_seconds: Request timeout in seconds.

    Returns:
        A configured httpx.AsyncClient instance.
    """
    return httpx.AsyncClient(
        base_url=base_url,
        headers=headers or {},
        timeout=httpx.Timeout(timeout_seconds),
        limits=httpx.Limits(max_connections=DEFAULT_MAX_CONNECTIONS),
    )


def build_sync_client(
    base_url: str = "",
    headers: Optional[dict[str, str]] = None,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
) -> httpx.Client:
    """Build and return a configured synchronous HTTP client.

    Args:
        base_url: Optional base URL prepended to all requests.
        headers: Optional default headers sent with every request.
        timeout_seconds: Request timeout in seconds.

    Returns:
        A configured httpx.Client instance.
    """
    return httpx.Client(
        base_url=base_url,
        headers=headers or {},
        timeout=httpx.Timeout(timeout_seconds),
        limits=httpx.Limits(max_connections=DEFAULT_MAX_CONNECTIONS),
    )
