"""Weighted scoring engine that transforms a TrendItem into a RankedIdea."""

import anthropic

from models.idea import RankedIdea
from models.trend import TrendItem
from ranking.novelty_checker import NoveltyChecker
from utils.logger import logger

VIRALITY_WEIGHT = 0.35
NOVELTY_WEIGHT = 0.25
SEARCHABILITY_WEIGHT = 0.20
HOOK_STRENGTH_WEIGHT = 0.20

TREND_SCORE_NORMALIZATION = 100.0
HOOK_SCORE_DEFAULT = 0.5
HOOK_SCORE_MIN = 0.0
HOOK_SCORE_MAX = 1.0

HOOK_RATING_PROMPT = (
    "Rate this headline's hook potential from 0.0 to 1.0. "
    "Return only a float. Headline: {title}"
)


class ScorerError(Exception):
    """Raised when idea scoring fails."""


class Scorer:
    """Scores a TrendItem across four dimensions and returns a RankedIdea.

    Args:
        novelty_checker: A NoveltyChecker instance for computing novelty scores.
        anthropic_client: An authenticated anthropic.Anthropic client.
        model: Claude model identifier to use for hook scoring.
        max_tokens: Maximum tokens for the hook scoring prompt.
    """

    def __init__(
        self,
        novelty_checker: NoveltyChecker,
        anthropic_client: anthropic.Anthropic,
        model: str,
        max_tokens: int,
    ) -> None:
        """Initialise the Scorer with its required dependencies."""
        self._novelty_checker = novelty_checker
        self._client = anthropic_client
        self._model = model
        self._max_tokens = max_tokens

    def score_idea(self, trend: TrendItem) -> RankedIdea:
        """Score a trend item across four dimensions and return a RankedIdea.

        Args:
            trend: The TrendItem to evaluate.

        Returns:
            A RankedIdea with all scores and a weighted final_score (rank=0).
        """
        virality_score = trend.engagement_score
        novelty_score = self._novelty_checker.compute_novelty(trend.title)
        searchability_score = trend.trend_score / TREND_SCORE_NORMALIZATION
        hook_strength_score = self._fetch_hook_score(trend.title)

        final_score = (
            virality_score * VIRALITY_WEIGHT
            + novelty_score * NOVELTY_WEIGHT
            + searchability_score * SEARCHABILITY_WEIGHT
            + hook_strength_score * HOOK_STRENGTH_WEIGHT
        )
        return RankedIdea(
            trend_item=trend,
            final_score=round(final_score, 4),
            rank=0,
            virality_score=round(virality_score, 4),
            novelty_score=round(novelty_score, 4),
            searchability_score=round(searchability_score, 4),
            hook_strength_score=round(hook_strength_score, 4),
        )

    def _fetch_hook_score(self, title: str) -> float:
        """Call Claude to rate the hook potential of a headline.

        Args:
            title: The headline to evaluate.

        Returns:
            A float in [0.0, 1.0] representing hook strength.
        """
        prompt = HOOK_RATING_PROMPT.format(title=title)
        try:
            response = self._client.messages.create(
                model=self._model,
                max_tokens=self._max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )
            raw_text = response.content[0].text.strip()
            score = float(raw_text)
            return max(HOOK_SCORE_MIN, min(HOOK_SCORE_MAX, score))
        except Exception as error:
            logger.warning("Scorer: hook score fetch failed for '{}': {}. Using default.", title, error)
            return HOOK_SCORE_DEFAULT
