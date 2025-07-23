from essay_agent.intelligence.quality_engine import QualityEngine
from essay_agent.tools import register_tool


def test_heuristic_scoring():
    qi = QualityEngine(offline=True)
    score = qi.score_draft("This is a very short draft.")
    assert 0 <= score <= 10


def test_tool_scoring(monkeypatch):
    # register dummy essay_scoring tool
    @register_tool("essay_scoring")
    def _dummy_essay_score(*, draft: str, user_id: str, profile: dict):
        """Return fixed high score for testing."""
        return {"overall_score": 9.2}

    qi = QualityEngine(offline=False)
    score = qi.score_draft("Sample draft")
    assert abs(score - 9.2) < 0.01 