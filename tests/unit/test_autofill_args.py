import pytest
from essay_agent.utils.default_args import autofill_args

def _ctx():
    return {
        "recent_chat": ["Hello"],
        "outline": {"hook": "..."},
    }

class DummyMem:
    essay_prompt = "Describe a challenge"
    preferences = {"preferred_word_count": 650}
    user_profile = type("X", (), {"model_dump": lambda self: {"dummy": True}})()
    def get(self, k, d=""):
        return getattr(self, k, d)

def test_clarify_autofill():
    step = {"tool": "clarify", "args": {"question": "Q?"}}
    filled = autofill_args(step, _ctx(), DummyMem)
    assert filled.get("user_input") == "Hello"

def test_outline_generator_autofill():
    step = {"tool": "outline_generator", "args": {}}
    filled = autofill_args(step, _ctx(), DummyMem)
    assert filled["essay_prompt"] == "Describe a challenge"


def test_outline_generator_story_idea_autofill():
    step = {"tool": "outline_generator", "args": {"story_idea": "Conquering Fear"}}
    filled = autofill_args(step, _ctx(), DummyMem)
    assert filled["story"] == "Conquering Fear"
    assert filled["essay_prompt"] == "Describe a challenge"


def test_expand_outline_section_autofill():
    step = {"tool": "expand_outline_section", "args": {}}
    ctx = {"outline": {"hook": "Intro text"}, "recent_chat": ["Hi"]}
    filled = autofill_args(step, ctx, DummyMem)
    assert filled["section_name"] == "hook"
    assert filled["outline_section"] == "Intro text"


def test_length_optimizer_autofill():
    step = {"tool": "length_optimizer", "args": {}}
    filled = autofill_args(step, _ctx(), DummyMem)
    assert filled["target_word_count"] == 650
    assert "outline" in filled 