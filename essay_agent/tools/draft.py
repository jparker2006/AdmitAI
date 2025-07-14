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
from essay_agent.llm_client import get_chat_llm, truncate_context
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
    timeout: float = 30.0

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
        """Generate a full essay draft from an outline."""
        from essay_agent.tools.errors import ToolError
        import json
        
        # ----------------------- Input validation -----------------------
        # Check if outline is a failed tool result
        if isinstance(outline, dict) and "error" in outline and outline["error"] is not None:
            raise ValueError(f"Cannot process - upstream outline tool failed: {outline['error']}")
        
        # Extract actual outline from successful tool result
        if isinstance(outline, dict) and "ok" in outline:
            if outline["ok"] is None:
                raise ValueError("Outline tool returned no result")
            outline = outline["ok"]
        
        if not voice_profile or not voice_profile.strip():
            raise ValueError("voice_profile must not be empty.")

        if not (10 <= word_count <= 1000):
            raise ValueError("word_count must be between 10 and 1000.")

        if isinstance(outline, dict):
            outline_str = json.dumps(outline, ensure_ascii=False, indent=2, default=str)
        else:
            outline_str = str(outline).strip()
            if not outline_str:
                raise ValueError("outline must not be empty.")

        # ----------------------- Prompt rendering -----------------------
        # Truncate voice_profile to prevent token limit issues
        voice_profile_truncated = truncate_context(voice_profile.strip(), max_tokens=10000)
        
        # For very large profiles, extract only essential information
        try:
            profile_data = json.loads(voice_profile_truncated)
            
            # If still too large, create a summary profile
            if len(voice_profile_truncated) > 20000:  # Very large profile
                essential_profile = {
                    "user_info": profile_data.get("user_info", {}),
                    "core_values": profile_data.get("core_values", []),
                    "writing_voice": profile_data.get("writing_voice"),
                    "recent_essays": profile_data.get("essay_history", [])[-2:] if profile_data.get("essay_history") else []
                }
                voice_profile_truncated = json.dumps(essential_profile, indent=2, default=str)
        except (json.JSONDecodeError, KeyError):
            # If not JSON, just truncate aggressively
            if len(voice_profile_truncated) > 20000:
                voice_profile_truncated = voice_profile_truncated[:20000] + "\n... [truncated for length]"
        
        prompt = render_template(
            DRAFT_PROMPT,
            outline=outline_str,
            voice_profile=voice_profile_truncated,
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