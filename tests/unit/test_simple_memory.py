import json
import threading

import pytest

from datetime import datetime

from essay_agent.memory.simple_memory import SimpleMemory, is_story_reused
from essay_agent.memory.user_profile_schema import EssayRecord, EssayVersion


@pytest.fixture(autouse=True)
def _tmp_memory(monkeypatch, tmp_path):
    # Redirect memory_store to temp dir to avoid clobbering real data
    monkeypatch.setattr("essay_agent.memory._MEMORY_ROOT", tmp_path, raising=False)


def test_roundtrip_profile():
    mem = SimpleMemory()
    profile = mem.load("bob")
    profile.user_info.name = "Bob"
    mem.save("bob", profile)

    loaded = mem.load("bob")
    assert loaded.user_info.name == "Bob"


def test_story_reuse_same_college():
    mem = SimpleMemory()
    user = "alice"
    record = EssayRecord(
        prompt_id="1",
        prompt_text="Prompt",
        platform="Harvard",
        status="draft",
        versions=[
            EssayVersion(
                version=1,
                timestamp=datetime.utcnow(),
                content="",
                word_count=100,
                used_stories=["Debate Leap"],
            )
        ],
    )
    mem.add_essay_record(user, record)

    assert is_story_reused(user, story_title="Debate Leap", college="Harvard") is True
    # Different college should be allowed
    assert is_story_reused(user, story_title="Debate Leap", college="Yale") is False


def test_concurrent_write(tmp_path, monkeypatch):
    monkeypatch.setattr("essay_agent.memory._MEMORY_ROOT", tmp_path, raising=False)
    mem = SimpleMemory()

    def _write(idx):
        p = mem.load("charlie")
        p.user_info.name = f"Charlie {idx}"
        mem.save("charlie", p)

    threads = [threading.Thread(target=_write, args=(i,)) for i in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    final_name = mem.load("charlie").user_info.name
    # Name should be one of the thread-written values; file not corrupted
    assert final_name.startswith("Charlie ") 


import pytest, os

from essay_agent.memory.simple_memory import SimpleMemory
from essay_agent.memory.user_profile_schema import UserProfile, UserInfo, AcademicProfile


def _empty_profile():
    return UserProfile(user_info=UserInfo(name="", grade=0, intended_major="", college_list=[], platforms=[]),
                       academic_profile=AcademicProfile(gpa=None, test_scores={}, courses=[], activities=[]),
                       core_values=[])


def test_extra_persistence(tmp_path, monkeypatch):
    monkeypatch.setattr("essay_agent.memory._MEMORY_ROOT", tmp_path, raising=False)

    uid = "extra_test_user"
    prof = _empty_profile()
    # Inject extras using both containers
    object.__setattr__(prof, "model_extra", {"essay_prompt": "Prompt"})  # type: ignore[attr-defined]
    object.__setattr__(prof, "__pydantic_extra__", {"college": "Harvard"})

    SimpleMemory.save(uid, prof)

    prof2 = SimpleMemory.load(uid)
    extra = getattr(prof2, "model_extra", {}) or {}
    assert extra.get("essay_prompt") == "Prompt"
    # During load, v2 extras merge into model_extra
    assert extra.get("college") == "Harvard"


def test_cli_roundtrip(tmp_path, monkeypatch):  # noqa: D401
    """Simulate CLI storing extras and ensure reload keeps them."""
    monkeypatch.setattr("essay_agent.memory._MEMORY_ROOT", tmp_path, raising=False)
    uid = "cli_round_user"
    from essay_agent.memory.smart_memory import SmartMemory
    mem = SmartMemory(uid)
    mem.set("essay_prompt", "Prompt text")
    mem.set("college", "Stanford")

    # Fresh instance should read both values
    mem2 = SmartMemory(uid)
    assert mem2.get("college") == "Stanford"
    assert mem2.get("essay_prompt") == "Prompt text"


# ---------------------------------------------------------------------------
# Regression test for issue #prompt-loss – ensure extras survive multiple
# load→save cycles (brand-new profile → set extras → reload → save → reload).
# ---------------------------------------------------------------------------


def test_prompt_roundtrip(tmp_path, monkeypatch):  # noqa: D401
    """Extras set during onboarding must persist through subsequent saves."""

    monkeypatch.setattr("essay_agent.memory._MEMORY_ROOT", tmp_path, raising=False)

    uid = "tmp_user"
    from essay_agent.memory.smart_memory import SmartMemory

    # Initial onboarding writes prompt + college ---------------------------
    mem = SmartMemory(uid)
    mem.set("essay_prompt", "Prompt")
    mem.set("college", "MIT")

    # Simulate agent turn that loads profile, writes something else and saves
    mem2 = SmartMemory(uid)
    # Example preference update triggers save internally
    mem2.preferences["tone"] = "casual"
    mem2.save()

    # Third load should still see original extras -------------------------
    mem3 = SmartMemory(uid)
    assert mem3.get("essay_prompt") == "Prompt"
    assert mem3.get("college") == "MIT" 