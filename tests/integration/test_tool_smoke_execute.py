import asyncio
import inspect
import os

os.environ.setdefault("ESSAY_AGENT_OFFLINE_TEST", "1")

import pytest

from essay_agent.tools import REGISTRY
from essay_agent.utils.default_args import autofill_args
from essay_agent.memory.smart_memory import SmartMemory
from essay_agent.tools.integration import execute_tool


@pytest.mark.asyncio
async def test_all_tools_execute(tmp_path, monkeypatch):
    """Smoke test: every registered tool executes without missing-arg error."""

    # Point memory store at tmp dir to avoid clobbering real data
    monkeypatch.setattr("essay_agent.memory._MEMORY_ROOT", tmp_path, raising=False)

    user_id = "smoke_user"
    mem = SmartMemory(user_id)

    # Minimal fake context resembling ContextSnapshot dict --------------------
    ctx = {
        "essay_prompt": "Describe a challenge and what you learned",
        "college_context": {"school": "Stanford", "word_limit": 650},
        "preferences": {"preferred_word_count": 650, "tone": "neutral"},
        "recent_chat": ["dummy user input"],
        "outline": {"hook": "", "context": "", "conflict": "", "growth_moment": "", "reflection": ""},
    }

    failures = []

    for name, tool in REGISTRY.items():
        # Build step & autofill args
        step = {"tool": name, "args": {}}
        args = autofill_args(step, ctx, mem)

        # Execute tool
        result = await execute_tool(name, **args)

        if result.get("error") is not None:
            failures.append(f"{name}: {result['error']}")

    assert not failures, "Some tools failed execution: " + ", ".join(failures) 