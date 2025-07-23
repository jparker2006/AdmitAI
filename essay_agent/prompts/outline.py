from __future__ import annotations

"""essay_agent.prompts.outline

High-stakes production prompt for the *Outlining Agent*.  The prompt is stored
as a Python module so that it can be imported, type-checked and benefit from
IDE support.
"""

from essay_agent.prompts.templates import make_prompt, inject_example
from essay_agent.prompts.example_registry import EXAMPLE_REGISTRY

# ✅ Refactored for GPT-4o, 100x reliability
_RAW_TEMPLATE = """
<role>
You are an essay-outline strategist who converts a story into a 5-part outline.
</role>

<input>
Story: {story}
EssayPrompt: {essay_prompt}
WordCount: {word_count}
Date: {today}
</input>

<constraints>
You MUST respond with valid JSON exactly matching the schema below.  
• Provide hook, context, conflict, growth, reflection – each 25-50 words.  
• estimated_word_count must equal WordCount.  
• No markdown or extra keys.
</constraints>

<output_schema>
{
  "outline": {
    "hook": "string",
    "context": "string",
    "conflict": "string",
    "growth": "string",
    "reflection": "string"
  },
  "estimated_word_count": 650
}
</output_schema>
"""

OUTLINE_PROMPT = make_prompt(
    inject_example(_RAW_TEMPLATE, EXAMPLE_REGISTRY["outline"])
)

__all__ = ["OUTLINE_PROMPT"] 