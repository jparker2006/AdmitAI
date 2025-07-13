from essay_agent.executor import EssayExecutor
from essay_agent.planner import EssayPlan, Phase
from essay_agent.tools import REGISTRY


def test_executor_with_registry(monkeypatch):
    # Ensure echo exists via registry
    assert "echo" in REGISTRY
    executor = EssayExecutor()
    plan = EssayPlan(phase=Phase.BRAINSTORMING)
    # Patch brainstorm/outline/... to echo to keep deterministic
    for name in ["brainstorm","outline","draft","revise","polish"]:
        monkeypatch.setitem(REGISTRY, name, REGISTRY["echo"])

    result = executor.run_plan(plan)
    assert "polish" in result
    assert "errors" not in result 