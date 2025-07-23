import os
import pytest
from essay_agent.agents.response_enhancer import ResponseEnhancer


def test_offline_no_change(monkeypatch):
    monkeypatch.setenv("ESSAY_AGENT_OFFLINE_TEST", "1")
    original = "Raw reply text."
    enhanced = ResponseEnhancer.enhance(original, context={}, politeness_level=2)
    assert enhanced == original
    monkeypatch.delenv("ESSAY_AGENT_OFFLINE_TEST") 