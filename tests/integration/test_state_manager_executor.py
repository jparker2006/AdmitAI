import pytest
from essay_agent.state_manager import ConversationStateManager
from essay_agent.executor import EssayExecutor
from essay_agent.planner import EssayPlan, Phase


@pytest.mark.asyncio
async def test_executor_with_state_manager(monkeypatch, tmp_path):
    """Ensure executor runs while conversation state manager persists."""

    # Mock tools to trivial functions
    from essay_agent.tools import TOOL_REGISTRY

    phase_to_tool = {
        Phase.BRAINSTORMING: "brainstorm",
        Phase.OUTLINING: "outline",
        Phase.DRAFTING: "draft",
        Phase.REVISING: "revise",
        Phase.POLISHING: "polish",
    }

    for tool_name in phase_to_tool.values():
        monkeypatch.setitem(TOOL_REGISTRY, tool_name, lambda n=tool_name: n.upper())

    # Conversation state
    mgr = ConversationStateManager("integration_user", storage_dir=tmp_path)
    mgr.add_user("start")

    executor = EssayExecutor()
    plan = EssayPlan(phase=Phase.BRAINSTORMING)
    updated_plan = await executor.run_plan_async(plan)

    assert updated_plan.errors == []
    mgr.add_ai("done")

    # Ensure messages persisted
    mgr2 = ConversationStateManager.load("integration_user", storage_dir=tmp_path)
    assert len(mgr2.messages) == 2 