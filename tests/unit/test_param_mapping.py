import pytest
from unittest.mock import patch, MagicMock

from essay_agent.tools import REGISTRY as TOOL_REGISTRY
from essay_agent.tools.integration import build_params


class _DummyProfile:
    def model_dump(self):
        return {"name": "test"}


@pytest.mark.parametrize("tool_name", list(TOOL_REGISTRY.keys()))
def test_build_params_returns_dict(tool_name, monkeypatch):
    """build_params should always return a non-empty dict for every tool."""

    # Monkeypatch SimpleMemory.load to avoid disk access
    monkeypatch.setattr(
        "essay_agent.tools.integration.SimpleMemory.load",
        lambda uid: _DummyProfile(),
    )

    ctx = {
        "essay_prompt": "Why CS?",
        "selection": "I love coding",
        "instruction": "make it punchy",
    }
    params = build_params(tool_name, user_id="test_user", user_input="Help", context=ctx)
    assert isinstance(params, dict) and params, f"Params empty for {tool_name}"

    # Cursor tools must include selection
    if tool_name in {
        "modify_selection",
        "explain_selection",
        "improve_selection",
        "rewrite_selection",
        "expand_selection",
        "condense_selection",
        "replace_selection",
    }:
        assert "selection" in params 