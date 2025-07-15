"""essay_agent.tools.writing_tools

LangChain-compatible drafting & writing tools (Section 3.4).  Each tool wraps a
high-stakes GPT-4 prompt from ``essay_agent.prompts.writing`` and validates the
strict JSON output.
"""

from __future__ import annotations

import json
from typing import Any, Dict

from essay_agent.prompts.templates import render_template
from essay_agent.response_parser import schema_parser, safe_parse
from essay_agent.llm_client import get_chat_llm, call_llm
from essay_agent.tools.base import ValidatedTool
from essay_agent.tools import register_tool
from essay_agent.prompts.writing import (
    OUTLINE_EXPANSION_PROMPT,
    PARAGRAPH_REWRITE_PROMPT,
    OPENING_IMPROVEMENT_PROMPT,
    VOICE_STRENGTHENING_PROMPT,
)

# ---------------------------------------------------------------------------
# JSON Schemas ---------------------------------------------------------------
# ---------------------------------------------------------------------------

_OUTLINE_EXPANSION_SCHEMA = {
    "type": "object",
    "properties": {"expanded_paragraph": {"type": "string"}},
    "required": ["expanded_paragraph"],
}

_PARAGRAPH_REWRITE_SCHEMA = {
    "type": "object",
    "properties": {"rewritten_paragraph": {"type": "string"}},
    "required": ["rewritten_paragraph"],
}

_OPENING_IMPROVEMENT_SCHEMA = {
    "type": "object",
    "properties": {"improved_opening": {"type": "string"}},
    "required": ["improved_opening"],
}

_VOICE_STRENGTHENING_SCHEMA = {
    "type": "object",
    "properties": {"voice_adjusted_paragraph": {"type": "string"}},
    "required": ["voice_adjusted_paragraph"],
}


# ---------------------------------------------------------------------------
# Helper ---------------------------------------------------------------------
# ---------------------------------------------------------------------------

def _call_and_parse(prompt: str, schema: Dict[str, Any]) -> Dict[str, Any]:  # noqa: D401
    """Helper: call LLM with *prompt* and parse against *schema*."""

    llm = get_chat_llm()
    raw = call_llm(llm, prompt)
    parsed = safe_parse(schema_parser(schema), raw)

    # ``safe_parse`` returns a plain dict when using ``schema_parser``
    if isinstance(parsed, dict):
        return parsed

    # Unexpected – handle gracefully
    try:
        return json.loads(str(parsed))
    except Exception as exc:  # noqa: BLE001
        raise ValueError(f"Failed to parse tool output: {exc}") from exc


# ---------------------------------------------------------------------------
# Tool Implementations -------------------------------------------------------
# ---------------------------------------------------------------------------

@register_tool("expand_outline_section")
class OutlineExpansionTool(ValidatedTool):
    """Expand a single outline section into a vivid paragraph."""

    name: str = "expand_outline_section"
    description: str = (
        "Expand a single outline section into a vivid paragraph while preserving voice."
    )

    timeout: float = 15.0

    def _run(
        self,
        *,
        outline_section: str,
        section_name: str,
        voice_profile: str,
        target_words: int = 120,
        **_: Any,
    ) -> Dict[str, Any]:  # type: ignore[override]
        # Input validation --------------------------------------------------
        outline_section = str(outline_section).strip()
        section_name = str(section_name).strip()
        voice_profile = str(voice_profile).strip()

        if not outline_section:
            raise ValueError("outline_section must not be empty.")
        if not section_name:
            raise ValueError("section_name must not be empty.")
        if not voice_profile:
            raise ValueError("voice_profile must not be empty.")
        if not (30 <= target_words <= 400):
            raise ValueError("target_words must be between 30 and 400.")

        # Render prompt -----------------------------------------------------
        prompt_text = render_template(
            OUTLINE_EXPANSION_PROMPT,
            outline_section=outline_section,
            section_name=section_name,
            voice_profile=voice_profile,
            target_words=target_words,
        )

        # Call & parse ------------------------------------------------------
        result = _call_and_parse(prompt_text, _OUTLINE_EXPANSION_SCHEMA)
        paragraph = str(result.get("expanded_paragraph", "")).strip()
        if not paragraph:
            raise ValueError("expanded_paragraph is empty.")
        return {"expanded_paragraph": paragraph}


