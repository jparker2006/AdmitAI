import pytest
from essay_agent.memory.context_manager import ContextWindowManager


def _make_cm(tmp_path, essay="essay1", max_tokens=50):
    cm = ContextWindowManager("u1", essay_id=essay, max_tokens=max_tokens, summary_max_tokens=20, storage_dir=tmp_path)
    return cm


@pytest.fixture(autouse=True)
def _iso(monkeypatch, tmp_path):
    monkeypatch.setattr("essay_agent.memory.context_manager.DEFAULT_DIR", tmp_path, raising=False)


def test_truncation(monkeypatch, tmp_path):
    cm = _make_cm(tmp_path)
    # Add many short messages
    for i in range(30):
        cm.add_user(f"hello {i}")
        cm.add_ai("ok")
    assert cm.token_count <= cm.max_tokens
    # Summary should hold earlier content
    assert cm.summary


def test_session_switch(tmp_path):
    cm = _make_cm(tmp_path, essay="e1")
    cm.add_user("first essay message")
    cm.switch_session("e2")
    assert not cm.messages  # new session empty
    cm.add_ai("hi e2")
    # Reload manager and confirm isolation
    cm2 = ContextWindowManager("u1", essay_id="e1", storage_dir=tmp_path)
    assert any("first essay" in m["content"] for m in cm2.messages)
    cm3 = ContextWindowManager("u1", essay_id="e2", storage_dir=tmp_path)
    assert any("hi e2" in m["content"] for m in cm3.messages) 