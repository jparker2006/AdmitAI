from datetime import datetime

import pytest
from pydantic import ValidationError

from essay_agent.memory.user_profile_schema import (
    DefiningMoment,
    WritingVoice,
    EssayVersion,
    EssayRecord,
    UserProfile,
    UserInfo,
    AcademicProfile,
    CoreValue,
    Activity,
)


def _minimal_user_profile():
    return UserProfile(
        user_info=UserInfo(
            name="Test", grade=12, intended_major="CS", college_list=["X"], platforms=[]
        ),
        academic_profile=AcademicProfile(
            gpa=3.9, test_scores={}, courses=[], activities=[]
        ),
        core_values=[],
    )


def test_user_profile_with_new_fields():
    profile = _minimal_user_profile()
    profile.defining_moments.append(
        DefiningMoment(
            title="Move", description="moved", emotional_impact="big", lessons_learned="many"
        )
    )
    profile.writing_voice = WritingVoice(
        tone_preferences=["conversational"], vocabulary_level="college", sentence_patterns=[], stylistic_traits=[]
    )
    assert profile.defining_moments[0].title == "Move"


def test_essay_version_validation():
    version = EssayVersion(
        version=1,
        timestamp=datetime.utcnow(),
        content="test",
        word_count=4,
    )
    record = EssayRecord(
        prompt_id="1", prompt_text="Why?", platform="CommonApp", versions=[version], status="draft"
    )
    profile = _minimal_user_profile()
    profile.essay_history.append(record)
    assert profile.essay_history[0].versions[0].word_count == 4 