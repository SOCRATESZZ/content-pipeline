"""Application configuration loaded from environment variables via pydantic-settings."""

from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class RedditSettings(BaseSettings):
    """Reddit API credentials."""

    client_id: str = ""
    client_secret: str = ""
    user_agent: str = "ContentPipeline/1.0"

    model_config = SettingsConfigDict(env_prefix="REDDIT__", extra="ignore")


class TwitterSettings(BaseSettings):
    """Twitter/X API v2 credentials."""

    bearer_token: str = ""

    model_config = SettingsConfigDict(env_prefix="TWITTER__", extra="ignore")


class AnthropicSettings(BaseSettings):
    """Anthropic Claude API settings."""

    api_key: str = ""
    model: str = "claude-sonnet-4-20250514"
    max_tokens: int = 1000

    model_config = SettingsConfigDict(env_prefix="ANTHROPIC__", extra="ignore")


class ElevenLabsSettings(BaseSettings):
    """ElevenLabs text-to-speech settings."""

    api_key: str = ""
    voice_id: str = ""
    model_id: str = "eleven_turbo_v2"

    model_config = SettingsConfigDict(env_prefix="ELEVENLABS__", extra="ignore")


class HeyGenSettings(BaseSettings):
    """HeyGen avatar video generation settings."""

    api_key: str = ""
    avatar_id: str = ""
    poll_interval_seconds: int = 10
    poll_timeout_seconds: int = 300

    model_config = SettingsConfigDict(env_prefix="HEYGEN__", extra="ignore")


class InstagramSettings(BaseSettings):
    """Instagram Graph API credentials."""

    access_token: str = ""
    user_id: str = ""

    model_config = SettingsConfigDict(env_prefix="INSTAGRAM__", extra="ignore")


class YouTubeSettings(BaseSettings):
    """YouTube Data API v3 settings."""

    credentials_json_path: str = ""

    model_config = SettingsConfigDict(env_prefix="YOUTUBE__", extra="ignore")


class AWSSettings(BaseSettings):
    """AWS S3 storage settings."""

    bucket_name: str = ""
    region: str = "us-east-1"

    model_config = SettingsConfigDict(env_prefix="AWS__", extra="ignore")


class AyrshareSettings(BaseSettings):
    """Ayrshare scheduled publishing settings."""

    api_key: str = ""

    model_config = SettingsConfigDict(env_prefix="AYRSHARE__", extra="ignore")


class Settings(BaseSettings):
    """Top-level application settings composed from all service sub-settings."""

    reddit: RedditSettings = Field(default_factory=RedditSettings)
    twitter: TwitterSettings = Field(default_factory=TwitterSettings)
    anthropic: AnthropicSettings = Field(default_factory=AnthropicSettings)
    elevenlabs: ElevenLabsSettings = Field(default_factory=ElevenLabsSettings)
    heygen: HeyGenSettings = Field(default_factory=HeyGenSettings)
    instagram: InstagramSettings = Field(default_factory=InstagramSettings)
    youtube: YouTubeSettings = Field(default_factory=YouTubeSettings)
    aws: AWSSettings = Field(default_factory=AWSSettings)
    ayrshare: AyrshareSettings = Field(default_factory=AyrshareSettings)

    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


def load_settings() -> Settings:
    """Load and return the application settings from environment variables."""
    return Settings()
