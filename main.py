"""CLI entrypoint for the AI content generation pipeline."""

import anthropic
import click
import praw
import tweepy
from pytrends.request import TrendReq
from rich.console import Console
from rich.table import Table

from config import load_settings
from generator.prompt_builder import PromptBuilder
from generator.script_validator import ScriptValidator
from generator.script_writer import ScriptWriter
from models.publish_result import PublishResult
from models.script import VideoScript
from pipeline import ContentPipeline
from publisher.hashtag_engine import HashtagEngine
from ranking.novelty_checker import NoveltyChecker
from ranking.ranker import Ranker
from ranking.scorer import Scorer
from scraper.aggregator import Aggregator
from scraper.google_trends_scraper import GoogleTrendsScraper
from scraper.reddit_scraper import RedditScraper
from scraper.twitter_scraper import TwitterScraper
from utils.logger import configure_logger, logger

console = Console()

DEFAULT_TOP_N = 5


@click.command()
@click.option("--genre", required=True, help='Content genre to process, e.g. "fitness", "tech".')
@click.option("--top-n", default=DEFAULT_TOP_N, show_default=True, help="Number of top ideas to process.")
@click.option("--dry-run", is_flag=True, default=False, help="Run scrape + rank + script only (skip video + publish).")
def run_pipeline(genre: str, top_n: int, dry_run: bool) -> None:
    """Run the AI content generation pipeline for a given genre."""
    configure_logger()
    settings = load_settings()
    logger.info("Starting pipeline for genre='{}' top_n={} dry_run={}", genre, top_n, dry_run)

    pipeline = build_pipeline(settings, dry_run=dry_run)
    results = pipeline.run(genre=genre, top_n=top_n, dry_run=dry_run)

    if dry_run:
        console.print("\n[bold yellow]Dry-run complete. Video production and publishing were skipped.[/bold yellow]")
        return

    print_summary_table(results)


def build_pipeline(settings, dry_run: bool = False) -> ContentPipeline:
    """Construct and return a fully wired ContentPipeline from settings.

    Args:
        settings: Loaded Settings object with all service credentials.
        dry_run: If True, skip building Producer and Publishers (no API keys needed).

    Returns:
        A configured ContentPipeline ready to run.
    """
    reddit_client = praw.Reddit(
        client_id=settings.reddit.client_id or "placeholder",
        client_secret=settings.reddit.client_secret or "placeholder",
        user_agent=settings.reddit.user_agent,
    )
    twitter_client = tweepy.Client(bearer_token=settings.twitter.bearer_token or "placeholder")
    trends_client = TrendReq(hl="en-US", tz=0)
    anthropic_client = anthropic.Anthropic(api_key=settings.anthropic.api_key or "placeholder")

    aggregator = Aggregator(scrapers=[
        RedditScraper(reddit_client),
        GoogleTrendsScraper(trends_client),
        TwitterScraper(twitter_client),
    ])

    novelty_checker = NoveltyChecker()
    scorer = Scorer(
        novelty_checker=novelty_checker,
        anthropic_client=anthropic_client,
        model=settings.anthropic.model,
        max_tokens=settings.anthropic.max_tokens,
    )
    ranker = Ranker(scorer=scorer)

    prompt_builder = PromptBuilder()
    validator = ScriptValidator()
    script_writer = ScriptWriter(
        anthropic_client=anthropic_client,
        prompt_builder=prompt_builder,
        validator=validator,
        model=settings.anthropic.model,
        max_tokens=settings.anthropic.max_tokens,
    )

    producer = _build_producer(settings) if not dry_run else None
    publishers = _build_publishers(settings) if not dry_run else []

    return ContentPipeline(
        aggregator=aggregator,
        ranker=ranker,
        script_writer=script_writer,
        producer=producer,
        publishers=publishers,
        hashtag_engine=HashtagEngine(),
    )


def _build_producer(settings):
    """Build and return a configured Producer from settings.

    Args:
        settings: Loaded Settings object.

    Returns:
        A configured Producer instance.
    """
    import httpx
    from utils.storage import StorageClient
    from video.avatar_client import AvatarClient
    from video.post_processor import PostProcessor
    from video.producer import Producer
    from video.tts_client import TTSClient

    http_client = httpx.Client()
    storage_client = StorageClient(
        bucket_name=settings.aws.bucket_name,
        region=settings.aws.region,
    )
    tts_client = TTSClient(
        http_client=http_client,
        api_key=settings.elevenlabs.api_key,
        model_id=settings.elevenlabs.model_id,
    )
    avatar_client = AvatarClient(
        http_client=http_client,
        api_key=settings.heygen.api_key,
        poll_interval_seconds=settings.heygen.poll_interval_seconds,
        poll_timeout_seconds=settings.heygen.poll_timeout_seconds,
    )
    return Producer(
        tts_client=tts_client,
        avatar_client=avatar_client,
        post_processor=PostProcessor(),
        storage_client=storage_client,
        voice_id=settings.elevenlabs.voice_id,
        avatar_id=settings.heygen.avatar_id,
    )


def _build_publishers(settings) -> list:
    """Build and return a list of configured publisher instances.

    Args:
        settings: Loaded Settings object.

    Returns:
        List of BasePublisher instances.
    """
    import httpx
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build as build_google_service
    from publisher.instagram_publisher import InstagramPublisher
    from publisher.youtube_publisher import YouTubePublisher

    http_client = httpx.Client()
    instagram_publisher = InstagramPublisher(http_client=http_client, settings=settings.instagram)

    credentials = Credentials.from_authorized_user_file(settings.youtube.credentials_json_path)
    youtube_service = build_google_service("youtube", "v3", credentials=credentials)
    youtube_publisher = YouTubePublisher(youtube_service=youtube_service, settings=settings.youtube)

    return [instagram_publisher, youtube_publisher]


def print_summary_table(results: list[PublishResult]) -> None:
    """Print a Rich summary table of all publish results.

    Args:
        results: List of PublishResult objects from the pipeline.
    """
    table = Table(title="Pipeline Summary", show_lines=True)
    table.add_column("Rank", style="bold cyan", justify="center")
    table.add_column("Title", style="white")
    table.add_column("Score", justify="center")
    table.add_column("Script Words", justify="center")
    table.add_column("Published To", style="green")
    table.add_column("Post URL", style="blue")

    for result in results:
        script: VideoScript = result.video.script
        idea = script.idea
        table.add_row(
            str(idea.rank),
            idea.trend_item.title[:60],
            f"{idea.final_score:.3f}",
            str(script.word_count),
            result.platform,
            result.post_url,
        )

    console.print(table)


if __name__ == "__main__":
    run_pipeline()
