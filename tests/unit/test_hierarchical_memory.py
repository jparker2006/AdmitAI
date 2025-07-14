import pytest
from datetime import datetime

from essay_agent.memory.hierarchical import HierarchicalMemory
from essay_agent.memory.user_profile_schema import CoreValue, EssayRecord, EssayVersion


@pytest.fixture(autouse=True)
def _tmp_memory(monkeypatch, tmp_path):
    """Redirect memory_store to a temp dir so real data isn't touched."""

    monkeypatch.setattr("essay_agent.memory._MEMORY_ROOT", tmp_path, raising=False)


def _make_record() -> EssayRecord:
    ver = EssayVersion(
        version=1,
        timestamp=datetime.utcnow(),
        content="Draft text ...",
        word_count=600,
        used_stories=[],
    )
    return EssayRecord(
        prompt_id="p1",
        prompt_text="Describe a challenge",
        platform="CommonApp",
        versions=[ver],
        status="draft",
    )


def test_tier_isolation(tmp_path, monkeypatch):
    monkeypatch.setattr("essay_agent.memory._MEMORY_ROOT", tmp_path, raising=False)
    mem = HierarchicalMemory("user1")

    # Add chat turn -- should only affect conversation file, not profile json
    mem.add_chat_turn({"human": "Hi"}, {"ai": "Hello"})
    assert len(mem.profile.essay_history) == 0


def test_add_semantic_and_search(monkeypatch, tmp_path):
    monkeypatch.setattr("essay_agent.memory._MEMORY_ROOT", tmp_path, raising=False)

    mem = HierarchicalMemory("user2")
    cv = CoreValue(value="Resilience", description="", evidence=[], used_in_essays=[])
    mem.add_semantic_item(cv)
    mem.save()

    # Re-instantiate to be sure it persisted
    mem2 = HierarchicalMemory("user2")
    results = mem2.semantic_search("resilience")
    assert results and isinstance(results[0], CoreValue)
    assert results[0].value == "Resilience"


def test_consolidate_session_updates_profile(monkeypatch, tmp_path):
    monkeypatch.setattr("essay_agent.memory._MEMORY_ROOT", tmp_path, raising=False)

    mem = HierarchicalMemory("user3")
    record = _make_record()
    mem.consolidate_session(stories_used=["Debate Leap"], essay_record=record)

    # Reload and validate
    mem2 = HierarchicalMemory("user3")
    assert len(mem2.get_essay_history()) == 1
    latest_ver = mem2.get_essay_history()[0].versions[-1]
    assert "Debate Leap" in latest_ver.used_stories 