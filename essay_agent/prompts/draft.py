"""essay_agent.prompts.draft

High-stakes production prompt for expanding an outline into a full first-person draft.
The prompt is built with the shared ``make_prompt`` helper so it can be rendered to a
string via ``render_template``.  Downstream code must pass the following variables:

* ``outline`` – JSON or rich-text outline structure to expand.
* ``voice_profile`` – Short description of the writer’s authentic voice.
* ``word_count`` – Target word count for the final draft.

The prompt enforces:
1. Preservation of the user’s voice.
2. Vivid detail and smooth transitions.
3. Strict JSON-only output: ``{"draft": "..."}``.
"""

from __future__ import annotations

from essay_agent.prompts.templates import make_prompt

# ---------------------------------------------------------------------------
# Drafting Agent Prompt ------------------------------------------------------
# ---------------------------------------------------------------------------

DRAFT_PROMPT = make_prompt(
    # NOTE: use double braces to escape literal braces inside format string
    """SYSTEM: You are the Drafting Agent for a college-essay assistant. Your goal is to
transform a structured outline into a compelling, first-person narrative draft that
reflects the student’s authentic voice.

CONSTRAINTS (follow *all*):
1. Write *strictly* in the first person.
2. Preserve the tone described in the voice profile (**{voice_profile}**).
3. Use vivid sensory details and smooth transitions between sections.
4. Aim for **{word_count}** words (±5%).
5. Do **NOT** invent facts outside the outline.
6. Return **only** valid JSON with the key "draft". No additional keys, commentary, or
   Markdown. Example: `{{\"draft\": \"...\"}}`.

RESOURCES:
OUTLINE_JSON:
{outline}

TODAY: {today}
"""
)

__all__ = ["DRAFT_PROMPT"] 