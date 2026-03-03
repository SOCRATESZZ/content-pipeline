"""ScriptValidator checks that a VideoScript meets word-count requirements."""

from models.script import VideoScript

MINIMUM_WORDS = 120
MAXIMUM_WORDS = 145


class ScriptValidationError(Exception):
    """Raised when a script fails word-count validation."""


class ScriptValidator:
    """Validates that a VideoScript falls within the required word count range."""

    def validate(self, script: VideoScript) -> bool:
        """Return True if the script word count is within the allowed range.

        Args:
            script: The VideoScript to validate.

        Returns:
            True if word_count is between MINIMUM_WORDS and MAXIMUM_WORDS inclusive.
        """
        return MINIMUM_WORDS <= script.word_count <= MAXIMUM_WORDS

    def count_words(self, text: str) -> int:
        """Count the number of whitespace-delimited words in a text string.

        Args:
            text: The text to count words in.

        Returns:
            Integer word count.
        """
        return len(text.split())
