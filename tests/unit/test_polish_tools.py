"""test_polish_tools.py

Unit tests for essay_agent.tools.polish_tools

Tests all four polish and refinement tools:
- GrammarFixTool  
- VocabularyEnhancementTool
- ConsistencyCheckTool
- WordCountOptimizerTool
"""

from __future__ import annotations

import json
import pytest
from langchain.llms.fake import FakeListLLM

from essay_agent.tools.polish_tools import (
    GrammarFixTool,
    VocabularyEnhancementTool, 
    ConsistencyCheckTool,
    WordCountOptimizerTool,
    _count_words,
    _intelligent_trim_text,
)
from essay_agent.tools import REGISTRY
from essay_agent.prompts.polish import (
    GRAMMAR_FIX_PROMPT,
    VOCABULARY_ENHANCEMENT_PROMPT,
    CONSISTENCY_CHECK_PROMPT,
)

# ---------------------------------------------------------------------------
# Prompt Template Variable Tests
# ---------------------------------------------------------------------------

def test_grammar_fix_prompt_variables():
    """Test GrammarFixTool prompt has correct template variables."""
    assert "{essay_text}" in GRAMMAR_FIX_PROMPT.template

def test_vocabulary_enhancement_prompt_variables():
    """Test VocabularyEnhancementTool prompt has correct template variables."""
    assert "{essay_text}" in VOCABULARY_ENHANCEMENT_PROMPT.template

def test_consistency_check_prompt_variables():
    """Test ConsistencyCheckTool prompt has correct template variables."""
    assert "{essay_text}" in CONSISTENCY_CHECK_PROMPT.template

# ---------------------------------------------------------------------------
# Tool Integration Tests with Fake LLM
# ---------------------------------------------------------------------------

def test_grammar_fix_tool_offline(monkeypatch):
    """Test GrammarFixTool with fake LLM response."""
    fake_output = {
        "corrected_essay": "I struggled with mathematics throughout my sophomore year. However, I was determined to improve my grades through consistent practice and seeking help.",
        "corrections_made": [
            "Fixed subject-verb agreement in 2 sentences",
            "Corrected 3 spelling errors",
            "Improved punctuation in complex sentences"
        ],
        "voice_preservation_notes": "Maintained authentic student voice while correcting technical errors",
        "error_count": 5
    }
    
    fake_llm = FakeListLLM(responses=[json.dumps(fake_output)])
    monkeypatch.setattr("essay_agent.tools.polish_tools.get_chat_llm", lambda **_: fake_llm)
    
    tool = GrammarFixTool()
    result = tool(essay_text="I struggle with math throughout my sophmore year. However I was determined to improve my grade through consistent practise and seeking help.")
    
    assert "ok" in result
    assert result["ok"]["corrected_essay"] == fake_output["corrected_essay"]
    assert result["ok"]["error_count"] == 5
    assert len(result["ok"]["corrections_made"]) == 3

def test_vocabulary_enhancement_tool_offline(monkeypatch):
    """Test VocabularyEnhancementTool with fake LLM response."""
    fake_output = {
        "enhanced_essay": "I struggled with mathematics throughout my sophomore year. However, I was determined to enhance my performance through consistent practice and seeking assistance.",
        "vocabulary_changes": [
            {
                "original": "improve my grades",
                "enhanced": "enhance my performance", 
                "reason": "More precise and sophisticated while remaining natural"
            },
            {
                "original": "seeking help",
                "enhanced": "seeking assistance",
                "reason": "More formal but age-appropriate vocabulary choice"
            }
        ],
        "enhancement_summary": "Enhanced 2 vocabulary choices for greater precision and impact",
        "voice_preservation_confidence": "high",
        "total_enhancements": 2
    }
    
    fake_llm = FakeListLLM(responses=[json.dumps(fake_output)])
    monkeypatch.setattr("essay_agent.tools.polish_tools.get_chat_llm", lambda **_: fake_llm)
    
    tool = VocabularyEnhancementTool()
    result = tool(essay_text="I struggled with math throughout my sophomore year. However, I was determined to improve my grades through consistent practice and seeking help.")
    
    assert "ok" in result
    assert result["ok"]["total_enhancements"] == 2
    assert result["ok"]["voice_preservation_confidence"] == "high"
    assert len(result["ok"]["vocabulary_changes"]) == 2

