import json

import pytest
from langchain.llms.fake import FakeListLLM

from essay_agent.tools.writing_tools import (
    OutlineExpansionTool,
    ParagraphRewriteTool,
    OpeningImprovementTool,
    VoiceStrengtheningTool,
)
from essay_agent.prompts.writing import (
    OUTLINE_EXPANSION_PROMPT,
    PARAGRAPH_REWRITE_PROMPT,
    OPENING_IMPROVEMENT_PROMPT,
    VOICE_STRENGTHENING_PROMPT,
)
from essay_agent.tools import REGISTRY


# ---------------------------------------------------------------------------
# Prompt variable tests
# ---------------------------------------------------------------------------

def test_outline_expansion_prompt_variables():
    required = {"outline_section", "section_name", "voice_profile", "target_words", "today"}
    assert required.issubset(set(OUTLINE_EXPANSION_PROMPT.input_variables))


def test_paragraph_rewrite_prompt_variables():
    required = {"paragraph", "style_instruction", "voice_profile", "today"}
    assert required.issubset(set(PARAGRAPH_REWRITE_PROMPT.input_variables))


def test_opening_improvement_prompt_variables():
    required = {"opening_sentence", "essay_context", "voice_profile", "today"}
    assert required.issubset(set(OPENING_IMPROVEMENT_PROMPT.input_variables))


def test_voice_strengthening_prompt_variables():
    required = {"paragraph", "voice_profile", "target_voice_traits", "today"}
    assert required.issubset(set(VOICE_STRENGTHENING_PROMPT.input_variables))


# ---------------------------------------------------------------------------
# Tool success path tests
# ---------------------------------------------------------------------------


def _patch_fake_llm(monkeypatch, fake_output):
    fake_llm = FakeListLLM(responses=[json.dumps(fake_output)])
    monkeypatch.setattr("essay_agent.tools.writing_tools.get_chat_llm", lambda **_: fake_llm)


def test_outline_expansion_tool_success(monkeypatch):
    fake_output = {"expanded_paragraph": "This is an expanded paragraph."}
    _patch_fake_llm(monkeypatch, fake_output)
    tool = OutlineExpansionTool()
    result = tool(
        outline_section="Point A; Point B",
        section_name="conflict",
        voice_profile="conversational",
        target_words=120,
    )
    assert result["error"] is None
    assert result["ok"]["expanded_paragraph"] == fake_output["expanded_paragraph"]


def test_paragraph_rewrite_tool_success(monkeypatch):
    fake_output = {"rewritten_paragraph": "Rewritten paragraph."}
    _patch_fake_llm(monkeypatch, fake_output)
    tool = ParagraphRewriteTool()
    result = tool(
        paragraph="Old paragraph.",
        style_instruction="make it more vivid",
        voice_profile="friendly",
    )
    assert result["error"] is None
    assert result["ok"]["rewritten_paragraph"] == fake_output["rewritten_paragraph"]


def test_opening_improvement_tool_success(monkeypatch):
    fake_output = {"improved_opening": "Improved opening sentence."}
    _patch_fake_llm(monkeypatch, fake_output)
    tool = OpeningImprovementTool()
    result = tool(
        opening_sentence="It was a bright day.",
        essay_context="Story about overcoming fear",
        voice_profile="reflective",
    )
    assert result["error"] is None
    assert result["ok"]["improved_opening"] == fake_output["improved_opening"]


def test_voice_strengthening_tool_success(monkeypatch):
    fake_output = {"voice_adjusted_paragraph": "Voice adjusted paragraph."}
    _patch_fake_llm(monkeypatch, fake_output)
    tool = VoiceStrengtheningTool()
    result = tool(
        paragraph="Generic paragraph.",
        voice_profile="humorous",
        target_voice_traits="witty, energetic",
    )
    assert result["error"] is None
    assert result["ok"]["voice_adjusted_paragraph"] == fake_output["voice_adjusted_paragraph"]


# ---------------------------------------------------------------------------
# Registry tests
# ---------------------------------------------------------------------------

def test_writing_tools_registry():
    assert "expand_outline_section" in REGISTRY
    assert "rewrite_paragraph" in REGISTRY
    assert "improve_opening" in REGISTRY
    assert "strengthen_voice" in REGISTRY 