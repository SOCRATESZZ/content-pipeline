"""VideoScript model representing a generated 60-second video script."""

from dataclasses import dataclass, field
from typing import Literal
from .idea import RankedIdea

HookVariant = Literal["question", "statement", "stat"]


@dataclass
class VideoScript:
    """A fully generated and validated 60-second video script.

    Attributes:
        idea: The RankedIdea this script was generated from.
        hook: Opening hook line (0-3 seconds).
        body: List of body insight lines (4-45 seconds, 3 items).
        cta: Call-to-action closing line (46-60 seconds).
        captions: List of 5 on-screen caption lines (3-6 words each).
        full_text: Concatenated full script text for word counting.
        word_count: Total word count of the full script.
        hook_variant: Style of hook used — question, statement, or stat.
    """

    idea: RankedIdea
    hook: str
    body: list[str]
    cta: str
    captions: list[str]
    full_text: str
    word_count: int
    hook_variant: HookVariant = "question"
