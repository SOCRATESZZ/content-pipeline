"""TTSClient wraps the ElevenLabs text-to-speech REST API."""

import httpx

from utils.logger import logger

ELEVENLABS_TTS_ENDPOINT = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
TTS_OUTPUT_FORMAT = "mp3_44100_128"


class TTSError(Exception):
    """Raised when text-to-speech generation fails."""


class TTSClient:
    """Generates audio from text using ElevenLabs text-to-speech API.

    Args:
        http_client: A configured httpx.Client for making API calls.
        api_key: ElevenLabs API key for authentication.
        model_id: ElevenLabs model identifier to use for synthesis.
    """

    def __init__(self, http_client: httpx.Client, api_key: str, model_id: str) -> None:
        """Initialise the TTSClient with an HTTP client and credentials."""
        self._http_client = http_client
        self._api_key = api_key
        self._model_id = model_id

    def generate_audio(self, text: str, voice_id: str) -> bytes:
        """Generate speech audio from text and return raw MP3 bytes.

        Args:
            text: The text to synthesise into speech.
            voice_id: ElevenLabs voice identifier to use.

        Returns:
            Raw MP3 audio bytes.
        """
        url = ELEVENLABS_TTS_ENDPOINT.format(voice_id=voice_id)
        payload = {
            "text": text,
            "model_id": self._model_id,
            "output_format": TTS_OUTPUT_FORMAT,
        }
        headers = {
            "xi-api-key": self._api_key,
            "Content-Type": "application/json",
        }
        logger.info("TTSClient: generating audio for {} chars of text", len(text))
        try:
            response = self._http_client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            logger.info("TTSClient: received {} bytes of audio", len(response.content))
            return response.content
        except httpx.HTTPStatusError as error:
            logger.error("TTSClient: API error {}: {}", error.response.status_code, error.response.text)
            raise TTSError(f"TTS generation failed: HTTP {error.response.status_code}") from error
        except httpx.RequestError as error:
            logger.error("TTSClient: request failed: {}", error)
            raise TTSError(f"TTS request failed: {error}") from error
