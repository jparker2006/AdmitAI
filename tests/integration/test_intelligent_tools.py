import asyncio

import pytest

from essay_agent.agent_autonomous import AutonomousEssayAgent


@pytest.mark.asyncio
async def test_agent_runs_brainstorm_to_polish(monkeypatch):
    """High-level smoke test ensuring the agent can run through at least one tool."""

    user_id = "integration_test_user"
    agent = AutonomousEssayAgent(user_id)

    # Monkey-patch SmartOrchestrator.execute_plan to shortcut heavy calls
    from essay_agent.tools.smart_orchestrator import SmartOrchestrator

    async def _fake_execute_plan(self, plan, *, original_user_input, context):  # noqa: D401,E501
        # Pretend we ran five tools
        return {
            "steps": [
                {"tool": "brainstorm", "result": {"ok": True}},
                {"tool": "outline", "result": {"ok": True}},
                {"tool": "draft", "result": {"ok": True}},
                {"tool": "revise", "result": {"ok": True}},
                {"tool": "polish", "result": {"ok": True}},
            ]
        }

    monkeypatch.setattr(SmartOrchestrator, "execute_plan", _fake_execute_plan, raising=True)

    response = await agent.handle_message("Help me with my essay")
    assert isinstance(response, str)
    assert response, "Agent did not return any response" 