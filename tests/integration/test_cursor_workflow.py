import pytest

from essay_agent.agent_autonomous import AutonomousEssayAgent
from essay_agent.tools.smart_orchestrator import SmartOrchestrator


@pytest.mark.asyncio
async def test_cursor_workflow(monkeypatch):
    user_id = "cursor_test_user"
    agent = AutonomousEssayAgent(user_id)

    # Patch Context snapshot to include selection so param builder gets it
    async def _fake_snapshot(self, user_input):  # noqa: D401,E501
        class _Snap:  # noqa: D401
            def model_dump(self):
                return {"selection": "I love CS"}
        return _Snap()

    monkeypatch.setattr(agent.ctx_engine, "snapshot", _fake_snapshot.__get__(agent.ctx_engine))

    # Patch orchestrator execute_plan to mimic tool execution quickly
    async def _quick_plan(self, plan, *, original_user_input, context):  # noqa: D401,E501
        return {"steps": [{"tool": "improve_selection", "result": {"ok": {"improved_text": "Better"}}}]}

    monkeypatch.setattr(SmartOrchestrator, "execute_plan", _quick_plan, raising=True)

    response = await agent.handle_message("Improve this selection")
    assert isinstance(response, str)
    assert response 