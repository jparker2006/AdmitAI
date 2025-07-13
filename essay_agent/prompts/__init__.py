"""Prompt package helpers."""

from __future__ import annotations

from typing import Dict
import re
from importlib import resources

# ---------------------------------------------------------------------------
# Preferred source: Python prompt modules -----------------------------------
# ---------------------------------------------------------------------------

try:
    # The new canonical implementation lives in planning.py
    from .planning import SYSTEM_PROMPT, PLANNER_REACT_PROMPT  # type: ignore

except ModuleNotFoundError:  # pragma: no cover
    # ---------------------------------------------------------------------
    # Legacy support: fall back to planning.txt until fully migrated
    # ---------------------------------------------------------------------
    _TAG_RE = re.compile(r"<(?P<tag>[a-zA-Z_]+)>(?P<body>.*?)</(?P=tag)>", re.DOTALL)

    def _load_planning_prompts() -> Dict[str, str]:  # noqa: D401
        """Return dict with 'SYSTEM_PROMPT' and 'PLANNER_REACT_PROMPT'."""

        txt = resources.read_text(__package__, "planning.txt", encoding="utf-8")
        matches = {m.group("tag"): m.group("body").strip() for m in _TAG_RE.finditer(txt)}
        return {
            "SYSTEM_PROMPT": matches.get("system_prompt", ""),
            "PLANNER_REACT_PROMPT": matches.get("planner_react_prompt", ""),
        }

    _prompts = _load_planning_prompts()
    SYSTEM_PROMPT = _prompts["SYSTEM_PROMPT"]
    PLANNER_REACT_PROMPT = _prompts["PLANNER_REACT_PROMPT"]

# ---------------------------------------------------------------------------
# Re-export template helpers -------------------------------------------------
# ---------------------------------------------------------------------------

from .templates import (
    make_prompt,
    make_chat_prompt,
    make_few_shot_prompt,
    render_template,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
    META_VARS,
)

from .brainstorm import BRAINSTORM_PROMPT  # noqa: F401

try:
    __all__.append("BRAINSTORM_PROMPT")
except NameError:  # pragma: no cover
    __all__ = ["BRAINSTORM_PROMPT"]

# ---------------------------------------------------------------------------
# Public symbols update ------------------------------------------------------
# ---------------------------------------------------------------------------

__all__ = [
    "SYSTEM_PROMPT",
    "PLANNER_REACT_PROMPT",
    "make_prompt",
    "make_chat_prompt",
    "make_few_shot_prompt",
    "render_template",
    "HumanMessagePromptTemplate",
    "SystemMessagePromptTemplate",
    "META_VARS",
] 