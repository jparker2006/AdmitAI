import pytest

from essay_agent.memory.semantic_search import SemanticSearchIndex
from essay_agent.memory.user_profile_schema import (
    CoreValue,
    AcademicProfile,
    UserInfo,
    UserProfile,
)


@pytest.fixture(autouse=True)
def _tmp_memory(monkeypatch, tmp_path):
    """Redirect memory_store & vector index dir to temp folder so tests are isolated."""

    monkeypatch.setattr("essay_agent.memory._MEMORY_ROOT", tmp_path, raising=False)


def _make_profile() -> UserProfile:  # noqa: D401
    info = UserInfo(name="Alice", grade=11, intended_major="CS", college_list=[], platforms=[])
    acad = AcademicProfile(gpa=None, test_scores={}, courses=[], activities=[])
    cv1 = CoreValue(value="Leadership", description="Leading team projects", evidence=[], used_in_essays=[])
    cv2 = CoreValue(value="Resilience", description="Overcame challenges", evidence=[], used_in_essays=[])
    return UserProfile(user_info=info, academic_profile=acad, core_values=[cv1, cv2])


def test_build_and_search(tmp_path, monkeypatch):
    monkeypatch.setattr("essay_agent.memory._MEMORY_ROOT", tmp_path, raising=False)

    profile = _make_profile()
    idx = SemanticSearchIndex.load_or_build("user1", profile)

    # Basic search should retrieve the Leadership value
    results = idx.search("leader", k=2)
    assert results, "Search returned empty list"
    assert any(isinstance(r, CoreValue) and r.value == "Leadership" for r in results)


def test_offline_fallback(monkeypatch, tmp_path):
    monkeypatch.setattr("essay_agent.memory._MEMORY_ROOT", tmp_path, raising=False)

    # Ensure no OpenAI key in env so fallback embedding used
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    profile = _make_profile()
    idx = SemanticSearchIndex.load_or_build("user2", profile)
    results = idx.search("resilience", k=2)
    assert results and results[0].value.lower() == "resilience" 