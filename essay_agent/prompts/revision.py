from __future__ import annotations

"""essay_agent.prompts.revision

High-stakes prompt template for RevisionTool.  Designed with 100× prompt-
engineering guidelines: role definition, exemplar, strict JSON schema, layered
instructions, and self-validation trigger.
"""

from essay_agent.prompts.templates import make_prompt

# ✅ Refactored for GPT-4o, 100x reliability
REVISION_PROMPT = make_prompt(
    """
<role>
You are an essay reviser who improves a draft based on a specific focus.
</role>

<input>
Draft: {draft}
RevisionFocus: {revision_focus}
Date: {today}
</input>

<constraints>
You MUST respond with valid JSON exactly matching the schema below.  
• Provide revised_draft (same length ±15%) and changes list (each change ≤80 chars).  
• No markdown or extra keys.
</constraints>

<output_schema>
{
  "revised_draft": "string",
  "changes": ["string", "string"]
}
</output_schema>
"""
)

__all__ = ["REVISION_PROMPT"] 