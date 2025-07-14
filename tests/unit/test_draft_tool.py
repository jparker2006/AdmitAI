import json

import pytest
from langchain.llms.fake import FakeListLLM

from essay_agent.tools.draft import DraftTool
from essay_agent.prompts.draft import DRAFT_PROMPT


def test_prompt_placeholders():
    # Updated to reflect separated concerns - word_count is no longer in main draft prompt
    required_vars = {"outline", "voice_profile"}
    assert required_vars.issubset(set(DRAFT_PROMPT.input_variables))


def test_draft_tool_success(monkeypatch):
    fake_response = json.dumps({"draft": "My essay"})
    fake_llm = FakeListLLM(responses=[fake_response])
    # Patch llm factory to return our fake
    monkeypatch.setattr("essay_agent.tools.draft.get_chat_llm", lambda **_: fake_llm)

    tool = DraftTool()
    outline = {
        "hook": "test",
        "context": "...",
        "conflict": "...",
        "growth": "...",
        "reflection": "...",
    }

    out = tool(outline=outline, voice_profile="conversational", word_count=650)
    assert out["error"] is None
    assert out["ok"]["draft"] == "My essay"


def test_draft_tool_parse_error(monkeypatch):
    fake_llm = FakeListLLM(responses=["NOT JSON"])
    monkeypatch.setattr("essay_agent.tools.draft.get_chat_llm", lambda **_: fake_llm)

    tool = DraftTool()
    outline = {"hook": "x", "context": "y"}
    result = tool(outline=outline, voice_profile="plain", word_count=100)

    assert result["ok"] is None
    assert result["error"] is not None 