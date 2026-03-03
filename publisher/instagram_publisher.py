"""InstagramPublisher publishes Reels and Carousels via the Graph API v18."""

from datetime import datetime

import httpx

from config import InstagramSettings
from models.publish_result import PublishResult
from models.video import VideoAsset
from publisher.base import BasePublisher, PublishError
from utils.logger import logger

INSTAGRAM_GRAPH_API_BASE_URL = "https://graph.facebook.com/v18.0"
MEDIA_TYPE_REELS = "REELS"
MEDIA_TYPE_IMAGE = "IMAGE"
MEDIA_TYPE_CAROUSEL = "CAROUSEL"
PUBLISH_PLATFORM = "instagram"


class InstagramPublisher(BasePublisher):
    """Publishes video Reels and image Carousels to Instagram via Graph API.

    Args:
        http_client: A configured httpx.Client.
        settings: InstagramSettings with access token and user ID.
    """

    def __init__(self, http_client: httpx.Client, settings: InstagramSettings) -> None:
        """Initialise the InstagramPublisher with an HTTP client and credentials."""
        self._client = http_client
        self._settings = settings

    def publish(self, video: VideoAsset, caption: str) -> PublishResult:
        """Publish a video as an Instagram Reel.

        Args:
            video: The VideoAsset to publish.
            caption: Text caption for the Reel.

        Returns:
            A PublishResult with the published post URL and ID.
        """
        return self.publish_reel(video, caption)

    def publish_reel(self, video: VideoAsset, caption: str) -> PublishResult:
        """Upload a video and publish it as an Instagram Reel.

        Args:
            video: VideoAsset containing the final video URL.
            caption: Caption text to attach to the Reel.

        Returns:
            A PublishResult for the published Reel.
        """
        logger.info("InstagramPublisher: uploading Reel for '{}'", video.script.idea.trend_item.title)
        try:
            container_id = self._create_reel_container(video.final_url, caption)
            post_id = self._publish_container(container_id)
            post_url = f"https://www.instagram.com/p/{post_id}/"
            logger.info("InstagramPublisher: Reel published as {}", post_url)
            return PublishResult(
                video=video, platform=PUBLISH_PLATFORM, post_id=post_id,
                post_url=post_url, success=True, published_at=datetime.utcnow(),
            )
        except Exception as error:
            logger.error("InstagramPublisher: Reel publish failed: {}", error)
            raise PublishError(f"Instagram Reel publish failed: {error}") from error

    def publish_carousel(self, slides: list[str], caption: str) -> PublishResult:
        """Upload multiple images and publish them as an Instagram Carousel.

        Args:
            slides: List of public image URLs to include in the carousel.
            caption: Caption text to attach to the Carousel.

        Returns:
            A PublishResult for the published Carousel.
        """
        logger.info("InstagramPublisher: creating Carousel with {} slides", len(slides))
        try:
            child_ids = [self._create_image_container(url) for url in slides]
            carousel_id = self._create_carousel_container(child_ids, caption)
            post_id = self._publish_container(carousel_id)
            post_url = f"https://www.instagram.com/p/{post_id}/"
            logger.info("InstagramPublisher: Carousel published as {}", post_url)
            return PublishResult(
                video=VideoAsset.__new__(VideoAsset), platform=PUBLISH_PLATFORM,
                post_id=post_id, post_url=post_url, success=True, published_at=datetime.utcnow(),
            )
        except Exception as error:
            logger.error("InstagramPublisher: Carousel publish failed: {}", error)
            raise PublishError(f"Instagram Carousel publish failed: {error}") from error

    def _create_reel_container(self, video_url: str, caption: str) -> str:
        """Create a media container for a Reel and return its ID."""
        response = self._client.post(
            f"{INSTAGRAM_GRAPH_API_BASE_URL}/{self._settings.user_id}/media",
            params={
                "video_url": video_url,
                "media_type": MEDIA_TYPE_REELS,
                "caption": caption,
                "access_token": self._settings.access_token,
            },
        )
        response.raise_for_status()
        return response.json()["id"]

    def _create_image_container(self, image_url: str) -> str:
        """Create a media container for a carousel image and return its ID."""
        response = self._client.post(
            f"{INSTAGRAM_GRAPH_API_BASE_URL}/{self._settings.user_id}/media",
            params={
                "image_url": image_url,
                "media_type": MEDIA_TYPE_IMAGE,
                "is_carousel_item": True,
                "access_token": self._settings.access_token,
            },
        )
        response.raise_for_status()
        return response.json()["id"]

    def _create_carousel_container(self, child_ids: list[str], caption: str) -> str:
        """Create a carousel container with the given child image IDs."""
        response = self._client.post(
            f"{INSTAGRAM_GRAPH_API_BASE_URL}/{self._settings.user_id}/media",
            params={
                "media_type": MEDIA_TYPE_CAROUSEL,
                "children": ",".join(child_ids),
                "caption": caption,
                "access_token": self._settings.access_token,
            },
        )
        response.raise_for_status()
        return response.json()["id"]

    def _publish_container(self, container_id: str) -> str:
        """Publish a previously created media container and return the post ID."""
        response = self._client.post(
            f"{INSTAGRAM_GRAPH_API_BASE_URL}/{self._settings.user_id}/media_publish",
            params={
                "creation_id": container_id,
                "access_token": self._settings.access_token,
            },
        )
        response.raise_for_status()
        return response.json()["id"]
