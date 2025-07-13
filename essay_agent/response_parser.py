"""essay_agent.response_parser

Standardised parsing & validation utilities for Essay Agent.

The module provides thin wrappers around LangChain's output-parsers plus a
``safe_parse`` helper that can automatically repair malformed LLM outputs via
`OutputFixingParser`.  It ensures all parsed objects conform to either a
Pydantic model or a JSON Schema.
"""
from __future__ import annotations

from typing import Any, Type, Union, Dict

from pydantic import BaseModel, ValidationError
# Prefer new community package paths, fallback if not available
try:
    from langchain_community.output_parsers import (
        PydanticOutputParser,
        StructuredOutputParser,
        OutputFixingParser,
        ResponseSchema,
    )
except ImportError:  # pragma: no cover – older LangChain fallback
    from langchain.output_parsers import (
        PydanticOutputParser,
        StructuredOutputParser,
        OutputFixingParser,
        ResponseSchema,
    )

# For newer LangChain versions, a common abstract base may not be exported.
try:
    from langchain.output_parsers import OutputParser  # type: ignore
except ImportError:  # pragma: no cover
    from typing import Protocol as OutputParser  # type: ignore

from essay_agent.llm_client import get_chat_llm

__all__ = [
    "ParseError",
    "JsonResponse",
    "pydantic_parser",
    "schema_parser",
    "safe_parse",
]


class ParseError(ValueError):
    """Raised when parsing fails even after repair attempts."""


class JsonResponse(BaseModel):
    """Very small default model: any JSON object with a *result* field."""

    result: Any


# ---------------------------------------------------------------------------
# Factory helpers
# ---------------------------------------------------------------------------

def pydantic_parser(model: Type[BaseModel]) -> OutputParser:  # noqa: D401
    """Return a LangChain :class:`PydanticOutputParser` for *model*."""

    return PydanticOutputParser(pydantic_object=model)


def schema_parser(schema: Dict[str, Any]) -> OutputParser:  # noqa: D401
    """Return a ``StructuredOutputParser`` built from a simplified JSON schema.

    Current LangChain versions expose ``from_response_schemas`` instead of the
    previous ``from_json_schema`` helper.  We convert *schema*'s top-level
    properties to :class:`ResponseSchema` objects with empty descriptions.
    """

    properties = schema.get("properties", {})
    response_schemas = [ResponseSchema(name=k, description="") for k in properties.keys()]
    return StructuredOutputParser.from_response_schemas(response_schemas)


# ---------------------------------------------------------------------------
# Safe parse helper with automatic fixing
# ---------------------------------------------------------------------------

def safe_parse(parser: OutputParser, text: str, *, retries: int = 2) -> Any:  # noqa: D401
    """Parse *text* with *parser*, retrying via ``OutputFixingParser`` if needed.

    Args:
        parser: Any LangChain ``OutputParser``.
        text: Raw LLM response string.
        retries: Number of repair attempts. ``0`` disables fixing.
    Raises:
        ParseError: If parsing fails after all retries.
    Returns:
        Parsed Python object (type depends on *parser*).
    """

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

            fixed_text = fixing_parser.parse(text)
            return safe_parse(parser, fixed_text, retries=retries - 1)

        # Fallback: no auto-fix available ------------------------------------
        raise ParseError("Failed to parse LLM output and no fixer available") from err 