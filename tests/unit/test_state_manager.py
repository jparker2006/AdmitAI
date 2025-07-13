from pathlib import Path

import pytest

from essay_agent.state_manager import ConversationStateManager


@pytest.fixture()
def temp_storage(tmp_path: Path):
    """Provide isolated directory for persistence tests."""

    return tmp_path


def test_add_and_retrieve(temp_storage):
    mgr = ConversationStateManager("u1", storage_dir=temp_storage, max_tokens=1000)
    mgr.add_user("Hello")
    mgr.add_ai("Hi there!")

    assert mgr.messages[0]["role"] == "user"
    assert mgr.messages[1]["role"] == "ai"
    assert mgr.context_messages()[0].content == "Hello"
    assert mgr.token_count > 0


def test_truncation(temp_storage):
    # small max_tokens to force truncation
    mgr = ConversationStateManager("u2", storage_dir=temp_storage, max_tokens=10)
    long_text = "A" * 50
    mgr.add_user(long_text)
    mgr.add_ai(long_text)

    # After truncation budget should be respected
    assert mgr.token_count <= mgr.max_tokens


def test_persistence(temp_storage):
    user_id = "u3"
    mgr = ConversationStateManager(user_id, storage_dir=temp_storage)
    mgr.add_user("One")
    mgr.add_ai("Two")

    # Reload
    mgr2 = ConversationStateManager.load(user_id, storage_dir=temp_storage)
    assert mgr2.messages == mgr.messages 