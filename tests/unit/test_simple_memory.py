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