import os

os.environ["ESSAY_AGENT_OFFLINE_TEST"] = "1"  # Ensure deterministic stub

from essay_agent.tools import REGISTRY


def test_chat_response_offline():
    tool = REGISTRY.get("chat_response")
    assert tool is not None, "chat_response tool should be registered"

    result = tool(prompt="Hello there!")  # type: ignore[arg-type]
    assert result["error"] is None
    reply = result["ok"].get("reply") if isinstance(result["ok"], dict) else None
    assert isinstance(reply, str) and reply, "chat_response should return a non-empty reply string" 