"""
Unit tests for college-scoped story diversification in BrainstormTool.

Tests the new college_id parameter and college-specific story blacklisting logic.
"""

import json
import pytest
from unittest.mock import patch, MagicMock

from essay_agent.tools.brainstorm import BrainstormTool
from essay_agent.memory.user_profile_schema import UserProfile, EssayRecord, EssayVersion, DefiningMoment
from essay_agent.memory.simple_memory import SimpleMemory
from langchain.llms.fake import FakeListLLM


class TestCollegeScopedBrainstorm:
    """Test suite for college-scoped story diversification."""

    def setup_method(self):
        """Set up test fixtures."""
        self.tool = BrainstormTool()
        self.test_profile = '{"name": "Alex", "activities": ["robotics", "debate", "volunteering"]}'
        self.test_prompt = "Describe a challenge you overcame."
        
        # Mock user profile with college-specific story history
        self.mock_profile = UserProfile(
            user_info={"name": "Alex", "grade": 12, "intended_major": "CS", "college_list": [], "platforms": []},
            academic_profile={"gpa": 3.8, "test_scores": {}, "courses": [], "activities": []},
            core_values=[],
            defining_moments=[
                DefiningMoment(
                    title="Robotics Championship",
                    description="Won state robotics competition",
                    emotional_impact="Pride and accomplishment",
                    lessons_learned="Persistence pays off"
                )
            ],
            essay_history=[
                EssayRecord(
                    prompt_id="harvard_1",
                    prompt_text="Leadership experience",
                    platform="harvard",
                    status="complete",
                    versions=[
                        EssayVersion(
                            version=1,
                            timestamp="2024-01-01T00:00:00",
                            content="Essay about robotics",
                            word_count=500,
                            used_stories=["Robotics Championship"]
                        )
                    ]
                ),
                EssayRecord(
                    prompt_id="stanford_1", 
                    prompt_text="Personal growth",
                    platform="stanford",
                    status="complete",
                    versions=[
                        EssayVersion(
                            version=1,
                            timestamp="2024-01-01T00:00:00",
                            content="Essay about debate",
                            word_count=500,
                            used_stories=["Debate Victory"]
                        )
                    ]
                )
            ]
        )

    def test_college_scoped_blacklist_same_college(self):
        """Test that stories are blocked only for the same college."""
        # Harvard should block "Robotics Championship" but not "Debate Victory"
        blacklist = self.tool._get_college_story_blacklist("test_user", "harvard")
        
        with patch.object(SimpleMemory, 'load', return_value=self.mock_profile):
            result = self.tool._get_college_story_blacklist("test_user", "harvard")
            assert "Robotics Championship" in result
            assert "Debate Victory" not in result

    def test_college_scoped_blacklist_different_college(self):
        """Test that different colleges have different blacklists."""
        with patch.object(SimpleMemory, 'load', return_value=self.mock_profile):
            # Stanford should block "Debate Victory" but not "Robotics Championship"
            stanford_blacklist = self.tool._get_college_story_blacklist("test_user", "stanford")
            assert "Debate Victory" in stanford_blacklist
            assert "Robotics Championship" not in stanford_blacklist

    def test_cross_college_story_suggestions(self):
        """Test that stories from other colleges are suggested for reuse."""
        with patch.object(SimpleMemory, 'load', return_value=self.mock_profile):
            # When applying to MIT, should suggest stories from Harvard and Stanford
            suggestions = self.tool._get_cross_college_story_suggestions("test_user", "mit")
            assert "Robotics Championship" in suggestions
            assert "Debate Victory" in suggestions

    def test_prompt_type_categorization(self):
        """Test automatic prompt type detection."""
        # Test identity prompts
        identity_prompt = "Tell us about your identity and background"
        assert self.tool._categorize_prompt_type(identity_prompt) == "identity"
        
        # Test passion prompts  
        passion_prompt = "What is your greatest passion or interest?"
        assert self.tool._categorize_prompt_type(passion_prompt) == "passion"
        
        # Test challenge prompts
        challenge_prompt = "Describe a challenge you overcame"
        assert self.tool._categorize_prompt_type(challenge_prompt) == "challenge"
        
        # Test achievement prompts
        achievement_prompt = "Tell us about an accomplishment you're proud of"
        assert self.tool._categorize_prompt_type(achievement_prompt) == "achievement"
        
        # Test community prompts
        community_prompt = "How have you contributed to your community?"
        assert self.tool._categorize_prompt_type(community_prompt) == "community"
        
        # Test general prompts
        general_prompt = "Write about anything important to you"
        assert self.tool._categorize_prompt_type(general_prompt) == "general"

    def test_story_category_mapping(self):
        """Test that story categories map to prompt types correctly."""
        # Test identity category mapping
        identity_categories = self.tool._get_recommended_story_categories("identity")
        assert "heritage" in identity_categories
        assert "family" in identity_categories
        
        # Test passion category mapping
        passion_categories = self.tool._get_recommended_story_categories("passion")
        assert "creative" in passion_categories
        assert "academic" in passion_categories
        
        # Test challenge category mapping
        challenge_categories = self.tool._get_recommended_story_categories("challenge")
        assert "obstacle" in challenge_categories
        assert "failure" in challenge_categories

    def test_story_conflict_detection(self):
        """Test detection of story conflicts with college usage rules."""
        with patch.object(SimpleMemory, 'load', return_value=self.mock_profile):
            # Should detect conflict when trying to reuse "Robotics Championship" for Harvard
            conflicts = self.tool._detect_story_conflicts(
                ["Robotics Championship", "New Story"], 
                "harvard", 
                "test_user"
            )
            assert "Robotics Championship" in conflicts
            assert "New Story" not in conflicts

    def test_backward_compatibility_no_college_id(self):
        """Test that tool works without college_id parameter."""
        fake_output = {
            "stories": [
                {"title": "Test Story", "description": "Test desc", "prompt_fit": "fits", "insights": ["insight1"]},
                {"title": "Test Story 2", "description": "Test desc 2", "prompt_fit": "fits", "insights": ["insight2"]},
                {"title": "Test Story 3", "description": "Test desc 3", "prompt_fit": "fits", "insights": ["insight3"]},
            ]
        }
        
        with patch('essay_agent.tools.brainstorm.get_chat_llm') as mock_llm:
            mock_llm.return_value = FakeListLLM(responses=[json.dumps(fake_output)])
            
            # Should work without college_id (backward compatibility)
            result = self.tool._run(
                essay_prompt=self.test_prompt,
                profile=self.test_profile,
                user_id="test_user"
                # No college_id parameter
            )
            
            assert result["stories"][0]["title"] == "Test Story"

    def test_college_aware_prompt_rendering(self):
        """Test that college-aware prompts are rendered with correct variables."""
        college_blacklist = {"Used Story 1", "Used Story 2"}
        cross_college_suggestions = ["Reusable Story 1", "Reusable Story 2"]
        
        rendered = self.tool._render_college_aware_prompt(
            essay_prompt=self.test_prompt,
            profile=self.test_profile,
            college_blacklist=college_blacklist,
            cross_college_suggestions=cross_college_suggestions,
            prompt_type="challenge",
            college_id="harvard"
        )
        
        assert "harvard" in rendered
        assert "Used Story 1" in rendered
        assert "Reusable Story 1" in rendered
        assert "challenge" in rendered

    def test_full_workflow_with_college_id(self):
        """Test complete workflow with college_id parameter."""
        fake_output = {
            "stories": [
                {"title": "New Challenge Story", "description": "Overcame coding bug", "prompt_fit": "Shows persistence", "insights": ["Debugging", "Growth"]},
                {"title": "Academic Struggle", "description": "Failed math test", "prompt_fit": "Shows resilience", "insights": ["Learning", "Improvement"]},
                {"title": "Social Challenge", "description": "Shy to confident", "prompt_fit": "Shows development", "insights": ["Confidence", "Growth"]},
            ]
        }
        
        with patch('essay_agent.tools.brainstorm.get_chat_llm') as mock_llm, \
             patch.object(SimpleMemory, 'load', return_value=self.mock_profile), \
             patch.object(SimpleMemory, 'save'):
            
            mock_llm.return_value = FakeListLLM(responses=[json.dumps(fake_output)])
            
            result = self.tool._run(
                essay_prompt=self.test_prompt,
                profile=self.test_profile,
                user_id="test_user",
                college_id="harvard"
            )
            
            assert len(result["stories"]) == 3
            assert result["stories"][0]["title"] == "New Challenge Story"
            # Should not include "Robotics Championship" since it's already used for Harvard

    def test_error_handling_missing_user_profile(self):
        """Test error handling when user profile is missing."""
        with patch.object(SimpleMemory, 'load', side_effect=Exception("Profile not found")):
            # Should gracefully handle missing profile
            blacklist = self.tool._get_college_story_blacklist("nonexistent_user", "harvard")
            assert blacklist == set()
            
            suggestions = self.tool._get_cross_college_story_suggestions("nonexistent_user", "harvard")
            assert suggestions == [] 