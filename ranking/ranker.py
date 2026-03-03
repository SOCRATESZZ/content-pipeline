"""Ranker that scores all trends and returns the top N ranked ideas."""

from models.idea import RankedIdea
from models.trend import TrendItem
from ranking.scorer import Scorer
from utils.logger import logger

DEFAULT_TOP_N = 5
RANK_STARTING_INDEX = 1


class Ranker:
    """Scores all trend items and returns the top N ideas sorted by final score.

    Args:
        scorer: A Scorer instance used to evaluate each trend.
    """

    def __init__(self, scorer: Scorer) -> None:
        """Initialise the Ranker with a Scorer dependency."""
        self._scorer = scorer

    def rank_ideas(self, trends: list[TrendItem], top_n: int = DEFAULT_TOP_N) -> list[RankedIdea]:
        """Score all trends, sort descending, assign ranks, and return top N.

        Args:
            trends: List of scraped TrendItem objects to rank.
            top_n: Maximum number of top-ranked ideas to return.

        Returns:
            List of up to top_n RankedIdea objects sorted by final_score descending.
        """
        logger.info("Ranker: scoring {} trends, returning top {}", len(trends), top_n)
        scored = [self._score_safely(trend) for trend in trends]
        valid = [idea for idea in scored if idea is not None]
        sorted_ideas = sorted(valid, key=lambda idea: idea.final_score, reverse=True)
        top_ideas = sorted_ideas[:top_n]
        return self._assign_ranks(top_ideas)

    def _score_safely(self, trend: TrendItem) -> RankedIdea | None:
        """Attempt to score a trend, returning None on failure.

        Args:
            trend: TrendItem to score.

        Returns:
            A RankedIdea if scoring succeeded, otherwise None.
        """
        try:
            return self._scorer.score_idea(trend)
        except Exception as error:
            logger.warning("Ranker: failed to score '{}': {}", trend.title, error)
            return None

    def _assign_ranks(self, ideas: list[RankedIdea]) -> list[RankedIdea]:
        """Assign sequential rank values starting at 1 to a sorted list.

        Args:
            ideas: Sorted list of RankedIdea objects.

        Returns:
            The same list with rank fields set to 1, 2, 3, ...
        """
        for position, idea in enumerate(ideas, start=RANK_STARTING_INDEX):
            idea.rank = position
        return ideas