@register_tool("rewrite_paragraph")
class ParagraphRewriteTool(ValidatedTool):
    """Rewrite paragraph to meet a style/tone instruction."""

    name: str = "rewrite_paragraph"
    description: str = (
        "Rewrite an existing paragraph to match a specific stylistic instruction while preserving voice."
    )

    timeout: float = 45.0  # paragraph rewriting requires careful analysis

    def _run(
        self,
        *,
        paragraph: str,
        style_instruction: str,
        voice_profile: str,
        **_: Any,
    ) -> Dict[str, Any]:  # type: ignore[override]
        # Validation --------------------------------------------------------
        paragraph = str(paragraph).strip()
        style_instruction = str(style_instruction).strip()
        voice_profile = str(voice_profile).strip()

        if not paragraph:
            raise ValueError("paragraph must not be empty.")
        if not style_instruction:
            raise ValueError("style_instruction must not be empty.")
        if not voice_profile:
            raise ValueError("voice_profile must not be empty.")
        if len(style_instruction) > 300:
            raise ValueError("style_instruction too long (max 300 chars).")

        # Prompt ------------------------------------------------------------
        prompt_text = render_template(
            PARAGRAPH_REWRITE_PROMPT,
            paragraph=paragraph,
            style_instruction=style_instruction,
            voice_profile=voice_profile,
        )

        result = _call_and_parse(prompt_text, _PARAGRAPH_REWRITE_SCHEMA)
        rewritten = str(result.get("rewritten_paragraph", "")).strip()
        if not rewritten:
            raise ValueError("rewritten_paragraph is empty.")
        return {"rewritten_paragraph": rewritten}


@register_tool("improve_opening")
class OpeningImprovementTool(ValidatedTool):
    """Improve an opening sentence to create a stronger hook."""

    name: str = "improve_opening"
    description: str = (
        "Improve an opening sentence to create a compelling hook while matching voice."
    )

    timeout: float = 10.0

    def _run(
        self,
        *,
        opening_sentence: str,
        essay_context: str,
        voice_profile: str,
        **_: Any,
    ) -> Dict[str, Any]:  # type: ignore[override]
        opening_sentence = str(opening_sentence).strip()
        essay_context = str(essay_context).strip()
        voice_profile = str(voice_profile).strip()

        if not opening_sentence:
            raise ValueError("opening_sentence must not be empty.")
        if not essay_context:
            raise ValueError("essay_context must not be empty.")
        if not voice_profile:
            raise ValueError("voice_profile must not be empty.")

        prompt_text = render_template(
            OPENING_IMPROVEMENT_PROMPT,
            opening_sentence=opening_sentence,
            essay_context=essay_context,
            voice_profile=voice_profile,
        )

        result = _call_and_parse(prompt_text, _OPENING_IMPROVEMENT_SCHEMA)
        improved = str(result.get("improved_opening", "")).strip()
        if not improved:
            raise ValueError("improved_opening is empty.")
        return {"improved_opening": improved}


@register_tool("strengthen_voice")
class VoiceStrengtheningTool(ValidatedTool):
    """Adjust paragraph to better match the user's authentic voice profile."""

    name: str = "strengthen_voice"
    description: str = (
        "Adjust a paragraph to better match the user's authentic voice profile."
    )

    timeout: float = 45.0  # voice strengthening requires deep analysis

    def _run(
        self,
        *,
        paragraph: str,
        voice_profile: str,
        target_voice_traits: str,
        **_: Any,
    ) -> Dict[str, Any]:  # type: ignore[override]
        paragraph = str(paragraph).strip()
        voice_profile = str(voice_profile).strip()
        target_voice_traits = str(target_voice_traits).strip()

        if not paragraph:
            raise ValueError("paragraph must not be empty.")
        if not voice_profile:
            raise ValueError("voice_profile must not be empty.")
        if not target_voice_traits:
            raise ValueError("target_voice_traits must not be empty.")

        prompt_text = render_template(
            VOICE_STRENGTHENING_PROMPT,
            paragraph=paragraph,
            voice_profile=voice_profile,
            target_voice_traits=target_voice_traits,
        )

        result = _call_and_parse(prompt_text, _VOICE_STRENGTHENING_SCHEMA)
        adjusted = str(result.get("voice_adjusted_paragraph", "")).strip()
        if not adjusted:
            raise ValueError("voice_adjusted_paragraph is empty.")
        return {"voice_adjusted_paragraph": adjusted} 