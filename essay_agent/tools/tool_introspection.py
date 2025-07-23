"""essay_agent.tools.tool_introspection

Runtime helper that inspects every registered tool and builds a catalogue
of required / optional arguments.  This will be used by the future
ArgResolver so we can supply correct kwargs without hard-coded mappings.

The catalogue is generated at **import time** so other modules can simply:

>>> from essay_agent.tools.tool_introspection import TOOL_ARG_SPEC, get_required_args
"""
from __future__ import annotations

import inspect
from types import MappingProxyType
from typing import Dict, List, Tuple

from essay_agent.tools import REGISTRY  # Imported late to avoid circulars

# ---------------------------------------------------------------------------
# Introspection helpers
# ---------------------------------------------------------------------------

_SKIP_NAMES = {
    "self",  # instance param
    "_",      # convention for catch-all kwargs
    "args",   # *args
    "kwargs", # **kwargs
    "tool_input",  # generic text input arg used by some tools
}


def _signature_args(tool) -> Tuple[List[str], List[str]]:
    """Return (required, optional) kw-only argument names from _run signature."""
    required: List[str] = []
    optional: List[str] = []

    try:
        sig = inspect.signature(tool._run)  # type: ignore[attr-defined]
    except (AttributeError, ValueError):
        return required, optional

    from inspect import Parameter

    for name, param in sig.parameters.items():
        if name in _SKIP_NAMES:
            continue
        if param.kind in (Parameter.VAR_KEYWORD, Parameter.VAR_POSITIONAL):
            continue
        if param.default is Parameter.empty:
            required.append(name)
        else:
            optional.append(name)

    return required, optional


def _pydantic_input_args(tool) -> Tuple[List[str], List[str]]:
    """Extract arg names from a Pydantic *InputModel* attribute if present."""
    try:
        input_model = getattr(tool, "InputModel")
    except AttributeError:
        return [], []

    try:
        fields = input_model.model_fields  # Pydantic v2
    except AttributeError:
        fields = getattr(input_model, "__fields__", {})  # Pydantic v1 fallback

    required: List[str] = []
    optional: List[str] = []

    for name, field in fields.items():  # type: ignore[attr-defined]
        if name in _SKIP_NAMES:
            continue
        if getattr(field, "is_required", getattr(field, "required", False)):
            required.append(name)
        else:
            optional.append(name)
    return required, optional


# ---------------------------------------------------------------------------
# Docstring parser fallback
# ---------------------------------------------------------------------------

import re


_DOC_ARG_RE = re.compile(r"^\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:\s", re.MULTILINE)


def _docstring_args(tool) -> List[str]:
    """Parse Args: section of docstring for param names."""
    doc = inspect.getdoc(tool.__class__) or inspect.getdoc(tool) or ""
    if "Args:" not in doc:
        return []
    # take lines after Args:
    try:
        args_part = doc.split("Args:")[1]
    except Exception:
        return []
    return _DOC_ARG_RE.findall(args_part)


# ---------------------------------------------------------------------------
# Build the catalogue
# ---------------------------------------------------------------------------

_spec: Dict[str, Dict[str, List[str]]] = {}

for name, tool in REGISTRY.items():
    sig_req, sig_opt = _signature_args(tool)
    mdl_req, mdl_opt = _pydantic_input_args(tool)
    doc_req = _docstring_args(tool)

    optional = sorted(set(sig_opt + mdl_opt))
    required = sorted({*sig_req, *mdl_req, *doc_req} - set(optional))

    _spec[name] = {
        "required": required,
        "optional": optional,
    }

# Freeze to read-only mapping to discourage mutation at runtime
TOOL_ARG_SPEC: Dict[str, Dict[str, List[str]]] = MappingProxyType(_spec)  # type: ignore[arg-type]

# ---------------------------------------------------------------------------
# Convenience helpers
# ---------------------------------------------------------------------------

def get_required_args(tool_name: str) -> List[str]:
    return TOOL_ARG_SPEC.get(tool_name, {}).get("required", [])


def get_optional_args(tool_name: str) -> List[str]:
    return TOOL_ARG_SPEC.get(tool_name, {}).get("optional", [])


__all__ = ["TOOL_ARG_SPEC", "get_required_args", "get_optional_args"] 