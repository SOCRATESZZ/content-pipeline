"""Twitter/X scraper using Tweepy v2 to fetch recent trending tweets."""

from datetime import datetime

import tweepy

from models.trend import TrendItem
from scraper.base import BaseScraper, ScraperError
from utils.logger import logger

TWITTER_BASE_URL = "https://twitter.com"
MAX_RESULTS_PER_REQUEST = 100
ENGAGEMENT_NORMALIZATION_FACTOR = 10000
RETWEET_WEIGHT = 3
TWEET_FIELDS = ["public_metrics", "created_at", "author_id"]


class TwitterScraper(BaseScraper):
    """Scrapes recent tweets for a genre hashtag using the Twitter API v2.

    Args:
        twitter_client: An authenticated tweepy.Client instance.
    """

    def __init__(self, twitter_client: tweepy.Client) -> None:
        """Initialise with an authenticated Tweepy v2 Client."""
        self._client = twitter_client

    def scrape(self, genre: str) -> list[TrendItem]:
        """Fetch recent non-retweet tweets for the genre hashtag.

        Args:
            genre: Hashtag keyword to search (e.g. "fitness").

        Returns:
            List of TrendItem objects from matching tweets.
        """
        logger.info("TwitterScraper: scraping #{}", genre)
        query = f"#{genre} -is:retweet lang:en"
        try:
            response = self._client.search_recent_tweets(
                query=query,
                max_results=MAX_RESULTS_PER_REQUEST,
                tweet_fields=TWEET_FIELDS,
            )
            return self._convert_response_to_trends(response, genre)
        except Exception as error:
            logger.error("TwitterScraper: failed for #{}: {}", genre, error)
            raise ScraperError(f"Twitter scrape failed for genre '{genre}'") from error

    def _convert_response_to_trends(
        self, response: tweepy.Response, genre: str
    ) -> list[TrendItem]:
        """Convert a Tweepy response into a list of TrendItem objects.

        Args:
            response: The raw tweepy.Response from search_recent_tweets.
            genre: Genre keyword used in the search query.

        Returns:
            List of TrendItem objects.
        """
        items: list[TrendItem] = []
        if not response.data:
            logger.warning("TwitterScraper: no tweets found for #{}", genre)
            return items
        for tweet in response.data:
            metrics = tweet.public_metrics or {}
            engagement_score = self._compute_engagement_score(metrics)
            items.append(TrendItem(
                title=tweet.text[:200],
                source="twitter",
                engagement_score=engagement_score,
                trend_score=engagement_score * 100,
                url=f"{TWITTER_BASE_URL}/i/web/status/{tweet.id}",
                collected_at=datetime.utcnow(),
            ))
        logger.info("TwitterScraper: fetched {} tweets for #{}", len(items), genre)
        return items

    def _compute_engagement_score(self, metrics: dict) -> float:
        """Compute a normalised engagement score from tweet public metrics.

        Args:
            metrics: Dictionary of public metrics from the tweet.

        Returns:
            Normalised engagement score in range [0.0, 1.0].
        """
        likes = metrics.get("like_count", 0)
        retweets = metrics.get("retweet_count", 0)
        raw_score = (likes + retweets * RETWEET_WEIGHT) / ENGAGEMENT_NORMALIZATION_FACTOR
        return min(1.0, raw_score)
