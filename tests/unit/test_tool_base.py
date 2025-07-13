import time
import pytest
from essay_agent.tools.base import ValidatedTool
from essay_agent.tools.errors import ToolError

class SleepTool(ValidatedTool):
    name="sleep"
    description="Sleep for given seconds"
    timeout=0.5
    def _run(self, seconds: float = 1.0):
        time.sleep(seconds)
        return {"slept": seconds}


def test_timeout():
    tool = SleepTool()
    out = tool(seconds=1.0)
    assert out["ok"] is None
    assert isinstance(out["error"], ToolError)


def test_success():
    tool = SleepTool()
    out = tool(seconds=0.1)
    assert out["error"] is None
    assert out["ok"]["slept"] == 0.1 