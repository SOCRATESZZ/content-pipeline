"""PromptBuilder constructs genre-aware system prompts for Claude script generation."""

from models.script import HookVariant

HOOK_INSTRUCTIONS: dict[str, str] = {
    "question": "Open with a thought-provoking question that hooks the viewer instantly.",
    "statement": "Open with a bold, surprising declarative statement.",
    "stat": "Open with a striking statistic or data point.",
}

SCRIPT_JSON_SCHEMA = """{
  "hook": "<opening hook line>",
  "body": ["<insight 1>", "<insight 2>", "<insight 3>"],
  "cta": "<call-to-action line>",
  "captions": ["<3-6 word caption>", "<3-6 word caption>", "<3-6 word caption>", "<3-6 word caption>", "<3-6 word caption>"]
}"""


class PromptBuilder:
    """Builds genre-tuned system prompts for video script generation."""

    def build_system_prompt(self, genre: str, hook_variant: HookVariant) -> str:
        """Return a genre-tuned system prompt for Claude script generation.

        Args:
            genre: Content category (e.g. "fitness", "tech", "personalfinance").
            hook_variant: The style of hook to use — question, statement, or stat.

        Returns:
            A fully formatted system prompt string.
        """
        hook_instruction = HOOK_INSTRUCTIONS.get(hook_variant, HOOK_INSTRUCTIONS["question"])
        return (
            f"You are an expert short-form video scriptwriter specialising in {genre} content.\n\n"
            f"Write a tight 60-second vertical video script structured as follows:\n\n"
            f"[HOOK] 0-3s: {hook_instruction}\n"
            f"[BODY] 4-45s: Deliver exactly 3 concise insights relevant to {genre}. "
            f"Each insight must take under 10 seconds when spoken aloud at a natural pace.\n"
            f"[CTA] 46-60s: End with a share prompt and follow trigger relevant to {genre} audiences.\n\n"
            f"Also include exactly 5 on-screen caption lines. "
            f"Each caption must be 3–6 words, punchy, and capture the visual moment.\n\n"
            f"IMPORTANT: Respond ONLY with valid JSON. No explanation, no markdown, no code fences.\n"
            f"Use this exact schema:\n{SCRIPT_JSON_SCHEMA}"
        )
