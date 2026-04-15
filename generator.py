"""Course generation engine - API call logic and prompt construction."""

import json
from pathlib import Path

import yaml
import anthropic


PROMPTS_DIR = Path(__file__).parent / "prompts"
WORDS_PER_MINUTE = 150


def _load_prompt_template() -> dict:
    """Load the system prompt template from YAML."""
    with open(PROMPTS_DIR / "system_prompt.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _load_output_schema() -> dict:
    """Load the expected output JSON schema."""
    with open(PROMPTS_DIR / "output_schema.json", "r", encoding="utf-8") as f:
        return json.load(f)


def build_prompt(
    topic: str,
    audience_level: str,
    target_duration: int,
    tone: str,
    additional_context: str = "",
) -> tuple[str, str]:
    """Build system and user prompts from template and inputs.

    Returns (system_prompt, user_prompt) tuple.
    """
    template = _load_prompt_template()
    schema = _load_output_schema()
    word_count = target_duration * WORDS_PER_MINUTE

    additional_context_block = ""
    if additional_context.strip():
        additional_context_block = template["additional_context_template"].format(
            additional_context=additional_context
        )

    system_prompt = template["role"].format(
        target_duration=target_duration,
        audience_level=audience_level,
    )

    user_prompt = template["instructions"].format(
        topic=topic,
        audience_level=audience_level,
        tone=tone,
        target_duration=target_duration,
        word_count=word_count,
        additional_context_block=additional_context_block,
    )

    user_prompt += (
        "\n\nRespond with a JSON object matching this schema:\n"
        + json.dumps(schema, indent=2)
    )

    return system_prompt, user_prompt


def generate_course(
    api_key: str,
    topic: str,
    audience_level: str,
    target_duration: int,
    tone: str,
    additional_context: str = "",
) -> dict:
    """Generate a micro-course by calling the Anthropic Messages API.

    Returns the parsed course dictionary.
    """
    system_prompt, user_prompt = build_prompt(
        topic, audience_level, target_duration, tone, additional_context
    )

    client = anthropic.Anthropic(
        api_key=api_key,
        max_retries=3,
        timeout=120.0,
    )

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=8192,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )

    response_text = message.content[0].text

    # Extract JSON from response - handle possible markdown code fences
    text = response_text.strip()
    if text.startswith("```"):
        # Remove opening fence (with optional language tag)
        first_newline = text.index("\n")
        text = text[first_newline + 1 :]
        # Remove closing fence
        if text.endswith("```"):
            text = text[: -3].strip()

    course = json.loads(text)
    return course
