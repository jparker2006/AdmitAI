import pytest

from essay_agent.agents.style_agent import StyleAgent
from essay_agent.agents.base import AgentState
from essay_agent.tools import REGISTRY as TOOL_REGISTRY


def test_style_agent_happy_path(monkeypatch):
    # Dummy outputs --------------------------------------------
    monkeypatch.setitem(TOOL_REGISTRY, "fix_grammar", lambda essay_text: {"corrected_essay": essay_text})
    monkeypatch.setitem(TOOL_REGISTRY, "enhance_vocabulary", lambda essay_text: {"enhanced_essay": essay_text})
    monkeypatch.setitem(TOOL_REGISTRY, "check_consistency", lambda essay_text: {"consistency_report": "ok"})
    monkeypatch.setitem(
        TOOL_REGISTRY,
        "optimize_word_count",
        lambda essay_text, target_words, preserve_meaning=True: {"optimized_essay": essay_text},
    )

    agent = StyleAgent()
    init_state = AgentState(
        data={
            "essay_text": "This is a rough draft of my essay.",
            "target_word_count": 650,
        }
    )

    result_state = agent.invoke(init_state)

    assert result_state.errors == []
    assert "optimized_essay" in result_state.data["optimize_word_count"] 