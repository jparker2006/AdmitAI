"""essay_agent.response_parser

LangChain response parsing with improved error handling.
"""

from __future__ import annotations

import json
import re
from typing import Any, Type

from langchain.output_parsers import OutputFixingParser
from langchain_core.output_parsers import BaseOutputParser
from pydantic import BaseModel

from essay_agent.llm_client import get_chat_llm


class ParseError(Exception):
    """Raised when response parsing fails."""


def safe_parse(parser: BaseOutputParser, text: str, retries: int = 3) -> Any:
    """Parse LLM response with automatic error fixing.

    This function attempts to parse the LLM response using the provided parser.
    If parsing fails, it will attempt to auto-fix the response using LangChain's
    OutputFixingParser (if available) and retry parsing.

    Args:
        parser: LangChain output parser to use.
        text: Raw LLM response string.
        retries: Number of repair attempts. ``0`` disables fixing.
    Raises:
        ParseError: If parsing fails after all retries.
    Returns:
        Parsed Python object (type depends on *parser*).
    """
    
    # Handle edge cases where text might already be parsed or wrong type
    if isinstance(text, dict):
        # Text is already parsed as dict, try to return as is
        return text
    
    if not isinstance(text, str):
        # Convert to string if it's not already
        text = str(text)
    
    # Clean the text
    text = text.strip()

    try:
        return parser.parse(text)
    except Exception as err:  # noqa: BLE001
        if retries <= 0:
            raise ParseError("Failed to parse LLM output") from err

        # Attempt to auto-fix if supported by current LangChain version ------
        if hasattr(OutputFixingParser, "from_llm"):
            # LangChain changed the signature of ``OutputFixingParser.from_llm``
            # in late 2023.  Older versions expect the *destination parser* as
            # the first positional argument, whereas newer versions expect the
            # *llm* first.  We therefore try the old call signature and fall back
            # to the new one if we receive a ``TypeError`` about duplicated
            # arguments.  This keeps the Essay Agent compatible across a broad
            # range of LangChain releases without pinning to a specific minor
            # version.

            try:
                # Old style: (destination_parser, llm=...)
                fixing_parser = OutputFixingParser.from_llm(parser, llm=get_chat_llm())
            except TypeError:
                # New style: (llm, destination_parser)
                fixing_parser = OutputFixingParser.from_llm(get_chat_llm(), parser)  # type: ignore[arg-type]

            try:
                fixed_text = fixing_parser.parse(text)
                return safe_parse(parser, fixed_text, retries=retries - 1)
            except Exception:
                # If fixing fails, try manual cleanup
                try:
                    cleaned_text = clean_response_text(text)
                    return parser.parse(cleaned_text)
                except Exception:
                    # Last resort - return a basic fallback
                    return create_fallback_response(text)

        # Fallback: no auto-fix available ------------------------------------
        # Try manual cleanup
        try:
            cleaned_text = clean_response_text(text)
            return parser.parse(cleaned_text)
        except Exception:
            # Last resort - return a basic fallback
            return create_fallback_response(text)


def clean_response_text(text: str) -> str:
    """Clean response text to improve parsing."""
    if not isinstance(text, str):
        text = str(text)
    
    # Remove markdown code blocks
    text = re.sub(r'```(?:json|python)?\s*', '', text)
    text = re.sub(r'```\s*', '', text)
    
    # Remove extra whitespace
    text = text.strip()
    
    # Fix common JSON issues
    text = re.sub(r',\s*}', '}', text)  # Remove trailing commas
    text = re.sub(r',\s*]', ']', text)  # Remove trailing commas in arrays
    
    return text


def create_fallback_response(text: str) -> dict:
    """Create a fallback response when parsing fails."""
    return {
        "error": "Failed to parse response",
        "raw_text": str(text)[:200] + "..." if len(str(text)) > 200 else str(text),
        "success": False
    }


# ---------------------------------------------------------------------------
# Schema-specific parsers
# ---------------------------------------------------------------------------

def pydantic_parser(model: Type[BaseModel]) -> BaseOutputParser:
    """Return a LangChain PydanticOutputParser for model."""
    from langchain.output_parsers import PydanticOutputParser
    return PydanticOutputParser(pydantic_object=model)


def schema_parser(expected_schema: dict) -> BaseOutputParser:
    """Create a parser for a specific schema."""
    from langchain.output_parsers import StructuredOutputParser
    from langchain.output_parsers.pydantic import PydanticOutputParser
    
    # Try to create a structured output parser
    try:
        if hasattr(StructuredOutputParser, 'from_response_schemas'):
            return StructuredOutputParser.from_response_schemas(expected_schema)
    except Exception:
        pass
    
    # Fallback to basic JSON parser
    return JsonOutputParser()


class JsonOutputParser(BaseOutputParser):
    """Simple JSON output parser."""
    
    def parse(self, text: str) -> dict:
        """Parse JSON response."""
        if isinstance(text, dict):
            return text
        
        if not isinstance(text, str):
            text = str(text)
        
        text = clean_response_text(text)
        
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Try to extract JSON from the text
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass
            
            # Return fallback
            return create_fallback_response(text)
    
    def get_format_instructions(self) -> str:
        """Get format instructions."""
        return "Return a valid JSON object." 