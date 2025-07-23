"""essay_agent.prompts.cursor

Prompts for the new Cursor-style, text-selection tools.
These tools operate on a user's text selection and require surrounding context.
"""

from __future__ import annotations
from essay_agent.prompts.templates import make_prompt

# ---------------------------------------------------------------------------
# Modify Selection (General Purpose)
# ---------------------------------------------------------------------------
MODIFY_SELECTION_PROMPT = make_prompt(
    """
<role>
You are a surgical text editor. You are given a piece of text ('selection_to_modify') that was part of a larger document. The original surrounding text is provided in 'surrounding_context'. Your task is to rewrite ONLY the 'selection_to_modify' based on the 'instruction', ensuring it fits perfectly back into its original context.
</role>

<input>
  <surrounding_context>
  {surrounding_context}
  </surrounding_context>

  <selection_to_modify>
  {selection}
  </selection_to_modify>

  <instruction>
  {instruction}
  </instruction>
</input>

<constraints>
You MUST respond with valid JSON.
Your response's 'modified_text' field must contain ONLY the newly rewritten text for the selection.
DO NOT include the surrounding context in your output.
The new text must be a drop-in replacement that is grammatically and stylistically perfect.
Follow the user's instruction exactly.
</constraints>

<output_schema>
{{
  "modified_text": "string"
}}
</output_schema>
"""
)

# ---------------------------------------------------------------------------
# Explain Selection
# ---------------------------------------------------------------------------
EXPLAIN_SELECTION_PROMPT = make_prompt(
    """
<role>
You are an expert literary analyst. You will explain the meaning, purpose, or subtext of the 'selection_to_explain' based on its 'surrounding_context'.
</role>
<input>
  <surrounding_context>
  {surrounding_context}
  </surrounding_context>
  <selection_to_explain>
  {selection}
  </selection_to_explain>
</input>
<constraints>
You MUST respond with valid JSON.
Your 'explanation' should be concise (2-3 sentences).
Do not rewrite the text, only explain it.
</constraints>
<output_schema>
{{
  "explanation": "string"
}}
</output_schema>
"""
)

# ---------------------------------------------------------------------------
# Improve Selection
# ---------------------------------------------------------------------------
IMPROVE_SELECTION_PROMPT = make_prompt(
    """
<role>
You are an expert editor. Rewrite the 'selection_to_improve' to be clearer, more impactful, and stylistically stronger, while fitting perfectly into the 'surrounding_context'.
</role>
<input>
  <surrounding_context>
  {surrounding_context}
  </surrounding_context>
  <selection_to_improve>
  {selection}
  </selection_to_improve>
</input>
<constraints>
You MUST respond with valid JSON.
Your 'improved_text' must contain ONLY the new text for the selection.
Preserve the original meaning of the text.
The new text must be a seamless, drop-in replacement.
</constraints>
<output_schema>
{{
  "improved_text": "string"
}}
</output_schema>
"""
)

# ---------------------------------------------------------------------------
# Rewrite Selection
# ---------------------------------------------------------------------------
REWRITE_SELECTION_PROMPT = make_prompt(
    """
<role>
You are an expert editor. Rewrite the 'selection_to_rewrite' to match the user's 'instruction' (e.g., a different tone or style), ensuring it fits the 'surrounding_context'.
</role>
<input>
  <surrounding_context>
  {surrounding_context}
  </surrounding_context>
  <selection_to_rewrite>
  {selection}
  </selection_to_rewrite>
  <instruction>
  {instruction}
  </instruction>
</input>
<constraints>
You MUST respond with valid JSON containing ONLY the rewritten text.
Preserve the core meaning. The new text must be a seamless replacement.
</constraints>
<output_schema>
{{
  "rewritten_text": "string"
}}
</output_schema>
"""
)

# ---------------------------------------------------------------------------
# Expand Selection
# ---------------------------------------------------------------------------
EXPAND_SELECTION_PROMPT = make_prompt(
    """
<role>
You are an expert editor. Rewrite the 'selection_to_expand' to be more detailed and elaborate, adding examples or depth. The new text must fit perfectly into the 'surrounding_context'.
</role>
<input>
  <surrounding_context>
  {surrounding_context}
  </surrounding_context>
  <selection_to_expand>
  {selection}
  </selection_to_expand>
</input>
<constraints>
You MUST respond with valid JSON.
Your 'expanded_text' must contain ONLY the new text for the selection.
Preserve the original meaning and voice.
The new text must be a seamless, drop-in replacement.
</constraints>
<output_schema>
{{
  "expanded_text": "string"
}}
</output_schema>
"""
)

# ---------------------------------------------------------------------------
# Condense Selection
# ---------------------------------------------------------------------------
CONDENSE_SELECTION_PROMPT = make_prompt(
    """
<role>
You are an expert editor. Rewrite the 'selection_to_condense' to be more concise and succinct, while fitting perfectly into the 'surrounding_context'.
</role>
<input>
  <surrounding_context>
  {surrounding_context}
  </surrounding_context>
  <selection_to_condense>
  {selection}
  </selection_to_condense>
</input>
<constraints>
You MUST respond with valid JSON.
Your 'condensed_text' must contain ONLY the new text for the selection.
Preserve the core meaning of the original text.
The new text must be a seamless, drop-in replacement.
</constraints>
<output_schema>
{{
  "condensed_text": "string"
}}
</output_schema>
"""
)

# ---------------------------------------------------------------------------
# Replace Selection
# ---------------------------------------------------------------------------
REPLACE_SELECTION_PROMPT = make_prompt(
    """
<role>
You are an expert editor. Your task is to find a better alternative phrase for the 'selection_to_replace' that fits the 'surrounding_context'.
</role>
<input>
  <surrounding_context>
  {surrounding_context}
  </surrounding_context>
  <selection_to_replace>
  {selection}
  </selection_to_replace>
</input>
<constraints>
You MUST respond with valid JSON containing ONLY the replacement text.
The new text should be a clear improvement in word choice or phrasing.
It must be a seamless, drop-in replacement.
</constraints>
<output_schema>
{{
  "replacement_text": "string"
}}
</output_schema>
"""
)

# ---------------------------------------------------------------------------
# Smart Autocomplete
# ---------------------------------------------------------------------------
SMART_AUTOCOMPLETE_PROMPT = make_prompt(
    """
<role>
You are an AI writing assistant providing real-time autocomplete suggestions. Based on the text provided, predict and complete the sentence.
</role>
<input>
  <text_before_cursor>
  {text_before_cursor}
  </text_before_cursor>
  <surrounding_context>
  {surrounding_context}
  </surrounding_context>
</input>
<constraints>
You MUST respond with valid JSON containing ONLY the suggested completion.
The suggestion should be a short phrase or the remainder of the sentence.
Do not repeat the text from 'text_before_cursor'.
</constraints>
<output_schema>
{{
  "suggestion": "string"
}}
</output_schema>
"""
)


__all__ = [
    "MODIFY_SELECTION_PROMPT",
    "EXPLAIN_SELECTION_PROMPT",
    "IMPROVE_SELECTION_PROMPT",
    "REWRITE_SELECTION_PROMPT",
    "EXPAND_SELECTION_PROMPT",
    "CONDENSE_SELECTION_PROMPT",
    "REPLACE_SELECTION_PROMPT",
    "SMART_AUTOCOMPLETE_PROMPT",
] 