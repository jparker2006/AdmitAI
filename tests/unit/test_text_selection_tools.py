import pytest

from essay_agent.tools import REGISTRY


_SELECTION_TOOLS = [
    "modify_selection",
    "explain_selection",
    "improve_selection",
    "rewrite_selection",
    "expand_selection",
    "condense_selection",
    "replace_selection",
    "smart_autocomplete",
    "transition_helper",
    "voice_matcher",
    "live_feedback",
    "word_choice_optimizer",
    "authenticity_checker",
    "goal_tracker",
    "strategy_advisor",
]


@pytest.mark.parametrize("tool_name", _SELECTION_TOOLS)
def test_selection_tool_runs(tool_name, monkeypatch):
    """Ensure each cursor-style tool has a description and invokes the LLM helper."""

    # Patch call_llm to avoid network access and flag invocation
    def _fake_call(llm, prompt, **kwargs):  # noqa: D401
        _fake_call.called = True
        return "Foo bar"

    _fake_call.called = False

    monkeypatch.setattr("essay_agent.llm_client.call_llm", _fake_call)

    tool = REGISTRY.get(tool_name)
    assert tool is not None, f"Tool {tool_name} not registered"

    # Description should be meaningful (>10 chars)
    assert hasattr(tool, "description") and len(tool.description) > 10

    result = tool(selection="I love CS", instruction="test", user_id="u", profile={})
    assert result["error"] is None, result["error"]
    assert result["ok"] is not None
    assert _fake_call.called, "LLM helper was not invoked" 