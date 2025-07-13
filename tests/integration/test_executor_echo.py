from essay_agent.executor import EssayExecutor
from essay_agent.planner import Plan, Phase


def test_executor_runs_echo():
    executor = EssayExecutor()
    plan = Plan(phase=Phase.BRAINSTORMING, tasks=["echo"], metadata={})

    outputs = executor.run_plan(plan)

    assert outputs["echo"] == {"echo": "Hello, Essay Agent!"} 