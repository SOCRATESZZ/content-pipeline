"""YouTubePublisher uploads videos as YouTube Shorts via Data API v3."""

from datetime import datetime

from googleapiclient.discovery import Resource
from googleapiclient.http import MediaFileUpload

from config import YouTubeSettings
from models.publish_result import PublishResult
from models.script import VideoScript
from models.video import VideoAsset
from publisher.base import BasePublisher, PublishError
from utils.logger import logger

YOUTUBE_VIDEO_MIMETYPE = "video/mp4"
YOUTUBE_PRIVACY_STATUS = "public"
YOUTUBE_SHORT_CATEGORY_ID = "22"
PUBLISH_PLATFORM = "youtube"
YOUTUBE_SHORTS_TAG = "#Shorts"
YOUTUBE_CHUNK_SIZE = 1024 * 1024


class YouTubePublisher(BasePublisher):
    """Publishes short-form videos to YouTube via the Data API v3.

    Args:
        youtube_service: An authenticated googleapiclient Resource for YouTube.
        settings: YouTubeSettings with credential configuration.
    """

    def __init__(self, youtube_service: Resource, settings: YouTubeSettings) -> None:
        """Initialise the YouTubePublisher with the API resource."""
        self._youtube = youtube_service
        self._settings = settings

    def publish(self, video: VideoAsset, caption: str) -> PublishResult:
        """Publish a video as a YouTube Short.

        Args:
            video: The VideoAsset to publish.
            caption: Text used as the video description.

        Returns:
            A PublishResult with the YouTube video URL and ID.
        """
        return self.publish_short(video, video.script)

    def publish_short(self, video: VideoAsset, script: VideoScript) -> PublishResult:
        """Upload a local MP4 file as a public YouTube Short.

        Args:
            video: VideoAsset with a local_path to the final MP4.
            script: VideoScript providing hook (title) and full_text (description).

        Returns:
            A PublishResult with the published video URL.
        """
        logger.info("YouTubePublisher: uploading Short '{}'", script.hook)
        try:
            video_id = self._upload_video_file(video, script)
            video_url = f"https://www.youtube.com/shorts/{video_id}"
            logger.info("YouTubePublisher: Short published as {}", video_url)
            return PublishResult(
                video=video, platform=PUBLISH_PLATFORM, post_id=video_id,
                post_url=video_url, success=True, published_at=datetime.utcnow(),
            )
        except Exception as error:
            logger.error("YouTubePublisher: upload failed: {}", error)
            raise PublishError(f"YouTube upload failed: {error}") from error

    def _upload_video_file(self, video: VideoAsset, script: VideoScript) -> str:
        """Execute the YouTube resumable upload and return the video ID.

        Args:
            video: VideoAsset with local_path to the file to upload.
            script: VideoScript providing title and description metadata.

        Returns:
            The YouTube video ID of the uploaded video.
        """
        body = self._build_video_resource(script)
        media = MediaFileUpload(video.local_path, mimetype=YOUTUBE_VIDEO_MIMETYPE, chunksize=YOUTUBE_CHUNK_SIZE, resumable=True)
        request = self._youtube.videos().insert(part="snippet,status", body=body, media_body=media)
        response = request.execute()
        return response["id"]

    def _build_video_resource(self, script: VideoScript) -> dict:
        """Build the YouTube video resource metadata dictionary.

        Args:
            script: VideoScript providing the video title and description.

        Returns:
            Dictionary formatted as a YouTube video resource body.
        """
        return {
            "snippet": {
                "title": script.hook[:100],
                "description": f"{script.full_text}\n\n{YOUTUBE_SHORTS_TAG}",
                "categoryId": YOUTUBE_SHORT_CATEGORY_ID,
                "tags": [YOUTUBE_SHORTS_TAG],
            },
            "status": {"privacyStatus": YOUTUBE_PRIVACY_STATUS},
        }
