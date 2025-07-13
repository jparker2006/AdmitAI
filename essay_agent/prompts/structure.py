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
    """SYSTEM: Expert College Essay Structure Architect. Generate precise, admissions-optimized outlines.

TASK: Create 4-section outline for {word_count}-word college essay.

INPUTS:
- Essay prompt: {essay_prompt}
- Story concept: {story}
- Target words: {word_count}

REASONING CHAIN:
1. EXTRACT CORE: What specific challenge/growth does this story demonstrate?
2. MATCH PROMPT: How does this story directly answer the essay prompt?
3. STRUCTURE ARC: Hook → Context → Growth → Reflection (15%/25%/40%/20%)
4. CALCULATE WORDS: Apply percentages, round to nearest 5, ensure exact total
5. VALIDATE FLOW: Each section must logically lead to the next

CONSTRAINTS:
- Hook: ≤25 words, creates intrigue, no rhetorical questions
- Context: Sets stakes, establishes 5 W's, leads to growth moment
- Growth: Vivid scene, specific actions, sensory details, character development
- Reflection: ≤40 words, future-focused insight, no clichés

FORBIDDEN:
- Clichés: "comfort zone", "made me who I am", "opened my eyes"
- Vague language: "learned a lot", "challenging experience"
- Generic content that could apply to anyone
- Rhetorical questions in hook
- Past-tense reflection only

OUTPUT SCHEMA (JSON ONLY):
{{
  "outline": {{
    "hook": "Compelling 1-2 sentence opener (≤25 words)",
    "context": "Background and stakes setup",
    "growth_moment": "Vivid scene with specific actions and development",
    "reflection": "Future-focused insight (≤40 words)"
  }},
  "section_word_counts": {{
    "hook": <int: exactly 15% of {word_count}, rounded to nearest 5>,
    "context": <int: exactly 25% of {word_count}, rounded to nearest 5>,
    "growth_moment": <int: exactly 40% of {word_count}, rounded to nearest 5>,
    "reflection": <int: exactly 20% of {word_count}, rounded to nearest 5>
  }},
  "estimated_word_count": <int: must equal {word_count} exactly>
}}

VALIDATION CHECKLIST:
□ Story directly answers: {essay_prompt}
□ Word counts sum to {word_count} exactly
□ Hook ≤25 words, Reflection ≤40 words
□ No clichéd language
□ First-person voice throughout
□ Logical flow between sections
□ JSON validates against schema

EXECUTE: Think through reasoning chain, then output ONLY valid JSON.

Today's date: {today}"""
)

# ---------------------------------------------------------------------------
# StructureValidatorTool Prompt
# ---------------------------------------------------------------------------

STRUCTURE_VALIDATOR_PROMPT = make_prompt(
    """SYSTEM: Essay Structure Quality Assurance Inspector. Systematic evaluation of outline quality.

TASK: Evaluate outline structure using 4-dimensional rubric.

INPUT OUTLINE: {outline}

EVALUATION METHODOLOGY:
1. FLOW ANALYSIS: Score logical progression and transitions (0-10)
2. ARC ASSESSMENT: Score emotional build and resolution (0-10)
3. PROMPT ALIGNMENT: Score direct response to requirements (0-10)
4. ORIGINALITY CHECK: Score uniqueness and cliché avoidance (0-10)

SCORING CRITERIA:
FLOW COHERENCE (0-10):
- 9-10: Seamless logical progression, smooth transitions
- 7-8: Clear flow with minor gaps
- 5-6: Adequate progression with some jumps
- 3-4: Unclear connections, awkward transitions
- 0-2: Disjointed, illogical sequence

EMOTIONAL PROGRESSION (0-10):
- 9-10: Compelling arc with tension, climax, resolution
- 7-8: Clear emotional journey with good pacing
- 5-6: Adequate emotional development
- 3-4: Weak emotional connection
- 0-2: No emotional arc or engagement

PROMPT ALIGNMENT (0-10):
- 9-10: Directly addresses all prompt requirements
- 7-8: Clearly responds to main prompt elements
- 5-6: Adequately addresses prompt
- 3-4: Partially addresses prompt
- 0-2: Misses prompt requirements

ORIGINALITY (0-10):
- 9-10: Fresh approach, avoids all clichés
- 7-8: Mostly original with minor generic elements
- 5-6: Some originality with common tropes
- 3-4: Mostly generic with clichéd language
- 0-2: Heavily clichéd and generic

ISSUE DETECTION:
Flag specific problems:
- Logical gaps between sections
- Weak emotional development
- Clichéd language or themes
- Insufficient prompt alignment
- Generic or vague content

OUTPUT SCHEMA (JSON ONLY):
{{
  "is_valid": <bool: true if overall_score >= 7.0>,
  "score": <float: average of 4 rubric scores, 1 decimal place>,
  "issues": ["Specific, actionable problem statement", "Another specific issue"],
  "overall_feedback": "Single paragraph (≤120 words) with concrete improvement steps"
}}

VALIDATION CHECKLIST:
□ All 4 dimensions scored 0-10
□ Score is accurate average (1 decimal)
□ is_valid reflects score ≥ 7.0
□ Issues are specific and actionable
□ Feedback ≤120 words
□ JSON validates against schema

EXECUTE: Score systematically, then output ONLY valid JSON.

Today's date: {today}"""
)

