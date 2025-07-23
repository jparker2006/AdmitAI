import os
import json
from essay_agent.utils.json_repair import fix
from essay_agent.tools.schema_registry import TOOL_OUTPUT_SCHEMA


def test_brainstorm_array_wrapped_to_dict():
    """Ensure json_repair.wraps array output into {"stories": [...]} dict."""
    os.environ["ESSAY_AGENT_OFFLINE_TEST"] = "1"  # deterministic path
    raw = """```json
    [
      {\"title\":\"A\",\"description\":\"Short\"}
    ]
    ```"""
    repaired = fix(raw, TOOL_OUTPUT_SCHEMA.get("brainstorm", ""))
    data = json.loads(repaired)
    assert isinstance(data, dict)
    assert "stories" in data
    # Ensure alias mapping worked
    item = data["stories"][0]
    assert "title" in item and "description" in item 