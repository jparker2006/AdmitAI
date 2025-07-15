"""Test for polish tool display bug fix

This test verifies that the polish tool results are properly displayed to users
after fixing the key mismatch between 'final_draft' and 'polished_draft'.
"""

import pytest
from dataclasses import dataclass
from essay_agent.conversation import NaturalResponseGenerator
from essay_agent.planner import EssayPlan, Phase


@dataclass
class MockToolResult:
    """Mock tool execution result for testing"""
    tool_name: str
    result: dict
    execution_time: float = 5.0


def test_polish_tool_display_with_final_draft_key():
    """Test that polish tool results with 'final_draft' key are properly displayed"""
    generator = NaturalResponseGenerator()
    
    # Mock polish tool result with 'final_draft' key (actual format)
    polish_result = MockToolResult(
        tool_name='polish',
        result={
            'ok': {
                'final_draft': 'This is a polished essay with excellent grammar and style.',
                'over_limit': False,
                'under_limit': False,
                'message': None
            },
            'error': None
        }
    )
    
    # Generate formatted response
    formatted_response = generator._format_successful_tool_result(polish_result)
    
    # Verify the essay content is displayed
    assert "Essay Polished:" in formatted_response
    assert "This is a polished essay with excellent grammar and style." in formatted_response
    assert "ready for submission" in formatted_response
    

def test_polish_tool_display_with_polished_draft_key():
    """Test that polish tool results with 'polished_draft' key still work (backward compatibility)"""
    generator = NaturalResponseGenerator()
    
    # Mock polish tool result with old 'polished_draft' key  
    class MockResult:
        polished_draft = 'This is a polished essay with the old key format.'
    
    polish_result = MockToolResult(
        tool_name='polish',
        result={'ok': MockResult()}
    )
    
    # Generate formatted response
    formatted_response = generator._format_successful_tool_result(polish_result)
    
    # Verify the essay content is displayed
    assert "Essay Polished:" in formatted_response
    assert "This is a polished essay with the old key format." in formatted_response
    

def test_polish_tool_fallback_for_malformed_result():
    """Test that malformed polish results fall back to generic success message"""
    generator = NaturalResponseGenerator()
    
    # Mock malformed polish tool result
    polish_result = MockToolResult(
        tool_name='polish',
        result={'ok': {'unexpected_key': 'some content'}}
    )
    
    # Generate formatted response
    formatted_response = generator._format_successful_tool_result(polish_result)
    
    # Verify it falls back to generic message
    assert "polish** completed successfully" in formatted_response


if __name__ == "__main__":
    # Quick verification that the fix works
    test_polish_tool_display_with_final_draft_key()
    test_polish_tool_display_with_polished_draft_key()
    test_polish_tool_fallback_for_malformed_result()
    print("✅ All polish tool display tests passed!") 