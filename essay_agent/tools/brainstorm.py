"""essay_agent.tools.brainstorm

Generate three story ideas for a given essay prompt and user profile.
"""
from __future__ import annotations

from typing import Any, Dict, List

from pydantic import BaseModel, Field

# Tool infrastructure ------------------------------------------------------
from essay_agent.prompts.templates import render_template
from essay_agent.response_parser import pydantic_parser, safe_parse
from essay_agent.llm_client import get_chat_llm
from essay_agent.tools.base import ValidatedTool
from essay_agent.tools import register_tool
from essay_agent.prompts.brainstorm import BRAINSTORM_PROMPT

# ---------------------------------------------------------------------------
# Load prompt text file
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Pydantic schema for parser
# ---------------------------------------------------------------------------

class Story(BaseModel):
    title: str = Field(..., max_length=60)
    description: str
    prompt_fit: str
    insights: List[str]

class BrainstormResult(BaseModel):
    stories: List[Story]

_PARSER = pydantic_parser(BrainstormResult)

# ---------------------------------------------------------------------------
# Tool implementation
# ---------------------------------------------------------------------------


@register_tool("brainstorm")
class BrainstormTool(ValidatedTool):
    """Generate exactly three authentic personal story ideas."""

    name: str = "brainstorm"
    description: str = (
        "Suggest 3 unique personal story ideas for a college essay given the essay prompt and user profile."
    )

    timeout: float = 12.0  # brainstorming can be moderately slow

    # ------------------------------------------------------------------
    # Synchronous execution
    # ------------------------------------------------------------------
    def _run(self, *, essay_prompt: str, profile: str, **_: Any) -> Dict[str, Any]:  # type: ignore[override]
        # -------------------- Input validation -------------------------
        essay_prompt = str(essay_prompt).strip()
        profile = str(profile).strip()
        if not essay_prompt:
            raise ValueError("essay_prompt must not be empty.")
        if not profile:
            raise ValueError("profile must not be empty.")

        # -------------------- Render high-stakes prompt ----------------
        rendered_prompt = render_template(
            BRAINSTORM_PROMPT, essay_prompt=essay_prompt, profile=profile
        )

        # -------------------- LLM call --------------------------------
        # Use a slightly higher temperature for creative idea generation
        llm = get_chat_llm(temperature=0.4)
        from essay_agent.llm_client import call_llm
        raw = call_llm(llm, rendered_prompt)

        # -------------------- Parse & validate -------------------------
        parsed = safe_parse(_PARSER, raw)

        # Business-level validations ----------------------------------
        if len(parsed.stories) != 3:
            raise ValueError("Expected exactly 3 story ideas in output.")

        titles = [s.title.strip() for s in parsed.stories]
        if len(set(titles)) != 3:
            raise ValueError("Story titles must be unique.")

        return parsed.dict() 