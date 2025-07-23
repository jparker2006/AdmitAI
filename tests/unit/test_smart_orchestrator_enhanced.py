import asyncio
from unittest.mock import AsyncMock, patch, MagicMock

import pytest

from essay_agent.tools.smart_orchestrator import SmartOrchestrator
from essay_agent.reasoning.bulletproof_reasoning import BulletproofReasoning


@pytest.mark.asyncio
async def test_retry_logic(monkeypatch):
    """Tool fails once then succeeds – SmartOrchestrator should retry."""
   
    # Mock execute_tool to fail then succeed
    calls = {}
    async def _fake_execute(tool, **kwargs):
        calls.setdefault(tool, 0)
        calls[tool] += 1
        if calls[tool] == 1:
            return {"ok": None, "error": "boom"}
        return {"ok": {"result": "ok"}, "error": None}

    monkeypatch.setattr("essay_agent.tools.smart_orchestrator.execute_tool", _fake_execute)

    orch = SmartOrchestrator(
        user_id="u1",
        memory=MagicMock(),
        context_engine=MagicMock(),
        reasoner=BulletproofReasoning(),
    )

    plan = [{"tool_name": "brainstorm", "tool_args": {}, "reasoning": "", "confidence": 0.9}]
    res = await orch.execute_plan(plan, original_user_input="hi", context={})
    assert res["steps"][0]["result"]["error"] is None
    assert calls["brainstorm"] == 2  # first failure, second success


@pytest.mark.asyncio
async def test_low_quality_triggers_followup(monkeypatch):
    """If draft quality is low, orchestrator should schedule improvement tool."""

    async def _dummy_execute(tool, **kwargs):
        if tool == "draft":
            return {"ok": {"draft": "short"}, "error": None}
        return {"ok": {"result": "improved"}, "error": None}

    monkeypatch.setattr("essay_agent.tools.smart_orchestrator.execute_tool", _dummy_execute)
    monkeypatch.setattr("essay_agent.intelligence.quality_engine.QualityEngine.score_draft", lambda self, text, user_id: 3.0)

    # Mock reasoner to avoid network
    fake_reasoner = AsyncMock(spec=BulletproofReasoning)
    fake_reasoner.decide_action.return_value = MagicMock(action="tool_execution", tool_name="revise", tool_args={}, reasoning="", confidence=0.9)

    orch = SmartOrchestrator("u2", MagicMock(), MagicMock(), reasoner=fake_reasoner)
    plan = [{"tool_name": "draft", "tool_args": {}, "reasoning": "", "confidence": 0.9}]
    res = await orch.execute_plan(plan, original_user_input="write", context={})

    tools_run = [s["tool"] for s in res["steps"]]
    assert "draft" in tools_run and "revise" in tools_run


@pytest.mark.asyncio
async def test_sequence_execution(monkeypatch):
    """select_tools should expand a tool_sequence into multiple steps."""

    orch = SmartOrchestrator("u3", MagicMock(), MagicMock(), reasoner=BulletproofReasoning())

    reasoning = {
        "action": "tool_sequence",
        "sequence": ["brainstorm", "outline"],
        "tool_args": {},
        "reasoning": "multi",
        "confidence": 0.9,
    }
    plan = asyncio.run(orch.select_tools(reasoning, {}))
    assert [p["tool_name"] for p in plan] == ["brainstorm", "outline"] 