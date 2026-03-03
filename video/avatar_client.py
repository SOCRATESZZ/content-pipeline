"""AvatarClient wraps the HeyGen REST API v2 for avatar video generation."""

import time

import httpx

from utils.logger import logger

HEYGEN_GENERATE_ENDPOINT = "https://api.heygen.com/v2/video/generate"
HEYGEN_STATUS_ENDPOINT = "https://api.heygen.com/v1/video_status.get"
AVATAR_DIMENSION_WIDTH = 1080
AVATAR_DIMENSION_HEIGHT = 1920
STATUS_COMPLETED = "completed"
STATUS_FAILED = "failed"


class AvatarError(Exception):
    """Raised when avatar video creation or polling fails."""


class AvatarClient:
    """Creates and polls HeyGen avatar videos via the v2 REST API.

    Args:
        http_client: A configured httpx.Client for API calls.
        api_key: HeyGen API key for authentication.
        poll_interval_seconds: Seconds to wait between status poll requests.
        poll_timeout_seconds: Maximum seconds to wait for video completion.
    """

    def __init__(
        self,
        http_client: httpx.Client,
        api_key: str,
        poll_interval_seconds: int,
        poll_timeout_seconds: int,
    ) -> None:
        """Initialise the AvatarClient with HTTP client and config."""
        self._http_client = http_client
        self._api_key = api_key
        self._poll_interval_seconds = poll_interval_seconds
        self._poll_timeout_seconds = poll_timeout_seconds

    def create_video(self, audio_url: str, avatar_id: str) -> str:
        """Submit a video generation request and return the job ID.

        Args:
            audio_url: S3 URL of the pre-generated audio file.
            avatar_id: HeyGen avatar identifier to animate.

        Returns:
            The HeyGen job ID string.
        """
        payload = {
            "video_inputs": [{
                "character": {"type": "avatar", "avatar_id": avatar_id},
                "voice": {"type": "audio", "audio_url": audio_url},
            }],
            "dimension": {"width": AVATAR_DIMENSION_WIDTH, "height": AVATAR_DIMENSION_HEIGHT},
        }
        headers = {"X-Api-Key": self._api_key, "Content-Type": "application/json"}
        logger.info("AvatarClient: submitting video generation for avatar '{}'", avatar_id)
        try:
            response = self._http_client.post(HEYGEN_GENERATE_ENDPOINT, json=payload, headers=headers)
            response.raise_for_status()
            job_id: str = response.json()["data"]["video_id"]
            logger.info("AvatarClient: video job created: {}", job_id)
            return job_id
        except (httpx.HTTPStatusError, httpx.RequestError, KeyError) as error:
            logger.error("AvatarClient: create_video failed: {}", error)
            raise AvatarError(f"HeyGen video creation failed: {error}") from error

    def poll_video_status(self, job_id: str) -> str:
        """Poll HeyGen until the video is complete and return the video URL.

        Args:
            job_id: HeyGen job identifier to poll.

        Returns:
            The public URL of the completed video.
        """
        deadline = time.monotonic() + self._poll_timeout_seconds
        headers = {"X-Api-Key": self._api_key}
        logger.info("AvatarClient: polling job {} (timeout={}s)", job_id, self._poll_timeout_seconds)
        while time.monotonic() < deadline:
            try:
                response = self._http_client.get(
                    HEYGEN_STATUS_ENDPOINT,
                    params={"video_id": job_id},
                    headers=headers,
                )
                response.raise_for_status()
                data = response.json().get("data", {})
                status = data.get("status", "")
                if status == STATUS_COMPLETED:
                    video_url: str = data["video_url"]
                    logger.info("AvatarClient: job {} completed", job_id)
                    return video_url
                if status == STATUS_FAILED:
                    raise AvatarError(f"HeyGen job {job_id} failed with status: {status}")
                logger.debug("AvatarClient: job {} status='{}', waiting {}s", job_id, status, self._poll_interval_seconds)
                time.sleep(self._poll_interval_seconds)
            except (httpx.HTTPStatusError, httpx.RequestError) as error:
                logger.error("AvatarClient: poll request error: {}", error)
                raise AvatarError(f"Polling failed for job {job_id}: {error}") from error
        raise AvatarError(f"HeyGen job {job_id} timed out after {self._poll_timeout_seconds}s")
