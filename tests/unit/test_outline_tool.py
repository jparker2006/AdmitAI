import os

import pytest

from essay_agent.tools.outline import OutlineTool


@pytest.fixture(autouse=True)
def _clear_api_key(monkeypatch):
    """Ensure OPENAI_API_KEY absent so FakeListLLM path is used in CI."""

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)


def test_outline_success_offline():
    tool = OutlineTool()
    result = tool(
        story="Questioning Traditional Gender Roles in Debate",
        prompt="Describe a time you challenged a belief or idea.",
        word_count=650,
    )

    assert "outline" in result
    outline = result["outline"]
    # Five required keys present
    for key in ["hook", "context", "conflict", "growth", "reflection"]:
        assert key in outline and isinstance(outline[key], str)

    assert result["estimated_word_count"] == 650


def test_outline_bad_inputs():
    tool = OutlineTool()
    with pytest.raises(ValueError):
        tool(story="", prompt="Prompt", word_count=650)
    with pytest.raises(ValueError):
        tool(story="Story", prompt="", word_count=650)
    with pytest.raises(ValueError):
        tool(story="Story", prompt="Prompt", word_count=0) 