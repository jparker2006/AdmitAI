from essay_agent.planner import EssayReActPlanner, Phase, EssayPlan
from essay_agent.executor import EssayExecutor
from langchain.llms.fake import FakeListLLM


def test_planner_executor_cycle(monkeypatch):
    fake = FakeListLLM(responses=[
        '{"tool": "outline", "args": {}}'
    ])
    planner = EssayReActPlanner(llm=fake)
    plan = planner.decide_next_action("Let's outline", context={})
    assert plan.data["next_tool"] == "outline"

    # Monkeypatch tools so executor has outline
    from essay_agent.tools import REGISTRY
    monkeypatch.setitem(REGISTRY, "outline", lambda: "ok")

    result = EssayExecutor().run_plan(EssayPlan(phase=plan.phase))
    assert result["outline"] == "ok" 