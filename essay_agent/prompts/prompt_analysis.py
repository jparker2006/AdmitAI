"""essay_agent.prompts.prompt_analysis

High-stakes production prompts for essay prompt analysis tools.
Each prompt is designed for strict JSON output with comprehensive validation.
"""

from __future__ import annotations

from essay_agent.prompts.templates import make_prompt

# ---------------------------------------------------------------------------
# Prompt Classification Tool
# ---------------------------------------------------------------------------

CLASSIFY_PROMPT_PROMPT = make_prompt(
    """
<role>
You are an expert college-essay prompt-classification specialist.
</role>

<input>
EssayPrompt: {essay_prompt}
Date: {today}
</input>

<constraints>
You MUST respond with valid JSON exactly matching the schema below.  
• theme must be one of [adversity, growth, identity, leadership, creativity, service, challenge, career, curiosity, other].  
• confidence float 0.0-1.0 rounded to 1 decimal.  
• rationale 15-25 words citing textual evidence.  
• No markdown, no extra keys.
</constraints>

<output_schema>
{
  "theme": "string",
  "confidence": 0.8,
  "rationale": "string"
}
</output_schema>
"""
)

# ---------------------------------------------------------------------------
# Requirements Extraction Tool
# ---------------------------------------------------------------------------

EXTRACT_REQUIREMENTS_PROMPT = make_prompt(
    """
<role>
You are a requirements-extraction specialist who parses essay prompts for constraints.
</role>

<input>
EssayPrompt: {essay_prompt}
Date: {today}
</input>

<constraints>
You MUST respond with valid JSON exactly matching the schema below.
• word_limit is an integer or null.
• key_questions are specific, actionable questions.
• evaluation_criteria are noun phrases.
• No markdown or extra keys.
</constraints>

<output_schema>
{{
  "word_limit": 650,
  "key_questions": ["string", "..."],
  "evaluation_criteria": ["string", "..."]
}}
</output_schema>
"""
)

# ---------------------------------------------------------------------------
# Strategy Suggestion Tool
# ---------------------------------------------------------------------------

SUGGEST_STRATEGY_PROMPT = make_prompt(
    """
<role>
You are a master essay strategy consultant who provides winning approaches.
</role>

<input>
EssayPrompt: {essay_prompt}
Profile: {profile}
Date: {today}
</input>

<constraints>
You MUST respond with valid JSON exactly matching the schema below.
• overall_strategy is a 100-120 word actionable plan.
• recommended_story_traits: 3-5 specific items from the profile.
• potential_pitfalls: 3-6 concrete warnings to avoid.
• No markdown or extra keys.
</constraints>

<output_schema>
{{
  "overall_strategy": "string",
  "recommended_story_traits": ["string", "..."],
  "potential_pitfalls": ["string", "..."]
}}
</output_schema>
"""
)

# ---------------------------------------------------------------------------
# Overlap Detection Tool
# ---------------------------------------------------------------------------

DETECT_OVERLAP_PROMPT = make_prompt(
    """
<role>
You are an overlap-detection analyst ensuring essay uniqueness *for a single college application*.
</role>

<input>
College: {college_name}
CandidateStory: {story}
PreviousEssaysForThisCollege: {previous_essays}
Date: {today}
</input>

<constraints>
You MUST respond with valid JSON exactly matching the schema below.
• Check for overlap ONLY against essays for the specified college. Reusing content for different colleges is acceptable.
• overlap_score is a float 0.0-1.0 (1 decimal).
• conflicting_essays contains 0-based indices of problem essays.
• No markdown or extra keys.
</constraints>

<output_schema>
{{
  "overlaps_found": false,
  "overlap_score": 0.2,
  "conflicting_essays": []
}}
</output_schema>
"""
)

__all__ = [
    "CLASSIFY_PROMPT_PROMPT",
    "EXTRACT_REQUIREMENTS_PROMPT", 
    "SUGGEST_STRATEGY_PROMPT",
    "DETECT_OVERLAP_PROMPT"
] 