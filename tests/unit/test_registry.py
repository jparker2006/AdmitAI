import pytest
from essay_agent.tools import REGISTRY, register_tool
from essay_agent.tools.base import ValidatedTool


@register_tool("dummy")
class DummyTool(ValidatedTool):
    name="dummy"
    description="dummy"
    def _run(self):
        return {"hello":"world"}


def test_registry_call():
    res = REGISTRY.call("dummy")
    assert res["ok"] == {"hello":"world"}
    assert res["error"] is None

@pytest.mark.asyncio
async def test_registry_acall():
    out = await REGISTRY.acall("dummy")
    assert out["ok"]["hello"] == "world" 