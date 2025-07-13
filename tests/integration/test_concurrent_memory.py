from concurrent.futures import ThreadPoolExecutor
import json

from essay_agent.memory import JSONConversationMemory


def test_concurrent_writes(tmp_path):
    user_id = "concurrent_user"
    # patch memory root
    from essay_agent import memory as mem_mod

    mem_mod._MEMORY_ROOT = tmp_path  # type: ignore[attr-defined]

    def worker(i: int):
        mem = JSONConversationMemory(user_id=user_id)
        mem.save_context({"input": f"hi {i}"}, {"output": f"yo {i}"})

    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(worker, range(20)))

    # verify
    conv_path = tmp_path / f"{user_id}.conv.json"
    data = json.loads(conv_path.read_text())
    # chat_history length should be 40 (20 inputs + 20 outputs)
    assert len(data["chat_history"]) == 40 