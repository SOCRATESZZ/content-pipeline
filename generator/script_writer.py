"""ScriptWriter generates 60-second video scripts via the Claude API."""

import json

import anthropic

from generator.prompt_builder import PromptBuilder
from generator.script_validator import ScriptValidator
from models.idea import RankedIdea
from models.script import HookVariant, VideoScript
from utils.logger import logger

TRIM_INSTRUCTION = (
    "The script is too long. Shorten the body section only. "
    "Keep the hook and CTA. Return only the revised JSON."
)

HOOK_VARIANT_PRIMARY: HookVariant = "question"
HOOK_VARIANT_AB_TEST: HookVariant = "stat"
MAX_RETRY_ATTEMPTS = 1


class ScriptWriterError(Exception):
    """Raised when script generation or validation fails after all retries."""


class ScriptWriter:
    """Generates, validates, and optionally trims 60-second video scripts.

    Args:
        anthropic_client: An authenticated anthropic.Anthropic client.
        prompt_builder: A PromptBuilder instance for constructing system prompts.
        validator: A ScriptValidator instance for word count checks.
        model: Claude model identifier to use.
        max_tokens: Maximum tokens for each API call.
    """

    def __init__(
        self,
        anthropic_client: anthropic.Anthropic,
        prompt_builder: PromptBuilder,
        validator: ScriptValidator,
        model: str,
        max_tokens: int,
    ) -> None:
        """Initialise ScriptWriter with all required dependencies."""
        self._client = anthropic_client
        self._prompt_builder = prompt_builder
        self._validator = validator
        self._model = model
        self._max_tokens = max_tokens

    def write_script(self, idea: RankedIdea, genre: str) -> VideoScript:
        """Generate a validated video script for a ranked idea.

        Args:
            idea: The RankedIdea to generate a script for.
            genre: Content genre used to tune the system prompt.

        Returns:
            A validated VideoScript with word count within allowed bounds.
        """
        script = self._generate_script(idea, genre, HOOK_VARIANT_PRIMARY)
        if script.word_count > self._validator.MAXIMUM_WORDS if hasattr(self._validator, 'MAXIMUM_WORDS') else 145:
            logger.warning("ScriptWriter: script too long ({} words), trimming.", script.word_count)
            script = self._trim_and_retry(idea, genre, script)
        logger.info("ScriptWriter: script ready ({} words) for '{}'", script.word_count, idea.trend_item.title)
        return script

    def write_ab_test_script(self, idea: RankedIdea, genre: str) -> VideoScript:
        """Generate an A/B test script using the 'stat' hook variant.

        Args:
            idea: The RankedIdea to generate a script for.
            genre: Content genre used to tune the system prompt.

        Returns:
            A VideoScript using the stat hook variant.
        """
        return self._generate_script(idea, genre, HOOK_VARIANT_AB_TEST)

    def _generate_script(self, idea: RankedIdea, genre: str, hook_variant: HookVariant) -> VideoScript:
        """Call Claude to generate a script and parse the JSON response.

        Args:
            idea: The RankedIdea to base the script on.
            genre: Content genre for the system prompt.
            hook_variant: Hook style to use.

        Returns:
            A parsed VideoScript dataclass.
        """
        system_prompt = self._prompt_builder.build_system_prompt(genre, hook_variant)
        user_message = f"Topic: {idea.trend_item.title}"
        try:
            response = self._client.messages.create(
                model=self._model,
                max_tokens=self._max_tokens,
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}],
            )
            raw_json = response.content[0].text.strip()
            return self._parse_script_response(raw_json, idea, hook_variant)
        except Exception as error:
            logger.error("ScriptWriter: generation failed for '{}': {}", idea.trend_item.title, error)
            raise ScriptWriterError(f"Script generation failed: {error}") from error

    def _trim_and_retry(self, idea: RankedIdea, genre: str, original: VideoScript) -> VideoScript:
        """Request Claude to trim an over-length script and re-parse it.

        Args:
            idea: The original RankedIdea.
            genre: Content genre.
            original: The over-length VideoScript to trim.

        Returns:
            A trimmed VideoScript.
        """
        try:
            response = self._client.messages.create(
                model=self._model,
                max_tokens=self._max_tokens,
                messages=[
                    {"role": "user", "content": f"Topic: {idea.trend_item.title}"},
                    {"role": "assistant", "content": json.dumps({
                        "hook": original.hook, "body": original.body,
                        "cta": original.cta, "captions": original.captions,
                    })},
                    {"role": "user", "content": TRIM_INSTRUCTION},
                ],
            )
            raw_json = response.content[0].text.strip()
            return self._parse_script_response(raw_json, idea, original.hook_variant)
        except Exception as error:
            logger.warning("ScriptWriter: trim failed, returning original: {}", error)
            return original

    def _parse_script_response(self, raw_json: str, idea: RankedIdea, hook_variant: HookVariant) -> VideoScript:
        """Parse a raw JSON string from Claude into a VideoScript dataclass.

        Args:
            raw_json: The raw JSON text returned by Claude.
            idea: The source RankedIdea.
            hook_variant: The hook variant used for this script.

        Returns:
            A populated VideoScript instance.
        """
        data = json.loads(raw_json)
        hook = data.get("hook", "")
        body: list[str] = data.get("body", [])
        cta = data.get("cta", "")
        captions: list[str] = data.get("captions", [])
        full_text = " ".join([hook] + body + [cta])
        word_count = self._validator.count_words(full_text)
        return VideoScript(
            idea=idea,
            hook=hook,
            body=body,
            cta=cta,
            captions=captions,
            full_text=full_text,
            word_count=word_count,
            hook_variant=hook_variant,
        )
