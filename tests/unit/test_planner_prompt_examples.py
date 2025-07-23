import pathlib
from essay_agent.tools import REGISTRY

TEMPLATE_PATH = pathlib.Path("essay_agent/prompts/planner/100x_planner_prompt.txt")


def test_example_blocks_present():
    text = TEMPLATE_PATH.read_text(encoding="utf-8")
    for ex_id in ["EX1", "EX2", "EX3", "EX4", "EX5", "EX6", "EX7", "EX8"]:
        assert ex_id in text, f"Missing example block {ex_id}"


def test_every_tool_name_mentioned():
    """Ensure each registered tool name appears at least once in template text."""
    text = TEMPLATE_PATH.read_text(encoding="utf-8")
    missing = [name for name in REGISTRY.keys() if name not in text]
    # Allow chat_response to be missing since it's implicit fallback
    missing = [m for m in missing if m != "chat_response"]
    assert not missing, f"Tools not referenced in few-shot examples or quick map: {missing}"
