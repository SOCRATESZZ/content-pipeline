"""TrendItem model representing a single scraped trending topic."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class TrendItem:
    """A single trending topic collected from a scraper source.

    Attributes:
        title: Headline or topic title of the trend.
        source: Name of the platform the trend was scraped from.
        engagement_score: Normalised engagement metric in range [0.0, 1.0].
        trend_score: Platform-specific trend strength in range [0.0, 100.0].
        url: Direct URL to the trending content.
        collected_at: UTC timestamp when this item was scraped.
    """

    title: str
    source: str
    engagement_score: float
    trend_score: float
    url: str
    collected_at: datetime = field(default_factory=datetime.utcnow)
