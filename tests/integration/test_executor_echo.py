from essay_agent.executor import EssayExecutor
from essay_agent.models import EssayPlan, Phase


def test_executor_graph_success(monkeypatch):
    """Executor should run through all five phases without errors when tools succeed."""

    executor = EssayExecutor()

    # Monkeypatch registry with simple no-arg lambdas to avoid argument issues
    from essay_agent.tools import TOOL_REGISTRY

    for phase_name, tool_name in {
        Phase.BRAINSTORMING: "brainstorm",
        Phase.OUTLINING: "outline",
        Phase.DRAFTING: "draft",
        Phase.REVISING: "revise",
        Phase.POLISHING: "polish",
    }.items():
        monkeypatch.setitem(TOOL_REGISTRY, tool_name, lambda n=tool_name: n.upper())

    plan = EssayPlan(phase=Phase.BRAINSTORMING)
    outputs = executor.run_plan(plan)

    # Assert each phase output exists
    assert outputs["brainstorm"] == "BRAINSTORM"
    assert outputs["outline"] == "OUTLINE"
    assert outputs["draft"] == "DRAFT"
    assert outputs["revise"] == "REVISE"
    assert outputs["polish"] == "POLISH"
    assert "errors" not in outputs 