"""essay_agent.prompts.brainstorming

High-stakes production prompts for brainstorming and story development tools.
Each prompt is designed for strict JSON output with comprehensive validation.
"""

from __future__ import annotations

from essay_agent.prompts.templates import make_prompt, ensure_example, literal
from essay_agent.prompts.example_registry import EXAMPLE_REGISTRY

# ensure subsequent prompt modules can safely append
__all__: list[str] = []

# ---------------------------------------------------------------------------
# Story Suggestion Tool
# ---------------------------------------------------------------------------

_SCHEMA_SUGGEST = literal(
    """
{
  "stories": [
    {
      "title": "string (4-8 words)",
      "description": "string (≤40 words)",
      "relevance_score": 0.85,
      "themes": ["string", "string"],
      "prompt_fit_explanation": "string (1 sentence)",
      "unique_elements": ["string"]
    }
  ],
  "analysis_notes": "string (brief rationale)"
}
"""
)

_RAW_SUGGESTION = (
    """
<role>
You are a college-essay story strategist who extracts five compelling, authentic story ideas from a student profile.
</role>

<input>
EssayPrompt: {essay_prompt}
Profile: {profile}
</input>

<constraints>
You MUST respond with valid JSON that exactly matches the schema below.  
• Provide exactly 5 story objects ordered by relevance (highest first).  
• Use 4-8 word titles; descriptions are ≤40 words.  
• Do not include markdown or extra keys.
IMPORTANT: Reply must use EXACTLY these key names – "title", "description", "relevance_score", "themes", "prompt_fit_explanation", "unique_elements" – and no others.
</constraints>

<output_schema>
""" + _SCHEMA_SUGGEST + """
</output_schema>
"""
)

STORY_SUGGESTION_PROMPT = ensure_example(
    make_prompt(_RAW_SUGGESTION),
    "suggest_stories",
)

# ---------------------------------------------------------------------------
# Specific Brainstorm Tool (topic-focused)
# ---------------------------------------------------------------------------

SPECIFIC_BRAINSTORM_PROMPT = ensure_example(
    make_prompt(
    """
<role>
You are an expert idea generator who crafts specific, unique brainstorming ideas for college essays.
</role>

<input>
Topic: {topic}
UserInput: {user_input}
Date: {today}
</input>

<constraints>
You MUST respond with valid JSON that exactly matches the schema below.  
• Provide 3-5 concise idea strings directly related to Topic/UserInput.  
• No additional keys, markdown, or commentary.
</constraints>

<output_schema>
{
  "ideas": ["string", "string"],
  "next_steps": "string (how to use the ideas)"
}
</output_schema>
"""
    ),
    "brainstorm_specific",
)

__all__.append("SPECIFIC_BRAINSTORM_PROMPT")

# ---------------------------------------------------------------------------
# Story Matching Tool
# ---------------------------------------------------------------------------

STORY_MATCHING_PROMPT = ensure_example(
    make_prompt(
    """
<role>
You are a college-essay evaluation specialist who scores how well a story fits a given prompt.
</role>

<input>
Story: {story}
EssayPrompt: {essay_prompt}
Date: {today}
</input>

<constraints>
You MUST respond with valid JSON that exactly matches the schema below.  
• Provide numeric scores with 0.1 precision.  
• Include at least 2 strengths and 2 weaknesses.  
• No markdown or additional keys.
</constraints>

<output_schema>
{
  "match_score": 8.5,
  "rationale": "string (≤100 words explaining the score)",
  "strengths": ["string", "string"],
  "weaknesses": ["string", "string"],
  "improvement_suggestions": ["string", "string"],
  "optimization_priority": "string (top area to improve)"
}
</output_schema>
"""
    ),
    "match_story",
)

# ---------------------------------------------------------------------------
# Story Expansion Tool
# ---------------------------------------------------------------------------

STORY_EXPANSION_PROMPT = ensure_example(
    make_prompt(
    """
<role>
You are a story-development consultant who generates questions and focus areas to expand a story seed.
</role>

<input>
StorySeed: {story_seed}
Date: {today}
</input>

<constraints>
You MUST respond with valid JSON exactly matching the schema below.  
• Provide 5-8 development questions.  
• Include 2-4 focus areas and 2-5 missing details.  
• No markdown or extra keys.
</constraints>

<output_schema>
{
  "expansion_questions": ["string", "string"],
  "focus_areas": ["string", "string"],
  "missing_details": ["string", "string"],
  "development_priority": "string (highest priority area)"
}
</output_schema>
"""
    ),
    "expand_story",
)

# ---------------------------------------------------------------------------
# Uniqueness Validation Tool
# ---------------------------------------------------------------------------

UNIQUENESS_VALIDATION_PROMPT = ensure_example(
    make_prompt(
    """
<role>
You are an essay originality analyst who scores a story angle for uniqueness and flags clichés.
</role>

<input>
StoryAngle: {story_angle}
PreviousEssays: {previous_essays}
Date: {today}
</input>

<constraints>
You MUST respond with valid JSON that matches the schema below.  
• Provide a uniqueness_score 0.00-1.00 (two decimals).  
• Include up to 5 cliché risks and differentiation suggestions.  
• No markdown or extra keys.
</constraints>

<output_schema>
{
  "uniqueness_score": 0.87,
  "is_unique": true,
  "cliche_risks": ["string"],
  "differentiation_suggestions": ["string"],
  "unique_elements": ["string"],
  "risk_mitigation": ["string"],
  "recommendation": "string (concise guidance)"
}
</output_schema>
"""
    ),
    "validate_uniqueness",
) 

# ---------------------------------------------------------------------------
# Story Development Tool
# ---------------------------------------------------------------------------

STORY_DEVELOPMENT_PROMPT = make_prompt(
    """
<role>
You are a narrative coach who enriches a student's story with vivid detail and reflection.
</role>

<input>
Story: {story}
Date: {today}
</input>

<constraints>
You MUST respond with valid JSON exactly matching the schema below.  
• Provide 5 development_questions that elicit detail and emotion.  
• Return 3-5 themes that fit the story.  
• No markdown or extra keys.
</constraints>

<output_schema>
{
  "developed_story": "string (1-2 sentence augmented version of the story)",
  "development_questions": ["string", "string"],
  "themes": ["string", "string"],
  "next_steps": "string (concise guidance)"
}
</output_schema>
"""
)

__all__.append("STORY_DEVELOPMENT_PROMPT") 

# ---------------------------------------------------------------------------
# Story Themes Tool
# ---------------------------------------------------------------------------

STORY_THEMES_PROMPT = make_prompt(
    """
<role>
You are a theme analyst who extracts key themes and messages from a student's story.
</role>

<input>
Story: {story}
Date: {today}
</input>

<constraints>
You MUST respond with valid JSON exactly matching the schema below.  
• Provide 3-5 identified_themes.  
• core_message ≤ 20 words, essay_potential one word (High|Medium|Low).  
• No markdown or extra keys.
</constraints>

<output_schema>
{
  "story_analysis": "string (short analysis line)",
  "identified_themes": ["string", "string"],
  "core_message": "string",
  "essay_potential": "High",
  "suggestions": "string (concise advice)"
}
</output_schema>
"""
)

__all__.append("STORY_THEMES_PROMPT") 