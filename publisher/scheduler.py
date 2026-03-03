"""Scheduler wraps the Ayrshare API for timed social media publishing."""

from datetime import datetime

import httpx

from publisher.base import BasePublisher
from utils.logger import logger

AYRSHARE_SCHEDULE_ENDPOINT = "https://app.ayrshare.com/api/post"


class SchedulerError(Exception):
    """Raised when scheduling a post via Ayrshare fails."""


class Scheduler:
    """Schedules posts to be published at a future time via the Ayrshare API.

    Args:
        http_client: A configured httpx.Client for API calls.
        api_key: Ayrshare API key for authentication.
    """

    def __init__(self, http_client: httpx.Client, api_key: str) -> None:
        """Initialise the Scheduler with HTTP client and Ayrshare credentials."""
        self._client = http_client
        self._api_key = api_key

    def schedule_post(
        self,
        publisher: BasePublisher,
        post_data: dict,
        post_at: datetime,
    ) -> str:
        """Schedule a post to be published at a specified time.

        Args:
            publisher: The BasePublisher instance that will execute the post.
            post_data: Platform-specific post payload dictionary.
            post_at: UTC datetime when the post should be published.

        Returns:
            The Ayrshare post ID string for the scheduled post.
        """
        schedule_iso = post_at.strftime("%Y-%m-%dT%H:%M:%SZ")
        platform_name = type(publisher).__name__.replace("Publisher", "").lower()
        payload = {
            **post_data,
            "scheduleDate": schedule_iso,
            "platforms": [platform_name],
        }
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        logger.info("Scheduler: scheduling post on {} at {}", platform_name, schedule_iso)
        try:
            response = self._client.post(AYRSHARE_SCHEDULE_ENDPOINT, json=payload, headers=headers)
            response.raise_for_status()
            post_id: str = response.json().get("id", "")
            logger.info("Scheduler: post scheduled with id={}", post_id)
            return post_id
        except (httpx.HTTPStatusError, httpx.RequestError) as error:
            logger.error("Scheduler: scheduling failed: {}", error)
            raise SchedulerError(f"Ayrshare scheduling failed: {error}") from error
