"""essay_agent.prompts.brainstorm

Upgraded high-stakes prompt for BrainstormTool.  Produces exactly 3 authentic
story ideas in strict JSON format.  Variables required: ``essay_prompt``,
``profile``, plus meta variable ``today`` injected by the template helper.

Enhanced with college-scoped diversification and prompt-type story mapping.
"""

from __future__ import annotations

from essay_agent.prompts.templates import make_prompt, inject_example
from essay_agent.prompts.example_registry import EXAMPLE_REGISTRY

# ---------------------------------------------------------------------------
# Compact XML-sectioned Brainstorming Prompt (≤400 tokens)
# ---------------------------------------------------------------------------

_RAW_TEMPLATE = (
    """
<role>
You are an expert college-essay brainstorming coach who crafts authentic, unique story ideas.
</role>

<input>
EssayPrompt: {essay_prompt}
Profile: {profile}
College: {college_name}
UsedStories: {college_story_history}
CrossCollegeSuggestions: {cross_college_suggestions}
PromptType: {prompt_type}
Categories: {recommended_categories}
Date: {today}
</input>

<constraints>
 You MUST respond with valid JSON that exactly matches the schema below.  
 • Generate exactly 3 distinct story ideas relevant to EssayPrompt.  
 • Do not repeat any story in UsedStories; reuse CrossCollegeSuggestions only if it fits.  
 • Titles are 4-8 words. Descriptions are two sentences (≤40 words total).  
 • Avoid clichés and ensure each story shows growth or values.
 • Respond with NOTHING BUT the JSON object—no markdown, no extra keys, no comments.
</constraints>

<self_check>
Before sending, verify:
1) Exactly 3 objects in "stories".
2) Keys: title, description, prompt_fit, insights, themes (and no others).
3) Output is valid JSON with no markdown or prose.
</self_check>

<output_schema>
{{
  "stories": [
    {{
      "title": "string (4-8 words)",
      "description": "string (<=40 words, 2 sentences)",
      "prompt_fit": "string (1 sentence on prompt alignment)",
      "insights": ["string", "string"],
      "themes": ["string"]
    }},
    {{
      "title": "string",
      "description": "string",
      "prompt_fit": "string",
      "insights": ["string"],
      "themes": ["string"]
    }},
    {{
      "title": "string",
      "description": "string",
      "prompt_fit": "string",
      "insights": ["string"],
      "themes": ["string"]
    }}
  ]
}}
</output_schema>
"""
)

BRAINSTORM_PROMPT = make_prompt(
    inject_example(_RAW_TEMPLATE, EXAMPLE_REGISTRY["brainstorm"])
)

__all__ = ["BRAINSTORM_PROMPT"]