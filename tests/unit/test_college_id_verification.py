"""
Tests for college ID verification logging in brainstorm tool.
"""

import pytest
from unittest.mock import patch, MagicMock
from essay_agent.tools.brainstorm import BrainstormTool


class TestCollegeIdVerification:
    """Test college ID verification logging functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.tool = BrainstormTool()
    
    @patch('essay_agent.utils.logging.debug_print')
    @patch('essay_agent.utils.logging.VERBOSE', True)
    def test_verify_college_id_with_valid_id(self, mock_debug_print):
        """Test college ID verification with valid college ID."""
        college_id = "stanford"
        
        self.tool._verify_college_id_usage(college_id)
        
        # Verify debug prints were called
        mock_debug_print.assert_called()
        
        # Check that appropriate messages were logged
        call_args = [call[0][1] for call in mock_debug_print.call_args_list]
        assert any("College ID received: stanford" in arg for arg in call_args)
        assert any("College-aware story selection ACTIVE" in arg for arg in call_args)
    
    @patch('essay_agent.utils.logging.debug_print')
    @patch('essay_agent.utils.logging.VERBOSE', True)
    def test_verify_college_id_with_none(self, mock_debug_print):
        """Test college ID verification with None college ID."""
        college_id = None
        
        self.tool._verify_college_id_usage(college_id)
        
        # Verify debug prints were called
        mock_debug_print.assert_called()
        
        # Check that warning was logged
        call_args = [call[0][1] for call in mock_debug_print.call_args_list]
        assert any("College ID received: None" in arg for arg in call_args)
        assert any("WARNING: college_id is None" in arg for arg in call_args)
    
    @patch('essay_agent.utils.logging.debug_print')
    @patch('essay_agent.utils.logging.VERBOSE', False)
    def test_verify_college_id_verbose_disabled(self, mock_debug_print):
        """Test college ID verification when verbose is disabled."""
        college_id = "harvard"
        
        self.tool._verify_college_id_usage(college_id)
        
        # Verify debug prints were NOT called when verbose is disabled
        mock_debug_print.assert_not_called()
    
    @patch('essay_agent.utils.logging.debug_print')
    @patch('essay_agent.utils.logging.VERBOSE', True)
    def test_debug_story_selection_includes_college_verification(self, mock_debug_print):
        """Test that debug_story_selection includes college ID verification."""
        from essay_agent.tools.brainstorm import Story
        
        stories = [
            Story(title="Test Story", description="Test", prompt_fit="Good", insights=["Test"])
        ]
        college_id = "mit"
        
        self.tool._debug_story_selection(
            stories=stories,
            prompt_type="challenge",
            college_blacklist=set(),
            cross_college_suggestions=[],
            college_id=college_id
        )
        
        # Verify debug prints were called
        mock_debug_print.assert_called()
        
        # Check that college ID verification was included
        call_args = [call[0][1] for call in mock_debug_print.call_args_list]
        assert any("College ID: mit" in arg for arg in call_args)
        assert any("College-aware story selection ACTIVE" in arg for arg in call_args)
    
    @patch('essay_agent.utils.logging.debug_print')
    @patch('essay_agent.utils.logging.VERBOSE', True)
    def test_update_user_profile_with_college_logging(self, mock_debug_print):
        """Test that user profile update includes college-aware logging."""
        from essay_agent.tools.brainstorm import Story
        
        stories = [
            Story(title="Test Story", description="Test", prompt_fit="Good", insights=["Test"])
        ]
        college_id = "yale"
        
        # Mock SimpleMemory to avoid actual file operations
        with patch('essay_agent.tools.brainstorm.SimpleMemory') as mock_memory:
            mock_profile = MagicMock()
            mock_profile.defining_moments = []
            mock_memory.load.return_value = mock_profile
            
            self.tool._update_user_profile_with_stories(
                user_id="test_user",
                stories=stories,
                college_id=college_id,
                prompt_type="challenge"
            )
        
        # Verify debug prints were called
        mock_debug_print.assert_called()
        
        # Check that college-aware logging was included
        call_args = [call[0][1] for call in mock_debug_print.call_args_list]
        assert any("Updating user profile" in arg and "college: yale" in arg for arg in call_args)
        assert any("Added new story to profile" in arg for arg in call_args)
    
    @patch('essay_agent.utils.logging.debug_print')
    @patch('essay_agent.utils.logging.VERBOSE', True)
    def test_update_user_profile_error_handling(self, mock_debug_print):
        """Test error handling in user profile update with logging."""
        from essay_agent.tools.brainstorm import Story
        
        stories = [
            Story(title="Test Story", description="Test", prompt_fit="Good", insights=["Test"])
        ]
        college_id = "princeton"
        
        # Mock SimpleMemory to raise an exception
        with patch('essay_agent.tools.brainstorm.SimpleMemory') as mock_memory:
            mock_memory.load.side_effect = Exception("Memory error")
            
            # Should not raise exception - should handle gracefully
            self.tool._update_user_profile_with_stories(
                user_id="test_user",
                stories=stories,
                college_id=college_id,
                prompt_type="identity"
            )
        
        # Verify error was logged
        call_args = [call[0][1] for call in mock_debug_print.call_args_list]
        assert any("Error updating user profile" in arg for arg in call_args)
    
    @patch('essay_agent.utils.logging.debug_print')
    @patch('essay_agent.utils.logging.VERBOSE', True)
    def test_college_id_verification_error_handling(self, mock_debug_print):
        """Test error handling in college ID verification."""
        college_id = "test_college"
        
        # Should handle any errors gracefully
        self.tool._verify_college_id_usage(college_id)
        
        # Verify basic verification messages were logged
        call_args = [call[0][1] for call in mock_debug_print.call_args_list]
        assert any("College ID received: test_college" in arg for arg in call_args)
        assert any("College-aware story selection ACTIVE" in arg for arg in call_args)
    
    def test_college_id_parameter_in_run_method(self):
        """Test that college_id parameter is properly accepted in _run method."""
        # Mock the LLM and other dependencies to focus on parameter handling
        with patch('essay_agent.tools.brainstorm.render_template') as mock_render:
            with patch('essay_agent.llm_client.call_llm') as mock_call_llm:
                with patch('essay_agent.tools.brainstorm.safe_parse') as mock_parse:
                    from essay_agent.tools.brainstorm import BrainstormResult, Story
                    
                    mock_render.return_value = "test prompt"
                    mock_call_llm.return_value = "test response"
                    
                    # Create a proper BrainstormResult object with 3 stories
                    mock_stories = [
                        Story(title="Story 1", description="Test story 1", prompt_fit="Good", insights=["Insight 1"]),
                        Story(title="Story 2", description="Test story 2", prompt_fit="Good", insights=["Insight 2"]),
                        Story(title="Story 3", description="Test story 3", prompt_fit="Good", insights=["Insight 3"])
                    ]
                    mock_brainstorm_result = BrainstormResult(stories=mock_stories)
                    mock_parse.return_value = mock_brainstorm_result
                    
                    # Test that college_id parameter is accepted
                    try:
                        result = self.tool._run(
                            essay_prompt="Test prompt",
                            profile="Test profile",
                            user_id="test_user",
                            college_id="test_college"
                        )
                        # Should not raise exception
                        assert isinstance(result, dict)
                        assert "stories" in result
                    except TypeError as e:
                        pytest.fail(f"college_id parameter not accepted: {e}")
    
    @patch('essay_agent.utils.logging.debug_print')
    @patch('essay_agent.utils.logging.VERBOSE', True)
    def test_debug_story_selection_comprehensive(self, mock_debug_print):
        """Test comprehensive debug story selection logging."""
        from essay_agent.tools.brainstorm import Story
        
        stories = [
            Story(title="Story 1", description="Test 1", prompt_fit="Good fit", insights=["Insight 1"]),
            Story(title="Story 2", description="Test 2", prompt_fit="Fair fit", insights=["Insight 2"])
        ]
        college_blacklist = {"Used Story"}
        cross_college_suggestions = ["Suggested Story"]
        college_id = "columbia"
        
        self.tool._debug_story_selection(
            stories=stories,
            prompt_type="passion",
            college_blacklist=college_blacklist,
            cross_college_suggestions=cross_college_suggestions,
            college_id=college_id
        )
        
        # Verify comprehensive logging
        call_args = [call[0][1] for call in mock_debug_print.call_args_list]
        
        # Check all expected elements are logged
        assert any("STORY SELECTION DEBUG" in arg for arg in call_args)
        assert any("Prompt type: passion" in arg for arg in call_args)
        assert any("College ID: columbia" in arg for arg in call_args)
        assert any("Selected stories:" in arg for arg in call_args)
        assert any("Blacklisted stories" in arg for arg in call_args)
        assert any("Cross-college suggestions" in arg for arg in call_args)
        assert any("Story 1" in arg for arg in call_args)
        assert any("Story 2" in arg for arg in call_args)
        assert any("END STORY SELECTION DEBUG" in arg for arg in call_args) 