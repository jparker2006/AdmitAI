"""essay_agent.prompts.guidance

Prompts for tools that provide strategic guidance and coaching to the user.
"""

from __future__ import annotations
from essay_agent.prompts.templates import make_prompt

# ---------------------------------------------------------------------------
# Suggest Next Actions (Proactive Guidance)
# ---------------------------------------------------------------------------
SUGGEST_NEXT_ACTIONS_PROMPT = make_prompt(
    """
<role>
You are an expert essay coach. Based on the user's situation, suggest 3-5 clear, actionable next steps to help them move forward.
</role>

<input>
  <current_essay_state>
  {essay_state}
  </current_essay_state>
  <conversation_history>
  {conversation_history}
  </conversation_history>
</input>

<constraints>
You MUST respond with valid JSON.
Each suggestion must be a concrete action the user can take right now.
Suggestions should be tailored to the user's current stage (e.g., brainstorming, drafting, polishing).
</constraints>

<output_schema>
{{
  "suggested_actions": [
    {{
      "action": "string (e.g., 'Brainstorm more story ideas')",
      "reasoning": "string (Why this is a good next step)"
    }}
  ]
}}
</output_schema>
"""
)

__all__ = ["SUGGEST_NEXT_ACTIONS_PROMPT"] 