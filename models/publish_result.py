"""PublishResult model representing the outcome of a platform publish action."""

from dataclasses import dataclass, field
from datetime import datetime
from .video import VideoAsset


@dataclass
class PublishResult:
    """The result of publishing a video to a social media platform.

    Attributes:
        video: The VideoAsset that was published.
        platform: Name of the publishing platform (e.g. "instagram", "youtube").
        post_id: Platform-assigned identifier for the published post.
        post_url: Public URL of the published post.
        published_at: UTC timestamp when the post was published.
        success: Whether the publish operation completed successfully.
    """

    video: VideoAsset
    platform: str
    post_id: str
    post_url: str
    success: bool
    published_at: datetime = field(default_factory=datetime.utcnow)
