from __future__ import annotations

"""essay_agent.tools.outline

LangChain-compatible tool that generates a structured five-part outline for a
chosen personal story idea.  It uses GPT-4 via :pymod:`essay_agent.llm_client`
under the hood but falls back to a deterministic stub when the environment is
offline (``FakeListLLM``) or the response cannot be parsed as JSON.
"""

import json
from typing import Any, Dict

from essay_agent.llm_client import chat
from essay_agent.prompts.outline import OUTLINE_PROMPT
from essay_agent.prompts.templates import render_template
from essay_agent.tools.base import ValidatedTool
from essay_agent.tools import register_tool


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _build_stub(story: str, prompt: str, word_count: int) -> Dict[str, Any]:  # noqa: D401
    """Return a deterministic outline used in CI/offline mode."""

    outline = {
        "hook": f"A moment that redefined my perspective on: {story[:30]}...",
        "context": "Provide background that anchors the reader and highlights the setting.",
        "conflict": "Describe the central tension or obstacle encountered.",
        "growth": "Explain the actions taken and lessons learned in overcoming the conflict.",
        "reflection": "Conclude with personal insights and how the experience shapes future goals.",
    }
    return {"outline": outline, "estimated_word_count": word_count}


# ---------------------------------------------------------------------------
# Tool implementation
# ---------------------------------------------------------------------------


@register_tool("outline")
class OutlineTool(ValidatedTool):
    """Generate a five-part outline for a personal story idea.

    Input
    -----
    story : str
        The chosen personal story seed selected during brainstorming.
    prompt : str
        The original essay prompt (so the outline stays on-topic).
    word_count : int, default=650
        Target final essay length – used to size each outline section.

    Output (dict)
    --------------
    {
        "outline": {
            "hook": str,
            "context": str,
            "conflict": str,
            "growth": str,
            "reflection": str
        },
        "estimated_word_count": int
    }
    """

    name: str = "outline"
    description: str = (
        "Generate a structured five-part outline (hook, context, conflict, "
        "growth, reflection) for a given story idea. Returns strict JSON."
    )

    # ------------------------------------------------------------------
    # Core sync execution (ValidatedTool requirement)
    # ------------------------------------------------------------------

    def _run(  # type: ignore[override]
        self, *, story: str, prompt: str, word_count: int = 650, **_: Any
    ) -> Dict[str, Any]:
        story = str(story).strip()
        prompt_txt = str(prompt).strip()
        if not story:
            raise ValueError("'story' must be a non-empty string")
        if not prompt_txt:
            raise ValueError("'prompt' must be a non-empty string")
        if not isinstance(word_count, int) or word_count <= 0:
            raise ValueError("'word_count' must be a positive integer")

        # Render high-stakes prompt --------------------------------------
        prompt_rendered = render_template(
            OUTLINE_PROMPT,
            story=story,
            essay_prompt=prompt_txt,
            word_count=word_count,
        )

        # Call LLM in sync mode with automatic retry via llm_client.chat ----
        raw = chat(prompt_rendered, temperature=0)

        # Offline mode returns the literal string "FAKE_RESPONSE" ----------
        if raw == "FAKE_RESPONSE":
            return _build_stub(story, prompt_txt, word_count)

        # Attempt to parse JSON -------------------------------------------
        try:
            parsed: Dict[str, Any] = json.loads(raw)
        except json.JSONDecodeError:
            return _build_stub(story, prompt_txt, word_count)

        # Basic schema validation -----------------------------------------
        outline = parsed.get("outline")
        if not isinstance(outline, dict):
            return _build_stub(story, prompt_txt, word_count)

        required_keys = {"hook", "context", "conflict", "growth", "reflection"}
        if required_keys - set(outline):
            return _build_stub(story, prompt_txt, word_count)

        # Ensure estimated_word_count present -----------------------------
        if "estimated_word_count" not in parsed:
            parsed["estimated_word_count"] = word_count

        return parsed

    # ------------------------------------------------------------------
    # Convenience call wrapper (mirrors EchoTool pattern)
    # ------------------------------------------------------------------

    def __call__(self, *args: Any, **kwargs: Any):  # type: ignore[override]
        """Ergonomic call signatures for tests & executor.

        Examples
        --------
        tool(story="...", prompt="...", word_count=650)
        """
        # Allow pure-keyword usage (preferred) ---------------------------
        if args:
            raise ValueError("Provide inputs as keyword arguments only")
        return self._run(**kwargs) 