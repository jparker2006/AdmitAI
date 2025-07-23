import os, json
from essay_agent.planner_prompt import PlannerPrompt


def test_build_prompt_contains_keys():
    tool_names = ["brainstorm_specific", "outline", "draft"]
    planner = PlannerPrompt(tool_names)
    ctx = {
        "last_tool": "brainstorm_specific",
        "recent_chat": ["Hi", "Hello", "Need help"],
        "profile": {"college": "Stanford", "essay_prompt": "Why?", "preferred_word_count": 650},
    }
    prompt = planner.build_prompt("Outline please", ctx)
    # Ensure crucial context fields are present
    assert "last_tool_used: brainstorm_specific" in prompt
    assert "recent_chat:" in prompt
    assert "Available tools" in prompt


def test_parse_response_and_offline_fallback(monkeypatch):
    tool_names = ["brainstorm_specific", "outline"]
    planner = PlannerPrompt(tool_names)
    raw = json.dumps({"plan": [{"tool": "outline", "args": {"story": "x"}}]})
    parsed = planner.parse_response(raw, offline=False)
    assert parsed[0]["tool"] == "outline"

    # Offline fallback
    monkeypatch.setenv("ESSAY_AGENT_OFFLINE_TEST", "1")
    parsed_off = planner.parse_response("{}")
    assert parsed_off[0]["tool"] == "brainstorm_specific"
    monkeypatch.delenv("ESSAY_AGENT_OFFLINE_TEST") 