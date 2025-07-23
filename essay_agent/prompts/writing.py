from __future__ import annotations

from essay_agent.prompts.templates import make_prompt

# ---------------------------------------------------------------------------
# Writing & Drafting Prompt Templates (Section 3.4) --------------------------
# ---------------------------------------------------------------------------

OUTLINE_EXPANSION_PROMPT = make_prompt(
    """
<role>
You are a writing assistant who expands outline sections with detailed content.
</role>

<input>
OutlineSection: {outline_section}
SectionName: {section_name}
VoiceProfile: {voice_profile}
TargetWords: {target_words}
Date: {today}
</input>

<constraints>
You MUST respond with valid JSON exactly matching the schema below.
• expanded_paragraph is a string with the new content.
• word_count should be respected.
• No markdown or extra keys.
</constraints>

<output_schema>
{{
  "expanded_paragraph": "string"
}}
</output_schema>
"""
)

# ---------------------------------------------------------------------------

PARAGRAPH_REWRITE_PROMPT = make_prompt(
    """
<role>
You are a revision specialist who rewrites paragraphs to meet stylistic goals.
</role>

<input>
Paragraph: {paragraph}
StyleInstruction: {style_instruction}
VoiceProfile: {voice_profile}
Date: {today}
</input>

<constraints>
You MUST respond with valid JSON exactly matching the schema below.
• Preserve the core message and all factual details.
• The rewritten paragraph must match the voice profile.
• No markdown or extra keys.
</constraints>

<output_schema>
{{
  "rewritten_paragraph": "string"
}}
</output_schema>
"""
)

# ---------------------------------------------------------------------------

OPENING_IMPROVEMENT_PROMPT = make_prompt(
    """
<role>
You are an essay hook specialist who creates magnetic opening sentences.
</role>

<input>
OpeningSentence: {opening_sentence}
EssayContext: {essay_context}
VoiceProfile: {voice_profile}
Date: {today}
</input>

<constraints>
You MUST respond with valid JSON exactly matching the schema below.
• The improved opening must be a single, compelling sentence.
• It must align with the essay's context and the user's voice.
• No markdown or extra keys.
</constraints>

<output_schema>
{{
  "improved_opening": "string"
}}
</output_schema>
"""
)

# ---------------------------------------------------------------------------

VOICE_STRENGTHENING_PROMPT = make_prompt(
    """
<role>
You are a voice-tuning expert who adjusts text to match a user's authentic style.
</role>

<input>
Paragraph: {paragraph}
VoiceProfile: {voice_profile}
TargetVoiceTraits: {target_voice_traits}
Date: {today}
</input>

<constraints>
You MUST respond with valid JSON exactly matching the schema below.
• Preserve the paragraph's core message.
• The output must align with the specified voice traits.
• No markdown or extra keys.
</constraints>

<output_schema>
{{
  "voice_adjusted_paragraph": "string"
}}
</output_schema>
"""
) 