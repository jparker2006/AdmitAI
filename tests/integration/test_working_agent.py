import pytest
from essay_agent.agent_legacy import EssayAgent
from essay_agent.models import EssayPrompt
from essay_agent.tools import REGISTRY

from langchain.llms.fake import FakeListLLM


def _patch_registry(monkeypatch):
    # Brainstorm needs 'stories' list
    monkeypatch.setitem(
        REGISTRY,
        "brainstorm",
        lambda **_: {"ok": {"stories": [{"title": "New Story"}]}, "error": None},
    )

    # Other tools return raw dicts (no wrapper) to satisfy agent's branching logic
    monkeypatch.setitem(REGISTRY, "outline", lambda **_: {"outline": {"hook": "", "context": "", "conflict": "", "growth": "", "reflection": ""}})
    monkeypatch.setitem(REGISTRY, "draft", lambda **_: {"draft": "DRAFT"})
    monkeypatch.setitem(REGISTRY, "revise", lambda **_: {"revised_draft": "REVISED", "changes": []})
    monkeypatch.setitem(REGISTRY, "polish", lambda **_: {"final_draft": "POLISH"})


@pytest.fixture(autouse=True)
def _clear_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)


def test_agent_workflow(monkeypatch, tmp_path):
    # Redirect memory store
    monkeypatch.setattr("essay_agent.memory._MEMORY_ROOT", tmp_path, raising=False)

    _patch_registry(monkeypatch)

    agent = EssayAgent(user_id="test_user")
    prompt = EssayPrompt(text="Describe a challenge", word_limit=100, college="Harvard")
    result = agent.generate_essay(prompt)

    assert result["final_draft"]  # uppercase POLISH
    assert "workflow" in result and set(result["workflow"].keys()) == {
        "brainstorm",
        "outline",
        "draft",
        "revise",
        "polish",
    } 