"""PostProcessor adds captions and background music to a video using ffmpeg."""

import os
import tempfile

import ffmpeg

from utils.logger import logger

BACKGROUND_MUSIC_VOLUME_DB = -20.0
OUTPUT_SUFFIX = "_processed.mp4"
CAPTION_FONT_SIZE = 48
CAPTION_FONT_COLOR = "white"
CAPTION_BOX_COLOR = "black@0.5"
CAPTION_BOX_BORDER = 5
CAPTION_LINE_SPACING = 60
CAPTION_X_POSITION = "(w-text_w)/2"
CAPTION_Y_POSITION = "h*0.75"


class PostProcessorError(Exception):
    """Raised when ffmpeg post-processing fails."""


class PostProcessor:
    """Adds burned-in captions and background music to a video file.

    Uses ffmpeg-python to compose the final output video.
    """

    def add_captions_and_music(
        self,
        video_path: str,
        captions: list[str],
        music_path: str,
    ) -> str:
        """Burn captions into the video and mix background music at -20dB.

        Args:
            video_path: Local path to the raw input video file.
            captions: List of caption strings to overlay on the video.
            music_path: Local path to the background music audio file.

        Returns:
            Local path of the processed output video file.
        """
        output_path = self._build_output_path(video_path)
        subtitle_path = self._write_subtitle_file(captions)
        logger.info("PostProcessor: processing '{}' -> '{}'", video_path, output_path)
        try:
            self._run_ffmpeg_pipeline(video_path, subtitle_path, music_path, output_path)
            logger.info("PostProcessor: finished '{}'", output_path)
            return output_path
        except ffmpeg.Error as error:
            logger.error("PostProcessor: ffmpeg failed: {}", error.stderr)
            raise PostProcessorError(f"ffmpeg processing failed: {error}") from error
        finally:
            if os.path.exists(subtitle_path):
                os.remove(subtitle_path)

    def _run_ffmpeg_pipeline(
        self, video_path: str, subtitle_path: str, music_path: str, output_path: str
    ) -> None:
        """Execute the ffmpeg pipeline to compose the final video.

        Args:
            video_path: Input raw video file path.
            subtitle_path: Path to the generated SRT subtitle file.
            music_path: Background music file path.
            output_path: Desired output file path.
        """
        video = ffmpeg.input(video_path)
        music = ffmpeg.input(music_path)
        video_with_subs = video.video.filter("subtitles", subtitle_path)
        mixed_audio = ffmpeg.filter(
            [video.audio, music.audio.filter("volume", f"{BACKGROUND_MUSIC_VOLUME_DB}dB")],
            "amix",
            inputs=2,
            duration="first",
        )
        ffmpeg.output(video_with_subs, mixed_audio, output_path, vcodec="libx264", acodec="aac").run(
            overwrite_output=True, quiet=True
        )

    def _write_subtitle_file(self, captions: list[str]) -> str:
        """Write captions to a temporary SRT subtitle file.

        Args:
            captions: List of caption strings.

        Returns:
            Path to the temporary SRT file.
        """
        srt_content = self._build_srt_content(captions)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".srt", delete=False, encoding="utf-8") as file:
            file.write(srt_content)
            return file.name

    def _build_srt_content(self, captions: list[str]) -> str:
        """Format captions as an SRT subtitle string with even time spacing.

        Args:
            captions: List of caption text strings.

        Returns:
            Formatted SRT content string.
        """
        lines: list[str] = []
        seconds_per_caption = 12
        for index, caption in enumerate(captions):
            start = index * seconds_per_caption
            end = start + seconds_per_caption
            lines.append(
                f"{index + 1}\n"
                f"{self._format_srt_time(start)} --> {self._format_srt_time(end)}\n"
                f"{caption}\n"
            )
        return "\n".join(lines)

    def _format_srt_time(self, total_seconds: int) -> str:
        """Convert seconds to SRT timestamp format HH:MM:SS,mmm.

        Args:
            total_seconds: Integer seconds to format.

        Returns:
            SRT-formatted timestamp string.
        """
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},000"

    def _build_output_path(self, video_path: str) -> str:
        """Derive the output file path from the input video path.

        Args:
            video_path: Input video file path.

        Returns:
            Output file path with a processed suffix.
        """
        base, _ = os.path.splitext(video_path)
        return f"{base}{OUTPUT_SUFFIX}"
