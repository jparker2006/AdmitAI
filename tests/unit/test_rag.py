import pytest
from langchain.llms.fake import FakeListLLM

from essay_agent.memory.hierarchical import HierarchicalMemory
from essay_agent.memory.user_profile_schema import CoreValue, UserProfile, UserInfo, AcademicProfile
from essay_agent.memory.rag import build_rag_chain


@pytest.fixture
def _profile(tmp_path, monkeypatch):
    monkeypatch.setattr("essay_agent.memory._MEMORY_ROOT", tmp_path, raising=False)
    info = UserInfo(name="Bob", grade=12, intended_major="History", college_list=[], platforms=[])
    acad = AcademicProfile(gpa=None, test_scores={}, courses=[], activities=[])
    cv = CoreValue(value="Leadership", description="Led the chess club", evidence=[], used_in_essays=[])
    profile = UserProfile(user_info=info, academic_profile=acad, core_values=[cv])
    mem = HierarchicalMemory("user_bob")
    mem.profile = profile
    mem.save()
    return mem


def _fake_llm():
    return FakeListLLM(responses=["Leadership is one of your standout qualities."])


def test_retrieval_relevance(_profile):
    chain = build_rag_chain("user_bob", _fake_llm(), _profile, top_k=1)
    docs = chain.retriever.get_relevant_documents("leadership")  # type: ignore[attr-defined]
    assert any("Leadership" in d.page_content for d in docs)


def test_chain_answer(_profile):
    chain = build_rag_chain("user_bob", _fake_llm(), _profile, top_k=1)
    resp = chain.invoke({"query": "Which of my values shows leadership?"})
    if isinstance(resp, dict):
        text = resp.get("result", "")
    else:
        text = str(resp)
    assert "Leadership" in text 