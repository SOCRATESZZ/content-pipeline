"""VideoAsset model representing a fully produced video file."""

from dataclasses import dataclass
from .script import VideoScript


@dataclass
class VideoAsset:
    """A fully produced video ready for publishing.

    Attributes:
        script: The VideoScript this asset was produced from.
        audio_url: S3 URL of the generated MP3 audio file.
        video_url: HeyGen-hosted URL of the raw avatar video.
        final_url: S3 URL of the post-processed video with captions and music.
        duration_seconds: Duration of the final video in seconds.
        local_path: Local filesystem path of the downloaded final video.
    """

    script: VideoScript
    audio_url: str
    video_url: str
    final_url: str
    duration_seconds: float
    local_path: str
