"""Abstract base class for all content scrapers."""

from abc import ABC, abstractmethod
from models.trend import TrendItem


class ScraperError(Exception):
    """Raised when a scraper fails to fetch or parse content."""


class BaseScraper(ABC):
    """Abstract scraper that defines the interface for all platform scrapers."""

    @abstractmethod
    def scrape(self, genre: str) -> list[TrendItem]:
        """Scrape trending content for the given genre.

        Args:
            genre: Content category or keyword to search for (e.g. "fitness").

        Returns:
            A list of TrendItem objects scraped from the platform.
        """
