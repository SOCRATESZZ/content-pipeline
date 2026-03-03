"""Producer orchestrates TTS → S3 → HeyGen → post-process → S3."""

import os
import tempfile
import uuid

import httpx

from models.script import VideoScript
from models.video import VideoAsset
from utils.logger import logger
from utils.storage import StorageClient
from video.avatar_client import AvatarClient
from video.post_processor import PostProcessor
from video.tts_client import TTSClient

AUDIO_S3_PREFIX = "audio"
VIDEO_S3_PREFIX = "videos/final"
AUDIO_CONTENT_TYPE = "audio/mpeg"
VIDEO_CONTENT_TYPE = "video/mp4"
LOCAL_DOWNLOAD_DIR = "tmp/videos"
BACKGROUND_MUSIC_PATH = "assets/background_music.mp3"


class VideoProductionError(Exception):
    """Raised when any stage of video production fails."""


class Producer:
    """Orchestrates the full video production pipeline for a script.

    Args:
        tts_client: TTSClient for generating audio from script text.
        avatar_client: AvatarClient for creating the avatar video.
        post_processor: PostProcessor for adding captions and music.
        storage_client: StorageClient for S3 uploads and downloads.
        voice_id: ElevenLabs voice identifier to use for audio.
        avatar_id: HeyGen avatar identifier to use for video.
    """

    def __init__(
        self,
        tts_client: TTSClient,
        avatar_client: AvatarClient,
        post_processor: PostProcessor,
        storage_client: StorageClient,
        voice_id: str,
        avatar_id: str,
    ) -> None:
        """Initialise the Producer with all production dependencies."""
        self._tts = tts_client
        self._avatar = avatar_client
        self._post_processor = post_processor
        self._storage = storage_client
        self._voice_id = voice_id
        self._avatar_id = avatar_id

    def produce(self, script: VideoScript) -> VideoAsset:
        """Execute the full production pipeline for a video script.

        Args:
            script: The validated VideoScript to produce into a VideoAsset.

        Returns:
            A VideoAsset with all URLs populated.
        """
        run_id = str(uuid.uuid4())[:8]
        logger.info("Producer: starting production run {} for '{}'", run_id, script.idea.trend_item.title)
        try:
            audio_url = self._generate_and_upload_audio(script, run_id)
            video_url, local_path = self._create_and_download_avatar_video(audio_url, run_id)
            final_path = self._post_process_video(local_path, script)
            final_url = self._upload_final_video(final_path, run_id)
            logger.info("Producer: run {} complete, final_url={}", run_id, final_url)
            return VideoAsset(
                script=script, audio_url=audio_url, video_url=video_url,
                final_url=final_url, duration_seconds=60.0, local_path=final_path,
            )
        except Exception as error:
            logger.error("Producer: run {} failed: {}", run_id, error)
            raise VideoProductionError(f"Production failed: {error}") from error

    def _generate_and_upload_audio(self, script: VideoScript, run_id: str) -> str:
        """Generate TTS audio and upload it to S3.

        Args:
            script: VideoScript whose full_text will be synthesised.
            run_id: Unique run identifier for naming the S3 object.

        Returns:
            S3 URL of the uploaded audio file.
        """
        audio_bytes = self._tts.generate_audio(script.full_text, self._voice_id)
        s3_key = f"{AUDIO_S3_PREFIX}/{run_id}.mp3"
        return self._storage.upload_bytes(audio_bytes, s3_key, AUDIO_CONTENT_TYPE)

    def _create_and_download_avatar_video(self, audio_url: str, run_id: str) -> tuple[str, str]:
        """Submit a HeyGen job, poll until done, and download the video.

        Args:
            audio_url: S3 URL of the pre-generated audio.
            run_id: Unique run identifier for naming the local file.

        Returns:
            Tuple of (heygen_video_url, local_file_path).
        """
        job_id = self._avatar.create_video(audio_url, self._avatar_id)
        video_url = self._avatar.poll_video_status(job_id)
        local_path = self._download_video_file(video_url, run_id)
        return video_url, local_path

    def _download_video_file(self, video_url: str, run_id: str) -> str:
        """Download a video from a URL to a local temporary file.

        Args:
            video_url: Remote URL of the video to download.
            run_id: Unique run identifier for naming the local file.

        Returns:
            Local file path of the downloaded video.
        """
        os.makedirs(LOCAL_DOWNLOAD_DIR, exist_ok=True)
        local_path = os.path.join(LOCAL_DOWNLOAD_DIR, f"{run_id}_raw.mp4")
        with httpx.Client() as client:
            response = client.get(video_url)
            response.raise_for_status()
        with open(local_path, "wb") as file:
            file.write(response.content)
        logger.debug("Producer: downloaded raw video to {}", local_path)
        return local_path

    def _post_process_video(self, local_path: str, script: VideoScript) -> str:
        """Apply captions and background music to the raw video.

        Args:
            local_path: Path to the raw downloaded video.
            script: VideoScript providing caption text.

        Returns:
            Path to the final processed video file.
        """
        return self._post_processor.add_captions_and_music(
            local_path, script.captions, BACKGROUND_MUSIC_PATH
        )

    def _upload_final_video(self, final_path: str, run_id: str) -> str:
        """Upload the post-processed video to S3 and return its URL.

        Args:
            final_path: Local path of the processed video.
            run_id: Unique run identifier for naming the S3 object.

        Returns:
            S3 URL of the uploaded final video.
        """
        with open(final_path, "rb") as file:
            video_bytes = file.read()
        s3_key = f"{VIDEO_S3_PREFIX}/{run_id}_final.mp4"
        return self._storage.upload_bytes(video_bytes, s3_key, VIDEO_CONTENT_TYPE)
