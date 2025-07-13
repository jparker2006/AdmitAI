import pytest
import asyncio

from essay_agent.executor import EssayExecutor
from essay_agent.planner import EssayPlan, Phase


@pytest.mark.asyncio
async def test_stategraph_no_errors(monkeypatch):
    from essay_agent.tools import TOOL_REGISTRY
    executor = EssayExecutor()

    # Patch tools to predictable outputs
    monkeypatch.setitem(TOOL_REGISTRY, "brainstorm", lambda: "idea")
    monkeypatch.setitem(TOOL_REGISTRY, "outline", lambda: "outline")
    monkeypatch.setitem(TOOL_REGISTRY, "draft", lambda: "draft")
    monkeypatch.setitem(TOOL_REGISTRY, "revise", lambda: "revised")
    monkeypatch.setitem(TOOL_REGISTRY, "polish", lambda: "polished")

    plan = EssayPlan(phase=Phase.BRAINSTORMING)
    updated_plan = await executor.run_plan_async(plan)

    assert updated_plan.errors == []
    assert updated_plan.data["brainstorm"] == "idea"
    assert updated_plan.phase == Phase.POLISHING  # finished last update 