def test_consistency_check_tool_offline(monkeypatch):
    """Test ConsistencyCheckTool with fake LLM response."""
    fake_output = {
        "consistency_report": {
            "overall_consistency_score": 7.5,
            "tense_consistency": "moderate",
            "voice_consistency": "strong", 
            "style_consistency": "strong",
            "total_issues_found": 2
        },
        "identified_issues": [
            {
                "issue_type": "tense_shift",
                "location": "paragraph 1, sentence 3",
                "description": "Unnecessary shift from past to present tense",
                "severity": "medium",
                "current_text": "I was studying when I realize",
                "recommended_fix": "I was studying when I realized"
            },
            {
                "issue_type": "voice_inconsistency", 
                "location": "paragraph 2, sentence 1",
                "description": "Shift to overly formal tone",
                "severity": "low",
                "current_text": "Subsequently, I endeavored to",
                "recommended_fix": "Next, I tried to"
            }
        ],
        "consistency_improvements": [
            "Maintain consistent past tense throughout narrative sections",
            "Keep voice natural and age-appropriate"
        ],
        "corrected_essay": "I struggled with mathematics throughout my sophomore year. However, I was determined to improve my grades. I was studying when I realized that I needed help.",
        "improvement_summary": "Fixed 2 consistency issues: 1 tense shift and 1 voice inconsistency"
    }
    
    fake_llm = FakeListLLM(responses=[json.dumps(fake_output)])
    monkeypatch.setattr("essay_agent.tools.polish_tools.get_chat_llm", lambda **_: fake_llm)
    
    tool = ConsistencyCheckTool()
    result = tool(essay_text="I struggled with math throughout my sophomore year. However, I was determined to improve my grades. I was studying when I realize that I needed help.")
    
    assert "ok" in result
    assert result["ok"]["consistency_report"]["overall_consistency_score"] == 7.5
    assert result["ok"]["consistency_report"]["total_issues_found"] == 2
    assert len(result["ok"]["identified_issues"]) == 2

def test_word_count_optimizer_tool_offline():
    """Test WordCountOptimizerTool (pure Python function)."""
    test_essay = """
    I have always been passionate about science and mathematics. Throughout my high school career, 
    I have consistently worked very hard to achieve excellent grades in all of my classes. 
    I am definitely excited about the opportunity to continue my education at your university.
    I believe that I will be able to contribute significantly to your academic community.
    """
    
    tool = WordCountOptimizerTool()
    result = tool(essay_text=test_essay, target_words=60)
    
    assert "ok" in result
    assert result["ok"]["target_word_count"] == 60
    assert result["ok"]["final_word_count"] <= 60
    assert result["ok"]["words_removed"] >= 0
    assert "optimization_notes" in result["ok"]

# ---------------------------------------------------------------------------
# Tool Registry Tests  
# ---------------------------------------------------------------------------

def test_grammar_fix_tool_registry():
    """Test GrammarFixTool is registered correctly."""
    assert "fix_grammar" in REGISTRY
    assert isinstance(REGISTRY["fix_grammar"], GrammarFixTool)

def test_vocabulary_enhancement_tool_registry():
    """Test VocabularyEnhancementTool is registered correctly."""
    assert "enhance_vocabulary" in REGISTRY
    assert isinstance(REGISTRY["enhance_vocabulary"], VocabularyEnhancementTool)

def test_consistency_check_tool_registry():
    """Test ConsistencyCheckTool is registered correctly."""
    assert "check_consistency" in REGISTRY
    assert isinstance(REGISTRY["check_consistency"], ConsistencyCheckTool)

def test_word_count_optimizer_tool_registry():
    """Test WordCountOptimizerTool is registered correctly."""
    assert "optimize_word_count" in REGISTRY
    assert isinstance(REGISTRY["optimize_word_count"], WordCountOptimizerTool)

# ---------------------------------------------------------------------------
# Input Validation Tests
# ---------------------------------------------------------------------------

def test_grammar_fix_tool_input_validation():
    """Test GrammarFixTool input validation."""
    tool = GrammarFixTool()
    
    # Empty text
    result = tool(essay_text="")
    assert "ok" in result
    assert "error" in result["ok"]
    assert "cannot be empty" in result["ok"]["error"]
    
    # Too short text
    result = tool(essay_text="Short")
    assert "ok" in result
    assert "error" in result["ok"]
    assert "at least 50 characters" in result["ok"]["error"]

def test_vocabulary_enhancement_tool_input_validation():
    """Test VocabularyEnhancementTool input validation.""" 
    tool = VocabularyEnhancementTool()
    
    # Empty text
    result = tool(essay_text="")
    assert "ok" in result
    assert "error" in result["ok"]
    assert "cannot be empty" in result["ok"]["error"]
    
    # Too short text
    result = tool(essay_text="Short")
    assert "ok" in result
    assert "error" in result["ok"]
    assert "at least 50 characters" in result["ok"]["error"]

def test_consistency_check_tool_input_validation():
    """Test ConsistencyCheckTool input validation."""
    tool = ConsistencyCheckTool()
    
    # Empty text
    result = tool(essay_text="")
    assert "ok" in result
    assert "error" in result["ok"]
    assert "cannot be empty" in result["ok"]["error"]
    
    # Too short text
    result = tool(essay_text="Short")
    assert "ok" in result
    assert "error" in result["ok"]
    assert "at least 50 characters" in result["ok"]["error"]

