"""Google Trends scraper using pytrends to fetch rising related queries."""

from datetime import datetime

from pytrends.request import TrendReq

from models.trend import TrendItem
from scraper.base import BaseScraper, ScraperError
from utils.logger import logger

GOOGLE_TRENDS_BASE_URL = "https://trends.google.com/trends/explore"
INTEREST_SCALE_MAX = 100.0
TIMEFRAME = "now 7-d"
GEO = ""
RISING_QUERIES_KEY = "rising"


class GoogleTrendsScraper(BaseScraper):
    """Scrapes rising related queries from Google Trends for a given genre.

    Args:
        trends_client: A configured pytrends TrendReq instance.
    """

    def __init__(self, trends_client: TrendReq) -> None:
        """Initialise with a pytrends TrendReq client."""
        self._trends = trends_client

    def scrape(self, genre: str) -> list[TrendItem]:
        """Fetch rising related queries from Google Trends for the genre.

        Args:
            genre: Keyword to search for rising queries (e.g. "fitness").

        Returns:
            List of TrendItem objects from rising related queries.
        """
        logger.info("GoogleTrendsScraper: scraping trends for '{}'", genre)
        try:
            self._trends.build_payload([genre], timeframe=TIMEFRAME, geo=GEO)
            related = self._trends.related_queries()
            return self._extract_trend_items(related, genre)
        except Exception as error:
            logger.error("GoogleTrendsScraper: failed for genre '{}': {}", genre, error)
            raise ScraperError(f"Google Trends scrape failed for genre '{genre}'") from error

    def _extract_trend_items(self, related: dict, genre: str) -> list[TrendItem]:
        """Extract TrendItem objects from pytrends related queries response.

        Args:
            related: The dictionary returned by pytrends.related_queries().
            genre: The genre keyword used in the query.

        Returns:
            List of TrendItem objects from rising queries.
        """
        items: list[TrendItem] = []
        genre_data = related.get(genre, {})
        rising_df = genre_data.get(RISING_QUERIES_KEY)
        if rising_df is None or rising_df.empty:
            logger.warning("GoogleTrendsScraper: no rising queries for '{}'", genre)
            return items
        for _, row in rising_df.iterrows():
            trend_score = float(min(row.get("value", 0), INTEREST_SCALE_MAX))
            items.append(TrendItem(
                title=str(row["query"]),
                source="google_trends",
                engagement_score=trend_score / INTEREST_SCALE_MAX,
                trend_score=trend_score,
                url=f"{GOOGLE_TRENDS_BASE_URL}?q={row['query']}",
                collected_at=datetime.utcnow(),
            ))
        logger.info("GoogleTrendsScraper: fetched {} rising queries for '{}'", len(items), genre)
        return items
