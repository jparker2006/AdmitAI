import pytest
from pydantic import ValidationError

from essay_agent.models import (
    EssayPrompt,
    EssayDraft,
    EssayFeedback,
    UserProfile,
)


def test_essay_prompt_valid():
    prompt = EssayPrompt(text="Describe a challenge you overcame.", word_limit=650)
    assert prompt.word_limit == 650
    assert prompt.text.startswith("Describe")


@pytest.mark.parametrize("invalid_text", ["", "   "])
def test_essay_prompt_invalid_text(invalid_text):
    with pytest.raises(ValidationError):
        EssayPrompt(text=invalid_text, word_limit=300)


def test_essay_prompt_word_limit_bounds():
    with pytest.raises(ValidationError):
        EssayPrompt(text="Prompt", word_limit=5)  # below min 10
    with pytest.raises(ValidationError):
        EssayPrompt(text="Prompt", word_limit=2000)  # above max 1000


def test_essay_feedback_score_bounds():
    # valid score
    EssayFeedback(comments="Nice work!", score={"clarity": 8, "voice": 7})

    # out-of-range score triggers error
    with pytest.raises(ValidationError):
        EssayFeedback(comments="Bad", score={"clarity": 11})


def test_essay_draft_round_trip():
    prompt = EssayPrompt(text="Tell us about a lesson learned.")
    draft = EssayDraft(prompt=prompt, draft_text="I learned a lot from ...")

    dumped = draft.model_dump()
    restored = EssayDraft.model_validate(dumped)

    assert restored == draft


def test_user_profile_import():
    # Smoke-test that alias works and can be instantiated via existing schema
    info = {
        "user_info": {
            "name": "Test",
            "grade": 12,
            "intended_major": "CS",
            "college_list": ["X University"],
            "platforms": [],
        },
        "academic_profile": {
            "gpa": 3.8,
            "test_scores": {"SAT": 1500},
            "courses": [],
            "activities": [],
        },
        "core_values": [],
    }

    profile = UserProfile(**info)
    assert profile.user_info.name == "Test" 