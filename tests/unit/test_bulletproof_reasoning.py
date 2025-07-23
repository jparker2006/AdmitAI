import asyncio
import pytest

from essay_agent.reasoning.bulletproof_reasoning import BulletproofReasoning


class _FakeLLM:
    """Simple fake LLM that yields predefined responses."""

    def __init__(self, responses):
        self._responses = responses
        self._idx = 0

    async def ainvoke(self, prompt):  # LangChain async interface
        idx = self._idx
        self._idx += 1
        return self._responses[min(idx, len(self._responses) - 1)]


@pytest.mark.asyncio
async def test_valid_json_first_try(monkeypatch):
    good_json = '{"action": "tool_execution", "tool_name": "brainstorm", "tool_args": {}, "reasoning": "ok", "confidence": 0.9}'
    monkeypatch.setattr(
        "essay_agent.reasoning.bulletproof_reasoning.get_chat_llm",
        lambda temperature=0.2: _FakeLLM([good_json]),
    )
    engine = BulletproofReasoning()
    res = await engine.decide_action("help me brainstorm", {})
    assert res.action == "tool_execution"
    assert res.tool_name == "brainstorm"
    assert res.confidence == 0.9


@pytest.mark.asyncio
async def test_retry_then_success(monkeypatch):
    bad = 'not json'
    good = '{"action": "conversation", "tool_name": null, "tool_args": {}, "reasoning": "talk", "confidence": 0.8}'
    monkeypatch.setattr(
        "essay_agent.reasoning.bulletproof_reasoning.get_chat_llm",
        lambda temperature=0.2: _FakeLLM([bad, good]),
    )
    engine = BulletproofReasoning()
    res = await engine.decide_action("hello", {})
    assert res.action == "conversation"
    assert res.confidence == 0.8


@pytest.mark.asyncio
async def test_exhaust_retries(monkeypatch):
    monkeypatch.setattr(
        "essay_agent.reasoning.bulletproof_reasoning.get_chat_llm",
        lambda temperature=0.2: _FakeLLM(["oops"] * 3),
    )
    engine = BulletproofReasoning()
    res = await engine.decide_action("hi", {})
    assert res.action == "conversation"
    assert res.confidence == 0.3 