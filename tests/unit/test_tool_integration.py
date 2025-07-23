import asyncio
import pytest

from essay_agent.tools.integration import build_params, execute_tool
from essay_agent.tools import REGISTRY
from essay_agent.tools.echo import EchoTool  # simple tool already registered

@pytest.mark.asyncio
async def test_execute_echo_tool():
    tool_name = "echo"
    params = build_params(tool_name, user_id="unit_user", user_input="Hi")
    params["message"] = "Hi"
    result = await execute_tool(tool_name, **params)
    assert result["error"] is None
    assert "Hello" in str(result["ok"]) or "Hi" in str(result["ok"]) 