import asyncio

import pytest

from essay_agent.tools.smart_orchestrator import SmartOrchestrator
from essay_agent.memory.smart_memory import SmartMemory
from essay_agent.intelligence.context_engine import ContextEngine
from essay_agent.reasoning.bulletproof_reasoning import BulletproofReasoning


class _DummyMemory(SmartMemory):
    """Lightweight stub for SmartMemory to avoid disk operations."""

    def __init__(self, user_id: str):
        super().__init__(user_id)

    # Override disk operations
    @classmethod
    def load(cls, user_id: str):  # noqa: D401
        return cls(user_id)


@pytest.mark.asyncio
async def test_select_and_execute_single_tool(monkeypatch):
    """SmartOrchestrator should execute the first chosen tool and return history."""

    user_id = "test_user"
    memory = _DummyMemory(user_id)
    ctx_engine = ContextEngine(user_id)
    orchestrator = SmartOrchestrator(user_id, memory, ctx_engine, BulletproofReasoning())

    reasoning = {
        "action": "tool_execution",
        "tool_name": "brainstorm",
        "tool_args": {},
        "reasoning": "initial test",
        "confidence": 0.9,
    }

    # Monkey-patch execute_tool to avoid hitting real tools
    from essay_agent.tools import smart_orchestrator as orchestrator_mod

    async def _fake_execute_tool(name: str, **params):  # noqa: D401
        return {"ok": {"dummy": True}, "error": None}

    monkeypatch.setattr(orchestrator_mod, "execute_tool", _fake_execute_tool)

    plan = await orchestrator.select_tools(reasoning, context={})
    result = await orchestrator.execute_plan(plan, original_user_input="Hello", context={})

    assert result["steps"], "No steps returned"
    assert result["steps"][0]["tool"] == "brainstorm"
    assert result["steps"][0]["result"]["ok"] == {"dummy": True} 