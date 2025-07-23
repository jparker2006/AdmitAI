import os, random, asyncio

os.environ["ESSAY_AGENT_OFFLINE_TEST"] = "1"

from essay_agent.tools import REGISTRY
from essay_agent.tools.smart_orchestrator import SmartOrchestrator
from essay_agent.memory.smart_memory import SmartMemory
from essay_agent.intelligence.context_engine import ContextEngine
from essay_agent.reasoning.bulletproof_reasoning import BulletproofReasoning

from essay_agent.utils.test_helpers import universal_context

async def _run_sample(tool_names):
    orchestrator = SmartOrchestrator(
        user_id="test_user",
        memory=SmartMemory("test_user"),
        context_engine=ContextEngine("test_user"),
        reasoner=BulletproofReasoning(),
    )
    plan = [{"tool_name": n, "tool_args": {}} for n in tool_names]
    res = await orchestrator.execute_plan(plan, user_input="hi", context=universal_context())
    return res


def test_orchestrator_arg_flow():
    sample_tools = random.sample(list(REGISTRY.keys()), k=min(5, len(REGISTRY)))
    res = asyncio.run(_run_sample(sample_tools))
    # We expect at least one step executed without error
    steps = res.get("steps", [])
    assert steps, "No steps executed"
    for step in steps:
        result = step.get("result", {})
        assert result.get("error") is None, f"Tool {step['tool']} errored" 