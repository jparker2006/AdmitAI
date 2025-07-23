"""essay_agent.tools.guidance_tools

Tools for providing strategic guidance and coaching.
"""

from __future__ import annotations
from typing import Any, Dict, List
from pydantic import BaseModel, Field

from essay_agent.prompts.templates import render_template
from essay_agent.response_parser import pydantic_parser, safe_parse
from essay_agent.llm_client import get_chat_llm, call_llm
from essay_agent.tools.base import ValidatedTool
from essay_agent.tools import register_tool
from essay_agent.prompts.guidance import SUGGEST_NEXT_ACTIONS_PROMPT

class SuggestedAction(BaseModel):
    action: str = Field(..., description="A concrete action the user can take.")
    reasoning: str = Field(..., description="Why this is a good next step.")

class SuggestNextActionsResult(BaseModel):
    suggested_actions: List[SuggestedAction] = Field(..., description="A list of suggested next actions.")

@register_tool("suggest_next_actions")
class SuggestNextActionsTool(ValidatedTool):
    """Suggest actionable next steps for the user based on their current context."""
    name: str = "suggest_next_actions"
    description: str = "Suggest actionable next steps to help the user progress."

    def _run(self, *, essay_state: str, conversation_history: str, **_: Any) -> Dict[str, Any]:
        rendered_prompt = render_template(
            SUGGEST_NEXT_ACTIONS_PROMPT,
            essay_state=essay_state,
            conversation_history=conversation_history,
        )

        llm = get_chat_llm(temperature=0.5) # Allow for some creativity in suggestions
        raw = call_llm(llm, rendered_prompt)
        
        parser = pydantic_parser(SuggestNextActionsResult)
        parsed = safe_parse(parser, raw)
        
        return parsed.model_dump() 