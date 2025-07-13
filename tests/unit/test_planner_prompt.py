import json
from essay_agent.planner import EssayReActPlanner, Phase
from essay_agent.tools import REGISTRY
from langchain.llms.fake import FakeListLLM


def test_planner_returns_brainstorm():
    fake = FakeListLLM(responses=[
        '{"tool": "brainstorm", "args": {}}'
    ])
    planner = EssayReActPlanner(llm=fake)
    plan = planner.decide_next_action("I need ideas", context={})
    assert plan.phase == Phase.BRAINSTORMING
    assert plan.data["next_tool"] == "brainstorm" 