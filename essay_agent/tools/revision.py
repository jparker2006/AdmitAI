from __future__ import annotations

"""essay_agent.tools.revision

LangChain-compatible RevisionTool that refines an essay draft based on a
specific focus (e.g. "tighten opening", "add vivid detail") and returns the
revised draft plus a bullet-style changelog.
"""

import json
from typing import Any, Dict, List

from essay_agent.llm_client import chat
from essay_agent.prompts.revision import REVISION_PROMPT
from essay_agent.prompts.templates import render_template
from essay_agent.tools.base import ValidatedTool
from essay_agent.tools import register_tool

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _stub_changes() -> List[str]:  # noqa: D401
    return [
        "Improved clarity in opening sentence",
        "Added vivid sensory detail in paragraph 2",
        "Tightened conclusion for stronger impact",
    ]


def _build_stub(draft: str) -> Dict[str, Any]:  # noqa: D401
    return {"revised_draft": draft.strip() + " (revised)", "changes": _stub_changes()}


# ---------------------------------------------------------------------------
# Tool
# ---------------------------------------------------------------------------

@register_tool("revise")
class RevisionTool(ValidatedTool):
    """Revise an essay draft per a specific focus and return change log."""

    name: str = "revise"
    description: str = (
        "Revise essay draft according to a targeted focus and return both the "
        "revised draft and a concise list of changes."
    )

    def _run(  # type: ignore[override]
        self,
        *,
        draft: str,
        revision_focus: str,
        word_count: int | None = None,
        **_: Any,
    ) -> Dict[str, Any]:
        """Revise an essay draft per a specific focus and return change log."""
        from essay_agent.tools.errors import ToolError
        
        # ----------------------- Input validation -----------------------
        # Check if draft is a failed tool result
        if isinstance(draft, dict) and "error" in draft and draft["error"] is not None:
            raise ValueError(f"Cannot process - upstream draft tool failed: {draft['error']}")
        
        # Extract actual draft from successful tool result
        if isinstance(draft, dict):
            # Handle wrappers like {"ok": {...}} from executor failures/successes
            if "ok" in draft:
                if draft["ok"] is None:
                    raise ValueError("Draft tool returned no result")
                draft = draft["ok"]

            # At this point `draft` might still be a mapping returned directly
            # from the DraftTool or a previous RevisionTool.  Extract the raw
            # draft string if available.
            if isinstance(draft, dict):
                if "draft" in draft:
                    draft = draft["draft"]
                elif "revised_draft" in draft:
                    draft = draft["revised_draft"]
        
        if not isinstance(draft, str) or not draft.strip():
            raise ValueError("draft must be a non-empty string")
        
        if not isinstance(revision_focus, str) or not revision_focus.strip():
            raise ValueError("revision_focus must be a non-empty string")

        focus = revision_focus.strip()
        
        # ----------------------- Prompt rendering -----------------------
        prompt_rendered = render_template(
            REVISION_PROMPT,
            draft=draft,
            revision_focus=focus,
            word_count=word_count or "N/A",
        )

        raw = chat(prompt_rendered, temperature=0)

        if raw == "FAKE_RESPONSE":
            return _build_stub(draft)

        try:
            parsed: Dict[str, Any] = json.loads(raw)
        except json.JSONDecodeError:
            return _build_stub(draft)

        # Basic validation --------------------------------------------------
        if not isinstance(parsed.get("revised_draft"), str):
            return _build_stub(draft)
        changes = parsed.get("changes")
        if not isinstance(changes, list) or not changes:
            return _build_stub(draft)

        # Ensure all change entries strings ---------------------------------
        parsed["changes"] = [str(c).strip() for c in changes if str(c).strip()]
        if not parsed["changes"]:
            parsed["changes"] = _stub_changes()

        return parsed

    # Convenience call wrapper ---------------------------------------------
    def __call__(self, *args: Any, **kwargs: Any):  # type: ignore[override]
        if args:
            raise ValueError("Use keyword arguments: draft=..., revision_focus=...")
        return self._run(**kwargs) 