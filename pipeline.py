"""ContentPipeline orchestrates all 5 stages from scraping to publishing."""

from typing import Optional

from generator.script_writer import ScriptWriter
from models.idea import RankedIdea
from models.publish_result import PublishResult
from models.script import VideoScript
from models.trend import TrendItem
from models.video import VideoAsset
from publisher.base import BasePublisher
from publisher.hashtag_engine import HashtagEngine
from ranking.ranker import Ranker
from scraper.aggregator import Aggregator
from utils.logger import logger
from video.producer import Producer

HASHTAG_SEPARATOR = "\n\n"


class ContentPipeline:
    """Orchestrates all 5 pipeline stages from trend scraping to publishing.

    Args:
        aggregator: Aggregator instance for Stage 1 scraping.
        ranker: Ranker instance for Stage 2 scoring and ranking.
        script_writer: ScriptWriter instance for Stage 3 script generation.
        producer: Producer instance for Stage 4 video production.
        publishers: List of BasePublisher instances for Stage 5 publishing.
        hashtag_engine: HashtagEngine for generating post captions.
    """

    def __init__(
        self,
        aggregator: Aggregator,
        ranker: Ranker,
        script_writer: ScriptWriter,
        producer: Producer,
        publishers: list[BasePublisher],
        hashtag_engine: HashtagEngine,
    ) -> None:
        """Initialise the ContentPipeline with all stage dependencies."""
        self._aggregator = aggregator
        self._ranker = ranker
        self._script_writer = script_writer
        self._producer = producer
        self._publishers = publishers
        self._hashtag_engine = hashtag_engine

    def run(self, genre: str, top_n: int, dry_run: bool = False) -> list[PublishResult]:
        """Execute all pipeline stages for a given genre.

        Args:
            genre: Content category to process (e.g. "fitness").
            top_n: Number of top-ranked ideas to process.
            dry_run: If True, skip video production and publishing.

        Returns:
            List of PublishResult objects from the publish stage.
        """
        trends = self._stage_scrape(genre)
        top_ideas = self._stage_rank(trends, top_n)
        scripts = self._stage_generate_scripts(top_ideas, genre)
        if dry_run:
            logger.info("Pipeline: dry-run mode — skipping video production and publishing")
            return []
        videos = self._stage_produce_videos(scripts)
        results = self._stage_publish(videos, genre)
        return results

    def _stage_scrape(self, genre: str) -> list[TrendItem]:
        """Stage 1: Scrape trending content from all configured sources.

        Args:
            genre: Content category to pass to each scraper.

        Returns:
            Flat list of deduplicated TrendItem objects.
        """
        logger.info("Pipeline Stage 1: scraping trends for genre '{}'", genre)
        trends = self._aggregator.collect_all_trends(genre)
        logger.info("Pipeline Stage 1: complete — {} trends collected", len(trends))
        return trends

    def _stage_rank(self, trends: list[TrendItem], top_n: int) -> list[RankedIdea]:
        """Stage 2: Score and rank all trends, returning the top N ideas.

        Args:
            trends: Full list of scraped TrendItem objects.
            top_n: Number of top ideas to return.

        Returns:
            List of top N RankedIdea objects sorted by final_score.
        """
        logger.info("Pipeline Stage 2: ranking {} trends, selecting top {}", len(trends), top_n)
        ideas = self._ranker.rank_ideas(trends, top_n)
        logger.info("Pipeline Stage 2: complete — {} ideas ranked", len(ideas))
        return ideas

    def _stage_generate_scripts(self, ideas: list[RankedIdea], genre: str) -> list[VideoScript]:
        """Stage 3: Generate a 60-second video script for each ranked idea.

        Args:
            ideas: List of top-ranked RankedIdea objects.
            genre: Content genre for prompt tuning.

        Returns:
            List of generated VideoScript objects (skips failed ideas).
        """
        logger.info("Pipeline Stage 3: generating scripts for {} ideas", len(ideas))
        scripts: list[VideoScript] = []
        for idea in ideas:
            try:
                script = self._script_writer.write_script(idea, genre)
                scripts.append(script)
                logger.debug("Pipeline Stage 3: script generated for '{}'", idea.trend_item.title)
            except Exception as error:
                logger.warning("Pipeline Stage 3: failed for '{}': {}", idea.trend_item.title, error)
        logger.info("Pipeline Stage 3: complete — {} scripts generated", len(scripts))
        return scripts

    def _stage_produce_videos(self, scripts: list[VideoScript]) -> list[VideoAsset]:
        """Stage 4: Produce avatar videos for each generated script.

        Args:
            scripts: List of validated VideoScript objects.

        Returns:
            List of VideoAsset objects (skips failed scripts).
        """
        logger.info("Pipeline Stage 4: producing {} videos", len(scripts))
        videos: list[VideoAsset] = []
        for script in scripts:
            try:
                video = self._producer.produce(script)
                videos.append(video)
                logger.debug("Pipeline Stage 4: video produced for '{}'", script.idea.trend_item.title)
            except Exception as error:
                logger.warning("Pipeline Stage 4: failed for '{}': {}", script.idea.trend_item.title, error)
        logger.info("Pipeline Stage 4: complete — {} videos produced", len(videos))
        return videos

    def _stage_publish(self, videos: list[VideoAsset], genre: str) -> list[PublishResult]:
        """Stage 5: Publish all produced videos to all configured platforms.

        Args:
            videos: List of VideoAsset objects ready for publishing.
            genre: Content genre used to generate hashtags.

        Returns:
            Flat list of PublishResult objects across all videos and platforms.
        """
        logger.info("Pipeline Stage 5: publishing {} videos to {} platforms", len(videos), len(self._publishers))
        results: list[PublishResult] = []
        hashtags = self._hashtag_engine.generate(genre)
        for video in videos:
            caption = self._build_caption(video, hashtags)
            for publisher in self._publishers:
                try:
                    result = publisher.publish(video, caption)
                    results.append(result)
                    logger.debug("Pipeline Stage 5: published '{}' to {}", video.script.idea.trend_item.title, result.platform)
                except Exception as error:
                    logger.warning("Pipeline Stage 5: publish failed for {} on {}: {}", video.script.idea.trend_item.title, type(publisher).__name__, error)
        logger.info("Pipeline Stage 5: complete — {} posts published", len(results))
        return results

    def _build_caption(self, video: VideoAsset, hashtags: list[str]) -> str:
        """Build a social media caption from the script hook and hashtags.

        Args:
            video: VideoAsset whose script provides the caption hook.
            hashtags: List of hashtag strings to append.

        Returns:
            Formatted caption string.
        """
        return f"{video.script.hook}{HASHTAG_SEPARATOR}{' '.join(hashtags)}"
