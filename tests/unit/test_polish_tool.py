import json

import pytest
from langchain.llms.fake import FakeListLLM

from essay_agent.prompts.polish import POLISH_PROMPT
from essay_agent.tools.polish import PolishTool
from essay_agent.tools import REGISTRY


def test_prompt_variables():
    required = {"draft", "word_count", "today"}
    assert required.issubset(set(POLISH_PROMPT.input_variables))


def _make_sentence(n: int) -> str:
    # Return a string with exactly n words: "w1 w2 ... wn"
    return " ".join([f"w{i}" for i in range(1, n + 1)])


def test_polish_success(monkeypatch):
    word_count = 5
    fake_draft = _make_sentence(word_count)
    fake_response = json.dumps({"final_draft": fake_draft})
    fake_llm = FakeListLLM(responses=[fake_response])
    monkeypatch.setattr("essay_agent.tools.polish.get_chat_llm", lambda **_: fake_llm)

    tool = PolishTool()
    out = tool(draft="Needs polish", word_count=word_count)

    assert out["error"] is None
    assert out["ok"]["final_draft"] == fake_draft

    # Registry call
    reg_out = REGISTRY.call("polish", draft="Needs polish", word_count=word_count)
    assert reg_out["ok"]["final_draft"] == fake_draft


def test_word_count_mismatch(monkeypatch):
    # LLM returns 4 words but asks for 5
    fake_response = json.dumps({"final_draft": _make_sentence(4)})
    fake_llm = FakeListLLM(responses=[fake_response])
    monkeypatch.setattr("essay_agent.tools.polish.get_chat_llm", lambda **_: fake_llm)

    tool = PolishTool()
    result = tool(draft="Needs polish", word_count=5)
    assert result["ok"]["under_limit"] is True
    assert result["error"] is None 