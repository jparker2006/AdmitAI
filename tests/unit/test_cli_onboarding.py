import sys, importlib, os
from pathlib import Path
from essay_agent.memory.simple_memory import SimpleMemory
from essay_agent.utils.prompt_validator import validate_prompt_len


def test_prompt_validator_ok():
    validate_prompt_len("word " * 650)


def test_prompt_validator_fail():
    import pytest
    with pytest.raises(ValueError):
        validate_prompt_len("word " * 651)


def test_onboard_script(monkeypatch):
    monkeypatch.setenv("ESSAY_AGENT_OFFLINE_TEST", "1")
    user_id = "pytest_onboard2"
    memory_file = Path("memory_store") / f"{user_id}.json"
    if memory_file.exists():
        memory_file.unlink()

    sys.argv = ["essay-agent.onboard", "--user", user_id, "--college", "Stanford", "--essay-prompt", "Identity prompt"]
    import essay_agent.onboard as onboard
    importlib.reload(onboard)

    profile = SimpleMemory.load(user_id)
    meta = getattr(profile, "model_extra", {})
    assert meta.get("college") == "Stanford"
    assert "Identity" in meta.get("essay_prompt", "") 