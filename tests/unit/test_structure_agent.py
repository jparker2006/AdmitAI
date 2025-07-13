import pytest

from essay_agent.agents.structure_agent import StructureAgent
from essay_agent.agents.base import AgentState
from essay_agent.tools import REGISTRY as TOOL_REGISTRY


def test_structure_agent_happy_path(monkeypatch):
    # Stub tools with predictable outputs --------------------------------------
    monkeypatch.setitem(
        TOOL_REGISTRY,
        "outline_generator",
        lambda story, essay_prompt, word_count=650: "outline",
    )
    monkeypatch.setitem(
        TOOL_REGISTRY,
        "structure_validator",
        lambda outline: "validated",
    )
    monkeypatch.setitem(
        TOOL_REGISTRY,
        "transition_suggestion",
        lambda outline: "transitions",
    )
    monkeypatch.setitem(
        TOOL_REGISTRY,
        "length_optimizer",
        lambda outline, target_word_count: "optimized",
    )

    agent = StructureAgent()
    init_state = AgentState(
        data={
            "story": "Some compelling story",
            "essay_prompt": "Describe a challenge you overcame.",
            "word_count": 650,
        }
    )

    result_state = agent.invoke(init_state)

    assert result_state.errors == []
    assert result_state.data["outline_generator"] == "outline"
    assert result_state.data["length_optimizer"] == "optimized" 