def test_word_count_optimizer_tool_input_validation():
    """Test WordCountOptimizerTool input validation."""
    tool = WordCountOptimizerTool()
    
    # Empty text
    result = tool(essay_text="", target_words=100)
    assert "ok" in result
    assert "error" in result["ok"]
    assert "cannot be empty" in result["ok"]["error"]
    
    # Invalid target_words
    result = tool(essay_text="This is a test essay with enough words to pass validation.", target_words="invalid")
    assert "ok" in result
    assert "error" in result["ok"]
    assert "must be a valid integer" in result["ok"]["error"]
    
    # Target words too small
    result = tool(essay_text="This is a test essay with enough words to pass validation.", target_words=10)
    assert "ok" in result
    assert "error" in result["ok"]
    assert "at least 50" in result["ok"]["error"]
    
    # Target words too large
    result = tool(essay_text="This is a test essay with enough words to pass validation.", target_words=3000)
    assert "ok" in result
    assert "error" in result["ok"]
    assert "cannot exceed 2000" in result["ok"]["error"]

# ---------------------------------------------------------------------------
# Helper Function Tests
# ---------------------------------------------------------------------------

def test_count_words():
    """Test _count_words helper function."""
    assert _count_words("") == 0
    assert _count_words("   ") == 0
    assert _count_words("hello") == 1
    assert _count_words("hello world") == 2
    assert _count_words("  hello   world  ") == 2
    assert _count_words("The quick brown fox jumps over the lazy dog.") == 9

def test_intelligent_trim_text():
    """Test _intelligent_trim_text helper function."""
    text = "I am very really quite excited about this absolutely amazing opportunity."
    
    # Test filler word removal
    result = _intelligent_trim_text(text, 8, preserve_meaning=True)
    word_count = _count_words(result)
    assert word_count <= 8
    
    # Test that filler words are removed first
    assert "very" not in result or "really" not in result or "quite" not in result
    
    # Test simple truncation
    result = _intelligent_trim_text(text, 5, preserve_meaning=False)
    assert _count_words(result) == 5

def test_intelligent_trim_text_edge_cases():
    """Test _intelligent_trim_text edge cases."""
    text = "Short text."
    
    # Text already at target
    result = _intelligent_trim_text(text, 2, preserve_meaning=True)
    assert result == text
    
    # Text under target
    result = _intelligent_trim_text(text, 5, preserve_meaning=True)
    assert result == text

# ---------------------------------------------------------------------------
# Tool Name and Description Tests
# ---------------------------------------------------------------------------

def test_all_tools_have_correct_names():
    """Test all tools have correct names."""
    grammar_tool = GrammarFixTool()
    vocab_tool = VocabularyEnhancementTool() 
    consistency_tool = ConsistencyCheckTool()
    word_count_tool = WordCountOptimizerTool()
    
    assert grammar_tool.name == "fix_grammar"
    assert vocab_tool.name == "enhance_vocabulary"
    assert consistency_tool.name == "check_consistency"
    assert word_count_tool.name == "optimize_word_count"

def test_all_tools_have_descriptions():
    """Test all tools have non-empty descriptions."""
    grammar_tool = GrammarFixTool()
    vocab_tool = VocabularyEnhancementTool()
    consistency_tool = ConsistencyCheckTool()
    word_count_tool = WordCountOptimizerTool()
    
    assert grammar_tool.description
    assert vocab_tool.description
    assert consistency_tool.description
    assert word_count_tool.description
    
    # Check descriptions contain key terms
    assert "grammar" in grammar_tool.description.lower()
    assert "vocabulary" in vocab_tool.description.lower()
    assert "consistency" in consistency_tool.description.lower()
    assert "word count" in word_count_tool.description.lower()

# ---------------------------------------------------------------------------
# Integration Tests
# ---------------------------------------------------------------------------

def test_all_polish_tools_in_registry():
    """Test all polish tools are properly registered."""
    expected_tools = [
        "fix_grammar",
        "enhance_vocabulary", 
        "check_consistency",
        "optimize_word_count"
    ]
    
    for tool_name in expected_tools:
        assert tool_name in REGISTRY, f"Tool {tool_name} not found in registry"
        
    # Verify tool types
    assert isinstance(REGISTRY["fix_grammar"], GrammarFixTool)
    assert isinstance(REGISTRY["enhance_vocabulary"], VocabularyEnhancementTool)
    assert isinstance(REGISTRY["check_consistency"], ConsistencyCheckTool)
    assert isinstance(REGISTRY["optimize_word_count"], WordCountOptimizerTool) 