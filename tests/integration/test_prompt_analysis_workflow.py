"""Integration test for prompt analysis tools working together.

This test demonstrates how the four prompt analysis tools can be used
together in a realistic essay planning workflow.
"""

import json
import pytest
from langchain.llms.fake import FakeListLLM

from essay_agent.tools import REGISTRY


def test_prompt_analysis_workflow(monkeypatch):
    """Test complete prompt analysis workflow with all four tools."""
    
    # Mock LLM responses for each tool
    classify_response = {
        "theme": "challenge",
        "confidence": 0.9,
        "rationale": "Directly asks about challenging beliefs, core challenge theme"
    }
    
    extract_response = {
        "word_limit": 650,
        "key_questions": ["What challenge did you overcome?", "What did you learn?"],
        "evaluation_criteria": ["problem-solving", "resilience", "self-reflection", "growth mindset"]
    }
    
    strategy_response = {
        "overall_strategy": "Focus on a specific debate loss that taught resilience. Use immigrant perspective to show unique challenges. Structure: setup stakes, describe failure moment, analyze what went wrong, demonstrate growth through specific actions taken afterward.",
        "recommended_story_traits": ["cultural perspective", "leadership under pressure", "analytical thinking", "resilience"],
        "potential_pitfalls": ["avoid generic 'failure made me stronger'", "don't blame others", "avoid victim narrative", "ensure clear lesson learned"]
    }
    
    overlap_response = {
        "overlaps_found": True,
        "overlap_score": 0.7,
        "conflicting_essays": [1]
    }
    
    # Mock the LLM with sequential responses
    fake_llm = FakeListLLM(responses=[
        json.dumps(classify_response),
        json.dumps(extract_response),
        json.dumps(strategy_response),
        json.dumps(overlap_response)
    ])
    
    # Patch all tools to use the fake LLM
    monkeypatch.setattr("essay_agent.tools.prompt_tools.get_chat_llm", lambda **_: fake_llm)
    
    # Test data
    essay_prompt = "Describe a time you challenged a belief or idea."
    user_profile = "Debate team captain, immigrant family, interested in social justice"
    story_idea = "Challenging traditional gender roles in debate"
    previous_essays = ["Soccer injury recovery", "Debate championship win"]
    
    # Step 1: Classify the prompt
    classify_result = REGISTRY.call("classify_prompt", essay_prompt=essay_prompt)
    assert classify_result["ok"]["theme"] == "challenge"
    assert classify_result["ok"]["confidence"] == 0.9
    
    # Step 2: Extract requirements
    extract_result = REGISTRY.call("extract_requirements", essay_prompt=essay_prompt)
    assert extract_result["ok"]["word_limit"] == 650
    assert len(extract_result["ok"]["key_questions"]) == 2
    assert "problem-solving" in extract_result["ok"]["evaluation_criteria"]
    
    # Step 3: Suggest strategy based on prompt and profile
    strategy_result = REGISTRY.call(
        "suggest_strategy", 
        essay_prompt=essay_prompt, 
        profile=user_profile
    )
    assert "debate" in strategy_result["ok"]["overall_strategy"]
    assert "cultural perspective" in strategy_result["ok"]["recommended_story_traits"]
    assert len(strategy_result["ok"]["potential_pitfalls"]) >= 2
    
    # Step 4: Check for overlap with previous essays
    overlap_result = REGISTRY.call(
        "detect_overlap",
        story=story_idea,
        previous_essays=previous_essays
    )
    assert overlap_result["ok"]["overlaps_found"] is True
    assert overlap_result["ok"]["overlap_score"] == 0.7
    assert overlap_result["ok"]["conflicting_essays"] == [1]
    
    # Verify all tools returned successful results
    assert all(result["error"] is None for result in [
        classify_result, extract_result, strategy_result, overlap_result
    ])
    
    print("✅ Complete prompt analysis workflow executed successfully!")


def test_prompt_analysis_workflow_realistic_scenario(monkeypatch):
    """Test with a more realistic scenario showing how tools complement each other."""
    
    # Realistic responses for a leadership prompt
    classify_response = {
        "theme": "leadership",
        "confidence": 0.85,
        "rationale": "Focuses on leadership experience and impact on others"
    }
    
    extract_response = {
        "word_limit": 500,
        "key_questions": ["What leadership role did you take?", "How did you impact others?"],
        "evaluation_criteria": ["leadership potential", "impact on community", "initiative", "teamwork"]
    }
    
    strategy_response = {
        "overall_strategy": "Choose a specific leadership moment where you initiated change. Show concrete impact on your team or community. Use active voice and specific examples.",
        "recommended_story_traits": ["initiative", "team building", "problem-solving"],
        "potential_pitfalls": ["avoid generic leadership clichés", "don't just list accomplishments", "show vulnerability"]
    }
    
    overlap_response = {
        "overlaps_found": False,
        "overlap_score": 0.2,
        "conflicting_essays": []
    }
    
    fake_llm = FakeListLLM(responses=[
        json.dumps(classify_response),
        json.dumps(extract_response),
        json.dumps(strategy_response),
        json.dumps(overlap_response)
    ])
    
    monkeypatch.setattr("essay_agent.tools.prompt_tools.get_chat_llm", lambda **_: fake_llm)
    
    # Test with leadership prompt
    essay_prompt = "Describe a time when you took initiative to solve a problem."
    user_profile = "Student council president, started environmental club, organized fundraisers"
    story_idea = "Starting school recycling program"
    previous_essays = ["Volunteer work at animal shelter", "Learning to code"]
    
    # Run the workflow
    classify_result = REGISTRY.call("classify_prompt", essay_prompt=essay_prompt)
    extract_result = REGISTRY.call("extract_requirements", essay_prompt=essay_prompt)
    strategy_result = REGISTRY.call("suggest_strategy", essay_prompt=essay_prompt, profile=user_profile)
    overlap_result = REGISTRY.call("detect_overlap", story=story_idea, previous_essays=previous_essays)
    
    # Verify results make sense for leadership theme
    assert classify_result["ok"]["theme"] == "leadership"
    assert extract_result["ok"]["word_limit"] == 500
    assert "initiative" in strategy_result["ok"]["recommended_story_traits"]
    assert overlap_result["ok"]["overlaps_found"] is False
    
    print("✅ Realistic leadership scenario workflow completed successfully!")


if __name__ == "__main__":
    # Run a quick demo
    print("Running prompt analysis workflow demo...")
    test_prompt_analysis_workflow(lambda x, y: None)
    test_prompt_analysis_workflow_realistic_scenario(lambda x, y: None) 