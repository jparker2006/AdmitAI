import json
from pathlib import Path

from essay_agent.memory import JSONConversationMemory


def test_memory_save_and_load(tmp_path):
    user_id = "unit_test_user"
    # Patch memory root to tmp_path
    from essay_agent import memory as mem_mod  # noqa: import-present

    mem_mod._MEMORY_ROOT = tmp_path  # type: ignore[attr-defined]

    mem = JSONConversationMemory(user_id=user_id)
    mem.save_context({"input": "Hello"}, {"output": "Hi"})

    # File should exist
    conv_path = tmp_path / f"{user_id}.conv.json"
    assert conv_path.exists()

    # Load new instance and ensure history preserved
    mem2 = JSONConversationMemory(user_id=user_id)
    vars = mem2.load_memory_variables({})
    assert len(vars["chat_history"]) == 2  # human + ai messages
    assert "Hello" in vars["summary"]

    # Clear and check file reset
    mem2.clear()
    data = json.loads(conv_path.read_text())
    assert data["chat_history"] == []
    assert data["summary"] == "" 