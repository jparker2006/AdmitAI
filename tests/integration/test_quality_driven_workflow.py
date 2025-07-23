import pytest

from essay_agent.agent_autonomous import AutonomousEssayAgent
from essay_agent.tools.smart_orchestrator import SmartOrchestrator


@pytest.mark.asyncio
async def test_quality_loop(monkeypatch):
    user = "quality_user"
    agent = AutonomousEssayAgent(user)

    # Force quality engine to return 6 then 9
    scores = [6.0, 9.1]

    def _fake_score(self, text, *, user_id="_qi"):
        return scores.pop(0)

    monkeypatch.setattr(
        agent.orchestrator.quality_engine,
        "score_draft",
        _fake_score.__get__(agent.orchestrator.quality_engine),
    )

    # Patch execute_tool to pretend revise tool runs
    async def _fake_execute(name: str, **params):
        return {"ok": {"draft": "Improved draft"}, "error": None}

    monkeypatch.setattr("essay_agent.tools.integration.execute_tool", _fake_execute)

    response = await agent.handle_message("Write my essay draft")
    assert "Improved" in response 