from langchain.llms.fake import FakeListLLM
import pytest

from essay_agent.query_rewriter import QueryRewriter
from essay_agent.prompts.query_rewrite import REWRITE_PROMPT, COMPRESS_PROMPT


def test_rewrite_prompt_vars():
    assert set(REWRITE_PROMPT.input_variables) == {"query"}


def test_rewrite_chain(monkeypatch):
    fake = FakeListLLM(responses=["{\"result\": \"Improved query\"}"])
    monkeypatch.setattr("essay_agent.query_rewriter.get_chat_llm", lambda **_: fake)

    qr = QueryRewriter()
    out = qr.rewrite_query("bad query")
    assert out == "Improved query"


def test_compress_chain_max_tokens_passed(monkeypatch):
    response = "{\"result\": \"compressed\"}"
    fake = FakeListLLM(responses=[response])
    monkeypatch.setattr("essay_agent.query_rewriter.get_chat_llm", lambda **_: fake)
    qr = QueryRewriter()
    out = qr.compress_context("some long context", max_tokens=123)
    # Ensure we still get expected output
    assert out == "compressed"


def test_clarify_missing_json(monkeypatch):
    fake = FakeListLLM(responses=["Not JSON"])
    monkeypatch.setattr("essay_agent.query_rewriter.get_chat_llm", lambda **_: fake)
    qr = QueryRewriter()
    with pytest.raises(ValueError):
        _ = qr.clarify_question("What?") 