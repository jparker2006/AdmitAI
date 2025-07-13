import pytest

from essay_agent.agents.research_agent import ResearchAgent
from essay_agent.agents.base import AgentState
from essay_agent.tools import REGISTRY as TOOL_REGISTRY


def test_research_agent_happy_path(monkeypatch):
    # Stub tools
    monkeypatch.setitem(TOOL_REGISTRY, "classify_prompt", lambda essay_prompt: "theme")
    monkeypatch.setitem(TOOL_REGISTRY, "extract_requirements", lambda essay_prompt: {"word_limit": 650})
    monkeypatch.setitem(TOOL_REGISTRY, "suggest_strategy", lambda essay_prompt, profile: "strategy")
    monkeypatch.setitem(TOOL_REGISTRY, "essay_scoring", lambda essay_text, essay_prompt: 9.5)

    agent = ResearchAgent()
    init_state = AgentState(
        data={
            "essay_prompt": "Describe a challenge you overcame.",
            "profile": "Student athlete, robotics captain",
            "essay_text": "Draft essay text...",
        }
    )

    result_state = agent.invoke(init_state)

    assert result_state.errors == []
    assert result_state.data["classify_prompt"] == "theme"
    assert result_state.data["suggest_strategy"] == "strategy" 