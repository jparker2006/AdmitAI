from __future__ import annotations

"""schema_registry – maps tool names to JSON schema snippets for repair assistant.

We attempt to grab the underlying Pydantic model from each tool's parser
(if available) and serialise its JSON schema.  Tools without an obvious
schema fall back to an empty string – the repair assistant will then rely on
existing fields in the raw text.
"""

from typing import Dict
from pydantic import BaseModel
from essay_agent.tools import REGISTRY

TOOL_OUTPUT_SCHEMA: Dict[str, str] = {}

for name, tool in REGISTRY.items():
    schema_str = ""
    # Try common attribute patterns
    mdl = None
    try:
        parser = getattr(tool, "_PARSER", None)
        if parser and hasattr(parser, "pydantic_object"):
            mdl = parser.pydantic_object  # type: ignore[attr-defined]
    except Exception:
        pass
    # Fallback: attribute named <ToolName>Result
    if mdl is None:
        try:
            result_name = f"{tool.__class__.__name__.replace('Tool','')}Result"
            mdl = getattr(tool.__class__.__module__, result_name, None)  # type: ignore
        except Exception:
            pass
    if mdl and isinstance(mdl, type) and issubclass(mdl, BaseModel):
        try:
            schema_str = mdl.model_json_schema()  # type: ignore[attr-defined]
        except Exception:
            pass
    TOOL_OUTPUT_SCHEMA[name] = schema_str

__all__ = ["TOOL_OUTPUT_SCHEMA"] 