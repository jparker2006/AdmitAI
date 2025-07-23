import asyncio

import pytest

from essay_agent.intelligence.quality_engine import QualityEngine


@pytest.mark.asyncio
async def test_quality_engine_async_wrapper():
    qe = QualityEngine(offline=True)
    text = "This is a reasonably long draft with enough words to evaluate readability and vocabulary richness."
    sync_score = qe.score_draft(text)
    async_score = await qe.async_score_draft(text)
    assert abs(sync_score - async_score) < 1e-6


@pytest.mark.parametrize("text,expected_max", [
    ("Too short", 5.0),
    (" ", 0.0),
])
def test_quality_engine_edge_cases(text, expected_max):
    qe = QualityEngine(offline=True)
    score = qe.score_draft(text)
    assert score <= expected_max 