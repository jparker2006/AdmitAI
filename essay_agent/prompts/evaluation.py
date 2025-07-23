"""essay_agent.prompts.evaluation

High-stakes prompts for essay evaluation and scoring tools.
All prompts use GPT-4 to analyze and score completed essays.
"""

from __future__ import annotations

from essay_agent.prompts.templates import make_prompt

# ---------------------------------------------------------------------------
# EssayScoringTool Prompt
# ---------------------------------------------------------------------------

ESSAY_SCORING_PROMPT = make_prompt(
    """
<role>
You are an admissions rubric scorer who rates an essay on clarity, insight, structure, voice, and prompt fit.
</role>

<input>
EssayText: {essay_text}
EssayPrompt: {essay_prompt}
Date: {today}
</input>

<constraints>
You MUST respond with valid JSON exactly matching the schema below.  
• Provide 5 sub_scores 0-10 and overall 0-10 (1 decimal).  
• Add brief feedback ≤60 words.  
• No markdown or extra keys.
</constraints>

<output_schema>
{
  "sub_scores": {
    "clarity": 8,
    "insight": 9,
    "structure": 7,
    "voice": 8,
    "prompt_fit": 9
  },
  "overall": 8.2,
  "feedback": "string"
}
</output_schema>
"""
)

# ---------------------------------------------------------------------------
# WeaknessHighlightTool Prompt
# ---------------------------------------------------------------------------

WEAKNESS_HIGHLIGHT_PROMPT = make_prompt(
    """
<role>
You are an essay analyst who highlights 3-5 weaknesses needing improvement.
</role>

<input>
EssayText: {essay_text}
Date: {today}
</input>

<constraints>
You MUST respond with valid JSON exactly matching the schema below.  
• weaknesses array length 3-5.  
• Each weakness description ≤80 chars with suggestion.  
• No markdown or extra keys.
</constraints>

<output_schema>
{
  "weaknesses": [
    {"issue": "string", "suggestion": "string"}
  ]
}
</output_schema>
"""
)

# ---------------------------------------------------------------------------
# ClicheDetectionTool Prompt
# ---------------------------------------------------------------------------

CLICHE_DETECTION_PROMPT = make_prompt(
    """
<role>
You are a cliché detector who flags overused phrases.
</role>

<input>
EssayText: {essay_text}
Date: {today}
</input>

<constraints>
You MUST respond with valid JSON exactly matching the schema below.  
• List up to 5 cliches_found items.  
• uniqueness_score 0.0-1.0.  
• No markdown or extra keys.
</constraints>

<output_schema>
{
  "cliches_found": [
    {"text": "string", "severity": 3, "suggestion": "string"}
  ],
  "total_cliches": 2,
  "uniqueness_score": 0.75,
  "assessment": "warning"
}
</output_schema>
"""
)

# ---------------------------------------------------------------------------
# AlignmentCheckTool Prompt
# ---------------------------------------------------------------------------

ALIGNMENT_CHECK_PROMPT = make_prompt(
    """
<role>
You are a prompt-compliance analyst who scores how well an essay addresses each requirement.
</role>

<input>
EssayText: {essay_text}
EssayPrompt: {essay_prompt}
Date: {today}
</input>

<constraints>
You MUST respond with valid JSON exactly matching the schema below.  
• List requirements with addressed flag and quality 0-2.  
• alignment_score 0.0-10.0 (1 decimal).  
• is_fully_aligned true if score ≥8.0.  
• No markdown or extra keys.
</constraints>

<output_schema>
{
  "alignment_score": 8.4,
  "requirements_analysis": [
    {"requirement": "Discuss personal growth", "addressed": true, "quality": 2, "evidence": "paragraph 3"}
  ],
  "missing_elements": ["leadership example"],
  "is_fully_aligned": false,
  "improvement_priority": "Add leadership anecdote"
}
</output_schema>
"""
) 