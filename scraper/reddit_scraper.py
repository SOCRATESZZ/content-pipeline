"""Reddit scraper using PRAW to fetch hot posts from genre subreddits."""

from datetime import datetime

import praw

from models.trend import TrendItem
from scraper.base import BaseScraper, ScraperError
from utils.logger import logger

HOT_POSTS_LIMIT = 50
REDDIT_BASE_URL = "https://www.reddit.com"
ENGAGEMENT_NORMALIZATION_FACTOR = 1000
COMMENT_WEIGHT = 2
SCORE_MIN = 0.0
SCORE_MAX = 1.0


class RedditScraper(BaseScraper):
    """Scrapes hot posts from a genre subreddit using the PRAW library.

    Args:
        reddit_client: An authenticated praw.Reddit instance.
    """

    def __init__(self, reddit_client: praw.Reddit) -> None:
        """Initialise with an authenticated PRAW Reddit client."""
        self._reddit = reddit_client

    def scrape(self, genre: str) -> list[TrendItem]:
        """Scrape top hot posts from the subreddit matching the genre.

        Args:
            genre: Subreddit name to scrape (e.g. "fitness").

        Returns:
            List of TrendItem objects from the subreddit's hot feed.
        """
        logger.info("RedditScraper: scraping r/{}", genre)
        try:
            subreddit = self._reddit.subreddit(genre)
            posts = list(subreddit.hot(limit=HOT_POSTS_LIMIT))
            items = [self._convert_post_to_trend(post) for post in posts]
            logger.info("RedditScraper: fetched {} posts from r/{}", len(items), genre)
            return items
        except Exception as error:
            logger.error("RedditScraper: failed to scrape r/{}: {}", genre, error)
            raise ScraperError(f"Reddit scrape failed for genre '{genre}'") from error

    def _convert_post_to_trend(self, post: praw.models.Submission) -> TrendItem:
        """Convert a PRAW submission into a TrendItem.

        Args:
            post: A PRAW Submission object.

        Returns:
            A TrendItem populated from the submission's fields.
        """
        raw_score = (post.score + post.num_comments * COMMENT_WEIGHT) / ENGAGEMENT_NORMALIZATION_FACTOR
        engagement_score = max(SCORE_MIN, min(SCORE_MAX, raw_score))
        return TrendItem(
            title=post.title,
            source="reddit",
            engagement_score=engagement_score,
            trend_score=float(post.upvote_ratio * 100),
            url=f"{REDDIT_BASE_URL}{post.permalink}",
            collected_at=datetime.utcnow(),
        )
