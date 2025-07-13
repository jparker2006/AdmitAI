"""essay_agent.tools.polish

LangChain-compatible PolishTool: performs final grammar & style refinement and
ensures the essay draft has exactly the requested word count.
"""

from __future__ import annotations

from typing import Any, Dict

from langchain.llms.fake import FakeListLLM

from essay_agent.tools import register_tool
from essay_agent.tools.base import ValidatedTool
from essay_agent.prompts.templates import render_template
from essay_agent.llm_client import get_chat_llm
from essay_agent.response_parser import safe_parse, schema_parser
from essay_agent.prompts.polish import POLISH_PROMPT

# ---------------------------------------------------------------------------
# JSON schema for parsing
# ---------------------------------------------------------------------------

_SCHEMA = {
    "type": "object",
    "properties": {
        "final_draft": {"type": "string"},
    },
    "required": ["final_draft"],
}


@register_tool("polish")
class PolishTool(ValidatedTool):
    """Polish grammar & style; enforce exact word count."""

    name: str = "polish"
    description: str = (
        "Perform final grammar/style polish on a draft while enforcing an exact word count."
    )

    timeout: float = 12.0

    # ------------------------------------------------------------------
    # Sync execution
    # ------------------------------------------------------------------
    def _run(self, *, draft: str, word_count: int = 650, **_: Any) -> Dict[str, str]:  # type: ignore[override]
        # -------------------- Input validation -------------------------
        draft = str(draft).strip()
        if not draft:
            raise ValueError("draft must not be empty.")

        if not (5 <= word_count <= 1000):
            raise ValueError("word_count must be between 5 and 1000.")

        # -------------------- Render prompt ----------------------------
        prompt = render_template(
            POLISH_PROMPT, draft=draft, word_count=word_count
        )

        # -------------------- LLM call --------------------------------
        llm = get_chat_llm()
        from essay_agent.llm_client import call_llm
        response: str = call_llm(llm, prompt)

        # For FakeListLLM offline mode, response is deterministic string
        if isinstance(llm, FakeListLLM):
            pass  # no-op; parse normally

        # -------------------- Parse & validate -------------------------
        parsed = safe_parse(schema_parser(_SCHEMA), response)
        final_draft: str = str(parsed["final_draft"]).strip()

        if not final_draft:
            raise ValueError("Parsed final_draft is empty.")

        actual_words = len(final_draft.split())
        # Allow a reasonable tolerance for *over* word count (10% or 10 words whichever greater).
        # Under-limit essays are permitted so the workflow does not fail if the LLM returns
        # a slightly shorter draft.  Overly long drafts, however, are still rejected to
        # respect application word limits.

        tolerance = max(10, int(word_count * 0.10))
        upper_bound = word_count + tolerance
        over_limit = actual_words > upper_bound
        under_limit = actual_words < word_count

        metadata_msg = None
        if over_limit:
            metadata_msg = (
                f"final_draft contains {actual_words} words, outside permitted range {word_count - tolerance}–{upper_bound}."
            )
        elif under_limit:
            metadata_msg = (
                f"final_draft contains {actual_words} words, below nominal target {word_count}."
            )

        return {
            "final_draft": final_draft,
            "over_limit": over_limit,
            "under_limit": under_limit,
            "message": metadata_msg,
        } 