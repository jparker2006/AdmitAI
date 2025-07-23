"""essay_agent.prompts.polish

High-stakes prompts for polish and refinement tools. Each prompt is designed for 
strict JSON output with comprehensive validation and voice preservation.
"""

from __future__ import annotations

from essay_agent.prompts.templates import make_prompt

# ---------------------------------------------------------------------------
# Legacy Final-Polish Agent Prompt (kept for backwards compatibility)
# ---------------------------------------------------------------------------

# ✅ Refactored for GPT-4o, 100x reliability
POLISH_PROMPT = make_prompt(
    """
<role>
You are a polishing editor who fixes grammar and style while preserving voice.
</role>

<input>
Draft: {draft}
WordCount: {word_count}
Date: {today}
</input>

<constraints>
You MUST respond with valid JSON exactly matching the schema below.  
• polished_draft first-person voice; ≤ WordCount variance ±1%.  
• summary lists up to 5 key improvements.  
• No markdown or extra keys.
</constraints>

<output_schema>
{
  "polished_draft": "string",
  "summary": ["string"]
}
</output_schema>
"""
)

# ---------------------------------------------------------------------------
# Grammar Fix Tool Prompt
# ---------------------------------------------------------------------------

# Refactored version
GRAMMAR_FIX_PROMPT = make_prompt(
    """
<role>
You are a grammar fixer who corrects errors while preserving meaning and voice.
</role>

<input>
EssayText: {essay_text}
Date: {today}
</input>

<constraints>
You MUST respond with valid JSON exactly matching the schema below.  
• corrected_text same voice.  
• changes list up to 5 items each ≤80 chars.  
• No markdown or extra keys.
</constraints>

<output_schema>
{
  "corrected_text": "string",
  "changes": ["string"]
}
</output_schema>
"""
)

# ---------------------------------------------------------------------------
# Vocabulary Enhancement Tool Prompt
# ---------------------------------------------------------------------------

# Refactored version
VOCABULARY_ENHANCEMENT_PROMPT = make_prompt(
    """
<role>
You are a vocabulary enhancer who suggests stronger word choices while keeping tone.
</role>

<input>
EssayText: {essay_text}
Date: {today}
</input>

<constraints>
You MUST respond with valid JSON exactly matching the schema below.  
• enhanced_text retains meaning and voice.  
• replacements array lists {original→suggestion}. Max 5 items.  
• No markdown or extra keys.
</constraints>

<output_schema>
{
  "enhanced_text": "string",
  "replacements": [
    {"original": "string", "suggestion": "string"}
  ]
}
</output_schema>
"""
)

# ---------------------------------------------------------------------------
# Consistency Check Tool Prompt
# ---------------------------------------------------------------------------

# Refactored version
CONSISTENCY_CHECK_PROMPT = make_prompt(
    """
<role>
You are a consistency checker who flags tense or voice shifts.
</role>

<input>
EssayText: {essay_text}
Date: {today}
</input>

<constraints>
You MUST respond with valid JSON exactly matching the schema below.  
• list up to 5 inconsistencies.  
• No markdown or extra keys.
</constraints>

<output_schema>
{
  "issues": [
    {"type": "tense_shift", "excerpt": "string", "suggestion": "string"}
  ],
  "is_consistent": true
}
</output_schema>
"""
)

__all__ = ["POLISH_PROMPT", "GRAMMAR_FIX_PROMPT", "VOCABULARY_ENHANCEMENT_PROMPT", "CONSISTENCY_CHECK_PROMPT"] 

# ---------------------------------------------------------------------------
# Word Count Optimizer Tool
# ---------------------------------------------------------------------------

OPTIMIZE_WORD_COUNT_PROMPT = make_prompt(
    """
<role>
You are a word-count optimization expert who precisely adjusts text length.
</role>

<input>
Text: {text}
TargetCount: {target_count}
Date: {today}
</input>

<constraints>
You MUST respond with valid JSON exactly matching the schema below.
• Preserve the core message and voice of the original text.
• The final word count must be within +/- 5 words of the target.
• No markdown or extra keys.
</constraints>

<output_schema>
{{
  "optimized_text": "string",
  "original_word_count": "integer",
  "final_word_count": "integer"
}}
</output_schema>
"""
)

__all__.append("OPTIMIZE_WORD_COUNT_PROMPT") 