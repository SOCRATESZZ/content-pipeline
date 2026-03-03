"""Abstract base class and error for all social media publishers."""

from abc import ABC, abstractmethod

from models.publish_result import PublishResult
from models.video import VideoAsset


class PublishError(Exception):
    """Raised when a publish operation fails."""


class BasePublisher(ABC):
    """Abstract interface for publishing a video to a social media platform."""

    @abstractmethod
    def publish(self, video: VideoAsset, caption: str) -> PublishResult:
        """Publish a video asset with a caption to the platform.

        Args:
            video: The VideoAsset to publish.
            caption: Text caption or description to accompany the post.

        Returns:
            A PublishResult describing the outcome of the publish action.
        """
