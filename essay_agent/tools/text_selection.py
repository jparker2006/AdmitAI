"""essay_agent.tools.text_selection

Cursor-style text selection / real-time intelligence tools introduced in
Section 3.2.  These lightweight implementations use deterministic string
transformations so tests pass without real LLM calls.  In production the
`_run` bodies can be replaced with LLM prompts (see TODO comments).
"""
from __future__ import annotations
from typing import Any, Dict, List
from pydantic import BaseModel, Field

from essay_agent.prompts.templates import render_template
from essay_agent.response_parser import pydantic_parser, safe_parse
from essay_agent.llm_client import get_chat_llm, call_llm
from essay_agent.tools.base import ValidatedTool
from essay_agent.tools import register_tool

from essay_agent.prompts.cursor import (
    MODIFY_SELECTION_PROMPT,
    EXPLAIN_SELECTION_PROMPT,
    IMPROVE_SELECTION_PROMPT,
    REWRITE_SELECTION_PROMPT,
    EXPAND_SELECTION_PROMPT,
    CONDENSE_SELECTION_PROMPT,
    REPLACE_SELECTION_PROMPT,
    SMART_AUTOCOMPLETE_PROMPT,
)

# Pydantic Models for each tool's output
class ModifySelectionResult(BaseModel):
    modified_text: str = Field(..., description="The modified text.")

class ExplainSelectionResult(BaseModel):
    explanation: str = Field(..., description="The explanation of the selected text.")

class ImproveSelectionResult(BaseModel):
    improved_text: str = Field(..., description="The improved text.")

class RewriteSelectionResult(BaseModel):
    rewritten_text: str = Field(..., description="The rewritten text.")

class ExpandSelectionResult(BaseModel):
    expanded_text: str = Field(..., description="The expanded text.")

class CondenseSelectionResult(BaseModel):
    condensed_text: str = Field(..., description="The condensed text.")

class ReplaceSelectionResult(BaseModel):
    replacement_text: str = Field(..., description="The replacement text.")

class SmartAutocompleteResult(BaseModel):
    suggestion: str = Field(..., description="The autocomplete suggestion.")


def _run_cursor_tool(prompt, pydantic_model, **kwargs):
    rendered_prompt = render_template(prompt, **kwargs)
    llm = get_chat_llm(temperature=0.3)
    raw = call_llm(llm, rendered_prompt)
    parser = pydantic_parser(pydantic_model)
    parsed = safe_parse(parser, raw)
    return parsed.model_dump()

@register_tool("modify_selection")
class ModifySelectionTool(ValidatedTool):
    """Modify the selected text based on a user instruction.

    This is a powerful, general-purpose tool that applies a user-provided
    instruction to a selected piece of text, ensuring the result fits
    seamlessly back into the surrounding context.

    Args:
        selection (str): The text highlighted by the user.
        instruction (str): The user's command (e.g., "make this funnier").
        surrounding_context (str): The text immediately before and after the selection.
    """
    name: str = "modify_selection"
    description: str = "Modify the selected text based on a user instruction."
    
    def _run(self, *, selection: str, instruction: str, surrounding_context: str, **_: Any) -> Dict[str, Any]:
        return _run_cursor_tool(
            MODIFY_SELECTION_PROMPT,
            ModifySelectionResult,
            selection=selection,
            instruction=instruction,
            surrounding_context=surrounding_context
        )

@register_tool("explain_selection")
class ExplainSelectionTool(ValidatedTool):
    """Explain the meaning, purpose, or subtext of the selected text."""
    name: str = "explain_selection"
    description: str = "Explain the selected text."
    
    def _run(self, *, selection: str, surrounding_context: str, **_: Any) -> Dict[str, Any]:
        return _run_cursor_tool(
            EXPLAIN_SELECTION_PROMPT,
            ExplainSelectionResult,
            selection=selection,
            surrounding_context=surrounding_context
        )

@register_tool("improve_selection")
class ImproveSelectionTool(ValidatedTool):
    """Improve the selected text for clarity, impact, and style."""
    name: str = "improve_selection"
    description: str = "Improve the selected text for clarity and impact."

    def _run(self, *, selection: str, surrounding_context: str, **_: Any) -> Dict[str, Any]:
        return _run_cursor_tool(
            IMPROVE_SELECTION_PROMPT,
            ImproveSelectionResult,
            selection=selection,
            surrounding_context=surrounding_context
        )

@register_tool("rewrite_selection")
class RewriteSelectionTool(ValidatedTool):
    """Rewrite the selected text to match a new style, tone, or instruction."""
    name: str = "rewrite_selection"
    description: str = "Rewrite the selected text with a different style or tone."

    def _run(self, *, selection: str, instruction: str, surrounding_context: str, **_: Any) -> Dict[str, Any]:
        return _run_cursor_tool(
            REWRITE_SELECTION_PROMPT,
            RewriteSelectionResult,
            selection=selection,
            instruction=instruction,
            surrounding_context=surrounding_context
        )

@register_tool("expand_selection")
class ExpandSelectionTool(ValidatedTool):
    """Expand the selected text to be more detailed or elaborate."""
    name: str = "expand_selection"
    description: str = "Expand the selected text to be more detailed."

    def _run(self, *, selection: str, surrounding_context: str, **_: Any) -> Dict[str, Any]:
        return _run_cursor_tool(
            EXPAND_SELECTION_PROMPT,
            ExpandSelectionResult,
            selection=selection,
            surrounding_context=surrounding_context
        )

@register_tool("condense_selection")
class CondenseSelectionTool(ValidatedTool):
    """Condense the selected text to be more concise and succinct."""
    name: str = "condense_selection"
    description: str = "Condense the selected text to be more concise."

    def _run(self, *, selection: str, surrounding_context: str, **_: Any) -> Dict[str, Any]:
        return _run_cursor_tool(
            CONDENSE_SELECTION_PROMPT,
            CondenseSelectionResult,
            selection=selection,
            surrounding_context=surrounding_context
        )

@register_tool("replace_selection")
class ReplaceSelectionTool(ValidatedTool):
    """Replace the selected text with a better alternative phrasing."""
    name: str = "replace_selection"
    description: str = "Replace the selected text with a better alternative."

    def _run(self, *, selection: str, surrounding_context: str, **_: Any) -> Dict[str, Any]:
        return _run_cursor_tool(
            REPLACE_SELECTION_PROMPT,
            ReplaceSelectionResult,
            selection=selection,
            surrounding_context=surrounding_context
        )

@register_tool("smart_autocomplete")
class SmartAutocompleteTool(ValidatedTool):
    """Provide real-time autocomplete suggestions as the user types."""
    name: str = "smart_autocomplete"
    description: str = "Provide real-time autocomplete suggestions."

    def _run(self, *, text_before_cursor: str, surrounding_context: str, **_: Any) -> Dict[str, Any]:
        return _run_cursor_tool(
            SMART_AUTOCOMPLETE_PROMPT,
            SmartAutocompleteResult,
            text_before_cursor=text_before_cursor,
            surrounding_context=surrounding_context
        ) 