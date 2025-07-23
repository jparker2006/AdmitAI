import pytest
from essay_agent.memory.smart_memory import SmartMemory


def test_preference_learning(tmp_path, monkeypatch):
    user_id = "pref_test_user"
    mem = SmartMemory(user_id)

    turn = {"user_input": "I prefer a casual tone and about 600 words.", "tool_result": {}}
    mem.learn(turn)
    assert mem.preferences["tone"] == "casual"
    assert mem.preferences["preferred_word_count"] == 600


def test_extra_storage_cross_version(tmp_path, monkeypatch):
    monkeypatch.setattr("essay_agent.memory._MEMORY_ROOT", tmp_path, raising=False)
    mem = SmartMemory("xversion")
    mem.set("essay_prompt", "Prompt text")
    # Reload new instance -> should read the same extra regardless of attr storage
    mem2 = SmartMemory("xversion")
    assert mem2.get("essay_prompt") == "Prompt text"


def test_tool_stats(tmp_path):
    user_id = "stat_user"
    mem = SmartMemory(user_id)
    turn = {"tool_result": {"tool_name": "brainstorm", "error": None}}
    mem.learn(turn)
    assert mem.tool_stats["brainstorm"]["usage_count"] >= 1
    assert mem.tool_stats["brainstorm"]["success_count"] >= 1 