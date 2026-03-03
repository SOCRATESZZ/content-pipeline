"""NoveltyChecker detects near-duplicate topics against a published history."""

import difflib
import json
import os

from utils.logger import logger

NOVELTY_FULL_SCORE = 1.0
NOVELTY_ZERO_SCORE = 0.0
DUPLICATE_SIMILARITY_THRESHOLD = 0.8
DEFAULT_HISTORY_PATH = "data/published_titles.json"


class NoveltyChecker:
    """Computes novelty scores by comparing titles against a local history file.

    Args:
        history_path: Path to the JSON file storing previously published titles.
    """

    def __init__(self, history_path: str = DEFAULT_HISTORY_PATH) -> None:
        """Initialise and load published title history from disk."""
        self._history_path = history_path
        self._published_titles: list[str] = self._load_history()

    def compute_novelty(self, title: str) -> float:
        """Return a novelty score for a title compared to published history.

        Args:
            title: The content title to evaluate.

        Returns:
            1.0 if the title is completely new; 0.0 if it is a near-duplicate.
        """
        for published_title in self._published_titles:
            ratio = difflib.SequenceMatcher(
                None, title.lower(), published_title.lower()
            ).ratio()
            if ratio > DUPLICATE_SIMILARITY_THRESHOLD:
                logger.debug("NoveltyChecker: '{}' is a near-duplicate (ratio={:.2f})", title, ratio)
                return NOVELTY_ZERO_SCORE
        return NOVELTY_FULL_SCORE

    def record_published_title(self, title: str) -> None:
        """Append a title to the history and persist it to disk.

        Args:
            title: The content title to record as published.
        """
        self._published_titles.append(title)
        self._save_history()

    def _load_history(self) -> list[str]:
        """Load the list of published titles from the JSON history file."""
        if not os.path.exists(self._history_path):
            return []
        try:
            with open(self._history_path, "r", encoding="utf-8") as file:
                return json.load(file)
        except (json.JSONDecodeError, OSError) as error:
            logger.warning("NoveltyChecker: could not load history from {}: {}", self._history_path, error)
            return []

    def _save_history(self) -> None:
        """Persist the in-memory title history back to the JSON file."""
        os.makedirs(os.path.dirname(self._history_path), exist_ok=True)
        with open(self._history_path, "w", encoding="utf-8") as file:
            json.dump(self._published_titles, file, indent=2)
