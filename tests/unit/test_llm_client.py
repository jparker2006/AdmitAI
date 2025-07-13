import importlib
import os
from types import SimpleNamespace

import pytest
from langchain.llms.fake import FakeListLLM

import essay_agent.llm_client as llm_client


def _reload_client(monkeypatch):
    """Reload the llm_client module so env var changes take effect."""

    importlib.reload(llm_client)
    return llm_client


def test_llm_client_offline(monkeypatch):
    # Ensure no API key so FakeListLLM is returned
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    client = _reload_client(monkeypatch)

    llm = client.get_chat_llm()
    assert isinstance(llm, FakeListLLM)


def test_track_cost(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    client = _reload_client(monkeypatch)

    with client.track_cost() as (llm, cb):
        result = llm.predict("Hello")
        assert isinstance(result, str)
        # With FakeListLLM we should have zero cost / tokens
        assert cb.total_cost == 0
        assert cb.total_tokens == 0


def test_llm_client_cache(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("ESSAY_AGENT_CACHE", "1")
    client = _reload_client(monkeypatch)

    # First call
    first = client.chat("cached prompt")
    # Second call should hit cache and return identical string
    second = client.chat("cached prompt")
    assert first == second


def test_llm_client_retry(monkeypatch):
    # Stub LLM that fails twice then succeeds
    class FailingTwiceLLM:
        def __init__(self):
            self.calls = 0

        def predict(self, *args, **kwargs):  # noqa: D401
            if self.calls < 2:
                self.calls += 1
                raise Exception("Rate limit")
            return "OK"

    failing_llm = FailingTwiceLLM()

    # Patch the public factory so chat() receives our stub
    monkeypatch.setattr(llm_client, "get_chat_llm", lambda **_: failing_llm, raising=False)

    # Re-import chat function (decorator already applied)
    result = llm_client.chat("Retry test")
    assert result == "OK"
    assert failing_llm.calls == 2 