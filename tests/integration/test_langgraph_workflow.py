import pytest

from essay_agent.executor import EssayExecutor
from essay_agent.planner import EssayPlan, Phase


def test_langgraph_error_handling(monkeypatch):
    from essay_agent.tools import TOOL_REGISTRY
    executor = EssayExecutor()

    # Good tools for first two phases
    monkeypatch.setitem(TOOL_REGISTRY, "brainstorm", lambda: "ok")

    # Inject error in outline tool
    def _boom():
        raise RuntimeError("outline failed")

    monkeypatch.setitem(TOOL_REGISTRY, "outline", _boom)

    # Remaining tools shouldn't matter but patch to detect they are *not* called
    called = {}
    for t in ["draft", "revise", "polish"]:
        def _spy(name=t):
            called[name] = True
            return name
        monkeypatch.setitem(TOOL_REGISTRY, t, _spy)

    plan = EssayPlan(phase=Phase.BRAINSTORMING)
    result = executor.run_plan(plan)

    # Error captured
    assert "errors" in result
    assert "outline failed" in result["errors"][0]

    # Draft phase should not have executed
    assert "draft" not in result 