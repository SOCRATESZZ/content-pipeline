"""Aggregator that merges and deduplicates results from multiple scrapers."""

import difflib

from models.trend import TrendItem
from scraper.base import BaseScraper
from utils.logger import logger

DEDUPLICATION_SIMILARITY_THRESHOLD = 0.8


class Aggregator:
    """Merges TrendItem results from multiple scrapers and deduplicates by title.

    Args:
        scrapers: List of BaseScraper instances to collect results from.
    """

    def __init__(self, scrapers: list[BaseScraper]) -> None:
        """Initialise with a list of scraper instances."""
        self._scrapers = scrapers

    def collect_all_trends(self, genre: str) -> list[TrendItem]:
        """Run all scrapers and return a merged, deduplicated list of trends.

        Args:
            genre: Content category to pass to each scraper.

        Returns:
            Flat list of deduplicated TrendItem objects from all sources.
        """
        all_items: list[TrendItem] = []
        for scraper in self._scrapers:
            try:
                items = scraper.scrape(genre)
                all_items.extend(items)
                logger.debug("Aggregator: {} returned {} items", type(scraper).__name__, len(items))
            except Exception as error:
                logger.warning("Aggregator: {} failed, skipping: {}", type(scraper).__name__, error)
        deduplicated = self._deduplicate_by_title(all_items)
        logger.info("Aggregator: {} raw items -> {} after deduplication", len(all_items), len(deduplicated))
        return deduplicated

    def _deduplicate_by_title(self, items: list[TrendItem]) -> list[TrendItem]:
        """Remove near-duplicate items based on title similarity.

        Args:
            items: Raw merged list of TrendItem objects.

        Returns:
            List with near-duplicate titles removed.
        """
        unique: list[TrendItem] = []
        for candidate in items:
            if not self._is_duplicate(candidate.title, unique):
                unique.append(candidate)
        return unique

    def _is_duplicate(self, title: str, existing: list[TrendItem]) -> bool:
        """Check whether a title is too similar to any existing item's title.

        Args:
            title: Title string to test.
            existing: Already-accepted TrendItem objects to compare against.

        Returns:
            True if the title is a near-duplicate of any existing title.
        """
        for item in existing:
            ratio = difflib.SequenceMatcher(None, title.lower(), item.title.lower()).ratio()
            if ratio > DEDUPLICATION_SIMILARITY_THRESHOLD:
                return True
        return False
