import os
from types import SimpleNamespace
import pytest

os.environ["ESSAY_AGENT_OFFLINE_TEST"] = "1"

from essay_agent.tools.smart_orchestrator import SmartOrchestrator


@pytest.mark.asyncio
async def test_orchestrator_empty_plan_falls_back_to_chat_response():
    orch = SmartOrchestrator(user_id="test_user", memory=SimpleNamespace(), context_engine=None)

    result = await orch.execute_plan([], original_user_input="Hi", context={})
    steps = result.get("steps", [])
    assert steps, "Orchestrator should execute at least one step"
    first = steps[0]
    assert first["tool"] == "chat_response", "Fallback tool should be chat_response" 