# ---------------------------------------------------------------------------
# TransitionSuggestionTool Prompt
# ---------------------------------------------------------------------------

TRANSITION_SUGGESTION_PROMPT = make_prompt(
    """SYSTEM: Narrative Transition Specialist. Create seamless paragraph bridges.

TASK: Generate 3 transition sentences connecting outline sections.

INPUT OUTLINE: {outline}

TRANSITION ALGORITHM:
1. ANALYZE ENDPOINTS: Identify last concept of section A, first concept of section B
2. FIND BRIDGE: Create logical connection between endpoints
3. MAINTAIN VOICE: Keep first-person, conversational tone
4. ENSURE FLOW: Each transition advances narrative momentum

TRANSITION REQUIREMENTS:
HOOK → CONTEXT:
- Bridge from opening intrigue to background setup
- Maintain engagement while providing context
- Set up stakes and importance

CONTEXT → GROWTH:
- Move from background to central challenge
- Build tension and anticipation
- Signal shift to main narrative

GROWTH → REFLECTION:
- Connect action/challenge to lessons learned
- Show shift from experience to insight
- Prepare for conclusion

CONSTRAINTS:
- Each transition ≤25 words
- First-person voice throughout
- Natural, conversational tone
- Advances narrative forward
- Connects specific content from adjacent sections

FORBIDDEN:
- Rhetorical questions
- Clichéd phrases: "Little did I know", "Looking back"
- Overly formal/academic language
- Generic connectors that could work anywhere
- Abrupt topic changes

OUTPUT SCHEMA (JSON ONLY):
{{
  "transitions": {{
    "hook_to_context": "Natural transition sentence (≤25 words)",
    "context_to_growth": "Momentum-building transition sentence (≤25 words)",
    "growth_to_reflection": "Insight-connecting transition sentence (≤25 words)"
  }}
}}

VALIDATION CHECKLIST:
□ 3 transitions provided
□ Each transition ≤25 words
□ First-person voice maintained
□ Natural, specific language
□ No rhetorical questions
□ JSON validates against schema

EXECUTE: Analyze endpoints, create bridges, output ONLY valid JSON.

Today's date: {today}"""
)

# ---------------------------------------------------------------------------
# LengthOptimizerTool Prompt
# ---------------------------------------------------------------------------

LENGTH_OPTIMIZER_PROMPT = make_prompt(
    """SYSTEM: Word Count Optimization Engine. Precise mathematical word distribution.

TASK: Redistribute words to hit exactly {target_word_count} words using optimal ratios.

INPUTS:
- Current outline: {outline}
- Target count: {target_word_count}

OPTIMIZATION ALGORITHM:
1. CALCULATE TARGETS: Apply proven percentages (15%/25%/40%/20%)
2. ROUND TO NEAREST 5: Clean word targets for each section
3. ENSURE EXACT TOTAL: Adjust largest section (growth_moment) if needed
4. VALIDATE CONSTRAINTS: Check minimum/maximum limits

PROVEN RATIOS:
- Hook: 15% of total (engaging opener)
- Context: 25% of total (adequate setup)
- Growth: 40% of total (essay heart)
- Reflection: 20% of total (meaningful closure)

MATHEMATICAL CONSTRAINTS:
- Hook: 50-150 words (minimum engagement, maximum brevity)
- Context: 100-300 words (adequate setup, not excessive)
- Growth: 200-500 words (substantial development, not overwhelming)
- Reflection: 75-200 words (meaningful insight, concise conclusion)

ROUNDING RULES:
1. Calculate: {target_word_count} × percentage
2. Round to nearest 5-word increment
3. Sum all sections
4. If sum ≠ {target_word_count}, adjust growth_moment
5. Validate all constraints

OUTPUT SCHEMA (JSON ONLY):
{{
  "optimized_counts": {{
    "hook": <int: ~15% of target, rounded to nearest 5>,
    "context": <int: ~25% of target, rounded to nearest 5>,
    "growth_moment": <int: ~40% of target, rounded to nearest 5>,
    "reflection": <int: ~20% of target, rounded to nearest 5>
  }},
  "total": <int: must equal {target_word_count} exactly>
}}

VALIDATION CHECKLIST:
□ All 4 sections have word counts
□ Each count is multiple of 5
□ Total equals {target_word_count} exactly
□ Growth moment has highest count
□ All counts within constraint limits
□ JSON validates against schema

EXECUTE: Calculate mathematically, validate constraints, output ONLY valid JSON.

Today's date: {today}"""
)

__all__ = [
    "OUTLINE_GENERATOR_PROMPT",
    "STRUCTURE_VALIDATOR_PROMPT", 
    "TRANSITION_SUGGESTION_PROMPT",
    "LENGTH_OPTIMIZER_PROMPT"
] 