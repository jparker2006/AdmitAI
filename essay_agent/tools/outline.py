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
from essay_agent.memory.simple_memory import ensure_essay_record, SimpleMemory
from essay_agent.memory.user_profile_schema import EssayVersion
from datetime import datetime


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
        self, *, story: str, prompt: str, word_count: int = 650, user_id: str | None = None, **_: Any
    ) -> Dict[str, Any]:
        from essay_agent.tools.errors import ToolError
        
        # Check if story is a failed tool result
        if isinstance(story, dict) and "error" in story and story["error"] is not None:
            raise ValueError(f"Cannot process - upstream brainstorm tool failed: {story['error']}")
        
        # Extract actual story from successful tool result
        if isinstance(story, dict) and "ok" in story:
            if story["ok"] is None:
                raise ValueError("Brainstorm tool returned no result")
            story = story["ok"]
            # If it's a dict with 'stories' key, extract first story
            if isinstance(story, dict) and "stories" in story:
                stories = story["stories"]
                if isinstance(stories, list) and len(stories) > 0:
                    story = stories[0].get("title", "Personal Story")
                else:
                    story = "Personal Story"
        
        story = str(story).strip()
        prompt_txt = str(prompt).strip()
        if not story:
            raise ValueError("'story' must be a non-empty string")
        if not prompt_txt:
            raise ValueError("'prompt' must be a non-empty string")
        if not isinstance(word_count, int) or word_count <= 0:
            raise ValueError("'word_count' must be a positive integer")

        # Render high-stakes prompt --------------------------------------
        # Calculate word distribution for structural planning
        hook_words = int(word_count * 0.125)  # 12.5% average of 10-15%
        context_words = int(word_count * 0.225)  # 22.5% average of 20-25%
        conflict_words = int(word_count * 0.275)  # 27.5% average of 25-30%
        growth_words = int(word_count * 0.275)  # 27.5% average of 25-30%
        reflection_words = int(word_count * 0.175)  # 17.5% average of 15-20%
        
        # Calculate percentages for display
        hook_percentage = "10-15"
        context_percentage = "20-25"
        conflict_percentage = "25-30"
        growth_percentage = "25-30"
        reflection_percentage = "15-20"
        
        prompt_rendered = render_template(
            OUTLINE_PROMPT,
            story=story,
            essay_prompt=prompt_txt,
            word_count=word_count,
            hook_words=hook_words,
            context_words=context_words,
            conflict_words=conflict_words,
            growth_words=growth_words,
            reflection_words=reflection_words,
            hook_percentage=hook_percentage,
            context_percentage=context_percentage,
            conflict_percentage=conflict_percentage,
            growth_percentage=growth_percentage,
            reflection_percentage=reflection_percentage,
        )

        # Call LLM in sync mode with automatic retry via llm_client.chat ----
        raw = chat(prompt_rendered, temperature=0)

        # Offline mode returns the literal string "FAKE_RESPONSE" ----------
        if raw == "FAKE_RESPONSE":
            result = _build_stub(story, prompt_txt, word_count)
        else:
            # Attempt to parse JSON -------------------------------------------
            try:
                parsed: Dict[str, Any] = json.loads(raw)
                
                # Basic schema validation -----------------------------------------
                outline = parsed.get("outline")
                if not isinstance(outline, dict):
                    result = _build_stub(story, prompt_txt, word_count)
                else:
                    required_keys = {"hook", "context", "conflict", "growth", "reflection"}
                    if required_keys - set(outline):
                        result = _build_stub(story, prompt_txt, word_count)
                    else:
                        # Ensure estimated_word_count present -----------------------------
                        if "estimated_word_count" not in parsed:
                            parsed["estimated_word_count"] = word_count
                        result = parsed
                        
            except json.JSONDecodeError:
                result = _build_stub(story, prompt_txt, word_count)

        # --------------------- Memory persistence -------------------------
        if user_id:
            try:
                rec = ensure_essay_record(user_id, prompt_txt)
                rec.status = "outline"
                rec.final_version = 0
                # store outline inside first version placeholder
                ver = EssayVersion(
                    version=0,
                    timestamp=datetime.utcnow(),
                    content=json.dumps(result["outline"], ensure_ascii=False),
                    word_count=word_count,
                )
                rec.versions.append(ver)
                # Save profile
                profile = SimpleMemory.load(user_id)
                SimpleMemory.save(user_id, profile)
            except Exception:
                pass

        return result

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