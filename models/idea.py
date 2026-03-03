"""RankedIdea model representing a scored and ranked content idea."""

from dataclasses import dataclass
from .trend import TrendItem


@dataclass
class RankedIdea:
    """A trend idea that has been scored and ranked for content production.

    Attributes:
        trend_item: The original scraped TrendItem this idea is based on.
        final_score: Weighted aggregate score across all dimensions.
        rank: Position in the ranked list (1 = highest score).
        virality_score: Score reflecting engagement and shareability [0.0, 1.0].
        novelty_score: Score reflecting uniqueness vs. recent history [0.0, 1.0].
        searchability_score: Score reflecting SEO and discoverability [0.0, 1.0].
        hook_strength_score: Claude-rated hook potential [0.0, 1.0].
    """

    trend_item: TrendItem
    final_score: float
    rank: int
    virality_score: float
    novelty_score: float
    searchability_score: float
    hook_strength_score: float
