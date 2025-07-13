"""Prompt package helpers."""

from __future__ import annotations

import re
from importlib import resources
from typing import Dict

_TAG_RE = re.compile(r"<(?P<tag>[a-zA-Z_]+)>(?P<body>.*?)</(?P=tag)>", re.DOTALL)


def _load_planning_prompts() -> Dict[str, str]:
    """Return dict with 'system_prompt' and 'planner_react_prompt'."""
    txt = resources.read_text(__package__, "planning.txt", encoding="utf-8")
    matches = {m.group("tag"): m.group("body").strip() for m in _TAG_RE.finditer(txt)}
    return {
        "SYSTEM_PROMPT": matches.get("system_prompt", ""),
        "PLANNER_REACT_PROMPT": matches.get("planner_react_prompt", ""),
    }

PLANNING_PROMPTS = _load_planning_prompts()

SYSTEM_PROMPT = PLANNING_PROMPTS["SYSTEM_PROMPT"]
PLANNER_REACT_PROMPT = PLANNING_PROMPTS["PLANNER_REACT_PROMPT"] 