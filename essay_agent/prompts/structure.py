"""essay_agent.prompts.structure

High-stakes prompts for essay structure and outline tools.
All prompts use GPT-4 to analyze and optimize essay structure.
"""

from __future__ import annotations

from essay_agent.prompts.templates import make_prompt

# ---------------------------------------------------------------------------
# OutlineGeneratorTool Prompt
# ---------------------------------------------------------------------------

OUTLINE_GENERATOR_PROMPT = make_prompt(
    """
<role>
You are an outline generator who creates a 4-section essay outline from a story.
</role>

<input>
Story: {story}
EssayPrompt: {essay_prompt}
WordCount: {word_count}
Date: {today}
</input>

<constraints>
You MUST respond with valid JSON exactly matching the schema below.  
• Provide hook, context, growth_moment, reflection.  
• section_word_counts must sum to WordCount.  
• Hook ≤25 words; Reflection ≤40 words.  
• No markdown or extra keys.
</constraints>

<output_schema>
{
  "outline": {
    "hook": "string",
    "context": "string",
    "growth_moment": "string",
    "reflection": "string"
  },
  "section_word_counts": {
    "hook": 100,
    "context": 150,
    "growth_moment": 260,
    "reflection": 140
  },
  "estimated_word_count": 650
}
</output_schema>
"""
)

# ---------------------------------------------------------------------------
# StructureValidatorTool Prompt
# ---------------------------------------------------------------------------

STRUCTURE_VALIDATOR_PROMPT = make_prompt(
    """
<role>
You are an essay-outline auditor who scores outline quality on flow, arc, prompt fit, and originality.
</role>

<input>
Outline: {outline}
Date: {today}
</input>

<constraints>
You MUST respond with valid JSON exactly matching the schema below.  
• Provide four rubric scores 0-10 and compute the average as score (1 decimal).  
• is_valid true if score ≥ 7.0.  
• Include 1-3 specific issues and ≤120-word overall_feedback.  
• No markdown or extra keys.
</constraints>

<output_schema>
{
  "is_valid": true,
  "score": 8.2,
  "issues": ["string"],
  "overall_feedback": "string"
}
</output_schema>
"""
)

# ---------------------------------------------------------------------------
# TransitionSuggestionTool Prompt
# ---------------------------------------------------------------------------

TRANSITION_SUGGESTION_PROMPT = make_prompt(
    """
<role>
You are a transition specialist who writes bridge sentences between outline sections.
</role>

<input>
Outline: {outline}
Date: {today}
</input>

<constraints>
You MUST respond with valid JSON exactly matching the schema below.  
• Provide three transitions: hook_to_context, context_to_growth, growth_to_reflection.  
• Each ≤25 words, first-person, no clichés.  
• No markdown or extra keys.
</constraints>

<output_schema>
{
  "transitions": {
    "hook_to_context": "string",
    "context_to_growth": "string",
    "growth_to_reflection": "string"
  }
}
</output_schema>
"""
)

# ---------------------------------------------------------------------------
# LengthOptimizerTool Prompt
# ---------------------------------------------------------------------------

LENGTH_OPTIMIZER_PROMPT = make_prompt(
    """
<role>
You are a word-count optimizer that redistributes section counts to hit the target length.
</role>

<input>
Outline: {outline}
TargetWords: {target_word_count}
Date: {today}
</input>

<constraints>
You MUST respond with valid JSON exactly matching the schema below.  
• Use approximate ratios Hook 15%, Context 25%, Growth 40%, Reflection 20%.  
• Each count multiple of 5; total equals TargetWords.  
• Growth count must be highest.  
• No markdown or extra keys.
</constraints>

<output_schema>
{
  "optimized_counts": {
    "hook": 100,
    "context": 150,
    "growth_moment": 260,
    "reflection": 140
  },
  "total": 650
}
</output_schema>
"""
)

__all__ = [
    "OUTLINE_GENERATOR_PROMPT",
    "STRUCTURE_VALIDATOR_PROMPT", 
    "TRANSITION_SUGGESTION_PROMPT",
    "LENGTH_OPTIMIZER_PROMPT"
] 