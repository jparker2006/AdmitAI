"""essay_agent.tools.draft

LangChain-compatible DraftTool: expands a structured outline into a complete
first-person draft while preserving the user’s voice profile.
"""

from __future__ import annotations

import json
from typing import Any, Dict, Union

from langchain.llms.fake import FakeListLLM

from essay_agent.tools import register_tool
from essay_agent.tools.base import ValidatedTool
from essay_agent.llm_client import get_chat_llm
from essay_agent.prompts.draft import DRAFT_PROMPT
from essay_agent.prompts.templates import render_template
from essay_agent.response_parser import safe_parse, schema_parser

# JSON schema used for validating the LLM response ---------------------------
_SCHEMA = {
    "type": "object",
    "properties": {
        "draft": {"type": "string"},
    },
    "required": ["draft"],
}


@register_tool("draft")
class DraftTool(ValidatedTool):
    """Generate a full essay draft from an outline.

    The tool renders a high-stakes prompt, calls GPT-4 (or a fake LLM during
    offline/CI runs), parses the JSON output, and performs final validation.
    """

    name: str = "draft"
    description: str = (
        "Expand an outline into a complete first-person draft while preserving the user’s voice."
    )

    # Drafting can take longer than quick tools
    timeout: float = 15.0

    # ------------------------------------------------------------------
    # LangChain sync execution
    # ------------------------------------------------------------------
    def _run(
        self,
        *,
        outline: Union[Dict[str, Any], str],
        voice_profile: str,
        word_count: int = 650,
        **_: Any,
    ) -> Dict[str, str]:  # type: ignore[override]
        """Return a JSON dict ``{"draft": "..."}``.

        Args:
            outline: Structured outline (dict) or plain string.
            voice_profile: Short description of writing voice.
            word_count: Target word count (10–1000).
        Returns:
            dict: Parsed JSON with key ``draft``.
        Raises:
            ValueError: On invalid inputs or LLM output.
        """

        # ----------------------- Input validation -----------------------
        if not voice_profile or not voice_profile.strip():
            raise ValueError("voice_profile must not be empty.")

        if not (10 <= word_count <= 1000):
            raise ValueError("word_count must be between 10 and 1000.")

        if isinstance(outline, dict):
            outline_str = json.dumps(outline, ensure_ascii=False, indent=2)
        else:
            outline_str = str(outline).strip()
            if not outline_str:
                raise ValueError("outline must not be empty.")

        # ----------------------- Prompt rendering -----------------------
        prompt = render_template(
            DRAFT_PROMPT,
            outline=outline_str,
            voice_profile=voice_profile.strip(),
            word_count=word_count,
        )

        # ----------------------- LLM call -------------------------------
        llm = get_chat_llm()
        from essay_agent.llm_client import call_llm
        response: str = call_llm(llm, prompt)

        # Allow FakeListLLM deterministic fallback -----------------------
        if isinstance(llm, FakeListLLM):
            # FakeListLLM returns pre-canned responses; we still parse them below
            pass

        # ----------------------- Parse & validate -----------------------
        parsed = safe_parse(schema_parser(_SCHEMA), response)
        draft_text: str = str(parsed["draft"]).strip()

        if not draft_text:
            raise ValueError("Draft text is empty.")

        # Tolerate small overruns (<= +50 words) -------------------------
        if word_count > 0 and len(draft_text.split()) > word_count + 50:
            raise ValueError("Draft exceeds allowed word count tolerance.")

        return {"draft": draft_text} 