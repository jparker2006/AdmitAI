import pytest

from essay_agent.tools.revision import RevisionTool


@pytest.fixture(autouse=True)
def _clear_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)


def test_revision_success_offline():
    tool = RevisionTool()
    result = tool(
        draft="I learned perseverance when...",
        revision_focus="add vivid imagery to opening",
    )

    assert set(result.keys()) == {"revised_draft", "changes"}
    assert result["revised_draft"].startswith("I learned perseverance")
    assert isinstance(result["changes"], list) and result["changes"]


def test_revision_bad_inputs():
    tool = RevisionTool()
    with pytest.raises(ValueError):
        tool(draft="", revision_focus="focus")
    with pytest.raises(ValueError):
        tool(draft="draft", revision_focus="") 