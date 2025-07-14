"""
Integration tests for college story diversification workflow.

Tests the complete multi-college story diversification system across different 
prompt types and colleges.
"""

import json
import pytest
from unittest.mock import patch, MagicMock

from essay_agent.tools.brainstorm import BrainstormTool
from essay_agent.memory.user_profile_schema import UserProfile, EssayRecord, EssayVersion, DefiningMoment
from essay_agent.memory.simple_memory import SimpleMemory
from langchain.llms.fake import FakeListLLM


class TestCollegeStoryDiversification:
    """Integration tests for college story diversification."""

    def setup_method(self):
        """Set up test fixtures."""
        self.tool = BrainstormTool()
        
        # Comprehensive user profile with diverse experiences
        self.user_profile = UserProfile(
            user_info={
                "name": "Alex Chen",
                "grade": 12,
                "intended_major": "Computer Science",
                "college_list": ["Harvard", "Stanford", "MIT"],
                "platforms": ["Common App", "Coalition"]
            },
            academic_profile={
                "gpa": 3.9,
                "test_scores": {"SAT": 1520},
                "courses": ["AP Computer Science", "AP Calculus"],
                "activities": []
            },
            core_values=[],
            defining_moments=[
                DefiningMoment(
                    title="Robotics Championship Victory",
                    description="Led team to state robotics championship",
                    emotional_impact="Pride and leadership growth",
                    lessons_learned="Teamwork and persistence",
                    story_category="achievement"
                ),
                DefiningMoment(
                    title="Immigrant Family Heritage",
                    description="Bridging cultures as first-generation American",
                    emotional_impact="Identity formation and pride",
                    lessons_learned="Cultural appreciation and resilience",
                    story_category="identity"
                ),
                DefiningMoment(
                    title="Coding Bootcamp Failure",
                    description="Failed first coding bootcamp, learned from mistakes",
                    emotional_impact="Humility and determination",
                    lessons_learned="Failure as learning opportunity",
                    story_category="challenge"
                ),
                DefiningMoment(
                    title="Community Garden Project",
                    description="Started neighborhood garden for food security",
                    emotional_impact="Social responsibility and impact",
                    lessons_learned="Community organizing and sustainability",
                    story_category="community"
                ),
                DefiningMoment(
                    title="Poetry and Creative Writing",
                    description="Discovered love for creative expression through poetry",
                    emotional_impact="Artistic fulfillment and self-discovery",
                    lessons_learned="Creative expression and vulnerability",
                    story_category="passion"
                )
            ],
            essay_history=[
                # Harvard application - used robotics story
                EssayRecord(
                    prompt_id="harvard_leadership",
                    prompt_text="Describe a leadership experience",
                    platform="harvard",
                    status="complete",
                    versions=[
                        EssayVersion(
                            version=1,
                            timestamp="2024-01-01T00:00:00",
                            content="Essay about robotics leadership",
                            word_count=500,
                            used_stories=["Robotics Championship Victory"]
                        )
                    ]
                ),
                # Stanford application - used heritage story
                EssayRecord(
                    prompt_id="stanford_identity",
                    prompt_text="Tell us about your identity",
                    platform="stanford",
                    status="complete",
                    versions=[
                        EssayVersion(
                            version=1,
                            timestamp="2024-01-01T00:00:00",
                            content="Essay about immigrant heritage",
                            word_count=500,
                            used_stories=["Immigrant Family Heritage"]
                        )
                    ]
                )
            ]
        )
        
        self.profile_json = json.dumps({
            "name": "Alex Chen",
            "experiences": [
                "Robotics team captain",
                "First-generation immigrant",
                "Failed coding bootcamp",
                "Community garden organizer",
                "Poetry enthusiast"
            ]
        })

    def test_multi_college_workflow(self):
        """Test complete workflow across multiple colleges."""
        
        # Define different story responses for different prompt types
        identity_stories = {
            "stories": [
                {"title": "Heritage Bridge Builder", "description": "Connecting two cultures daily", "prompt_fit": "Shows identity formation", "insights": ["Cultural bridge", "Adaptation"]},
                {"title": "Language Keeper", "description": "Preserving family traditions", "prompt_fit": "Shows cultural identity", "insights": ["Tradition", "Family"]},
                {"title": "First Generation Pioneer", "description": "Navigating college prep alone", "prompt_fit": "Shows independence", "insights": ["Resilience", "Independence"]}
            ]
        }
        
        passion_stories = {
            "stories": [
                {"title": "Poetry Slam Discovery", "description": "Found voice through spoken word", "prompt_fit": "Shows creative passion", "insights": ["Expression", "Confidence"]},
                {"title": "Code as Art", "description": "Programming as creative medium", "prompt_fit": "Shows technical passion", "insights": ["Creativity", "Logic"]},
                {"title": "Garden Design Vision", "description": "Creating sustainable spaces", "prompt_fit": "Shows environmental passion", "insights": ["Sustainability", "Community"]}
            ]
        }
        
        challenge_stories = {
            "stories": [
                {"title": "Bootcamp Failure Lesson", "description": "Learned from coding failure", "prompt_fit": "Shows growth mindset", "insights": ["Persistence", "Learning"]},
                {"title": "Language Barrier Break", "description": "Overcoming communication struggles", "prompt_fit": "Shows adaptability", "insights": ["Communication", "Growth"]},
                {"title": "Team Conflict Resolution", "description": "Solved robotics team dispute", "prompt_fit": "Shows leadership", "insights": ["Leadership", "Diplomacy"]}
            ]
        }
        
        with patch.object(SimpleMemory, 'load', return_value=self.user_profile), \
             patch.object(SimpleMemory, 'save'):
            
            # Test MIT application - should avoid Harvard's robotics story and Stanford's heritage story
            
            # 1. MIT Identity prompt - should get new identity story (not Stanford's heritage)
            with patch('essay_agent.tools.brainstorm.get_chat_llm') as mock_llm:
                mock_llm.return_value = FakeListLLM(responses=[json.dumps(identity_stories)])
                
                result = self.tool._run(
                    essay_prompt="Tell us about your identity and background",
                    profile=self.profile_json,
                    user_id="test_user",
                    college_id="mit"
                )
                
                # Should get new identity stories, not reuse Stanford's heritage story
                story_titles = [story["title"] for story in result["stories"]]
                assert "Heritage Bridge Builder" in story_titles
                assert "Immigrant Family Heritage" not in story_titles  # Already used for Stanford
            
            # 2. MIT Passion prompt - should get passion stories
            with patch('essay_agent.tools.brainstorm.get_chat_llm') as mock_llm:
                mock_llm.return_value = FakeListLLM(responses=[json.dumps(passion_stories)])
                
                result = self.tool._run(
                    essay_prompt="What is your greatest passion or interest?",
                    profile=self.profile_json,
                    user_id="test_user",
                    college_id="mit"
                )
                
                story_titles = [story["title"] for story in result["stories"]]
                assert "Poetry Slam Discovery" in story_titles
                # Should be different from identity stories
                assert "Heritage Bridge Builder" not in story_titles
            
            # 3. MIT Challenge prompt - should get challenge stories
            with patch('essay_agent.tools.brainstorm.get_chat_llm') as mock_llm:
                mock_llm.return_value = FakeListLLM(responses=[json.dumps(challenge_stories)])
                
                result = self.tool._run(
                    essay_prompt="Describe a challenge you overcame",
                    profile=self.profile_json,
                    user_id="test_user",
                    college_id="mit"
                )
                
                story_titles = [story["title"] for story in result["stories"]]
                assert "Bootcamp Failure Lesson" in story_titles
                # Should be different from previous stories
                assert "Poetry Slam Discovery" not in story_titles
                assert "Heritage Bridge Builder" not in story_titles

    def test_story_diversification_across_prompts(self):
        """Test that different prompt types get different stories within same college."""
        
        # Test Harvard application with multiple prompts
        identity_response = {
            "stories": [
                {"title": "Cultural Navigator", "description": "Bridging two worlds", "prompt_fit": "Shows identity", "insights": ["Culture", "Bridge"]},
                {"title": "Family Translator", "description": "Helping parents navigate", "prompt_fit": "Shows responsibility", "insights": ["Family", "Support"]},
                {"title": "Heritage Keeper", "description": "Preserving traditions", "prompt_fit": "Shows values", "insights": ["Tradition", "Values"]}
            ]
        }
        
        passion_response = {
            "stories": [
                {"title": "Creative Coder", "description": "Art through programming", "prompt_fit": "Shows passion", "insights": ["Creativity", "Tech"]},
                {"title": "Word Weaver", "description": "Poetry as expression", "prompt_fit": "Shows creativity", "insights": ["Expression", "Art"]},
                {"title": "Garden Architect", "description": "Designing green spaces", "prompt_fit": "Shows environmental passion", "insights": ["Environment", "Design"]}
            ]
        }
        
        with patch.object(SimpleMemory, 'load', return_value=self.user_profile), \
             patch.object(SimpleMemory, 'save'):
            
            # First prompt - Identity
            with patch('essay_agent.tools.brainstorm.get_chat_llm') as mock_llm:
                mock_llm.return_value = FakeListLLM(responses=[json.dumps(identity_response)])
                
                identity_result = self.tool._run(
                    essay_prompt="Tell us about your identity",
                    profile=self.profile_json,
                    user_id="test_user",
                    college_id="harvard"
                )
                
                identity_titles = [story["title"] for story in identity_result["stories"]]
                assert "Cultural Navigator" in identity_titles
            
            # Second prompt - Passion (should get different stories)
            with patch('essay_agent.tools.brainstorm.get_chat_llm') as mock_llm:
                mock_llm.return_value = FakeListLLM(responses=[json.dumps(passion_response)])
                
                passion_result = self.tool._run(
                    essay_prompt="What is your greatest passion?",
                    profile=self.profile_json,
                    user_id="test_user",
                    college_id="harvard"
                )
                
                passion_titles = [story["title"] for story in passion_result["stories"]]
                assert "Creative Coder" in passion_titles
                # Should be different from identity stories
                assert "Cultural Navigator" not in passion_titles

    def test_cross_college_reuse_appropriate_stories(self):
        """Test that appropriate stories can be reused across colleges."""
        
        # Test that MIT can reuse good stories from Harvard/Stanford when appropriate
        reuse_response = {
            "stories": [
                {"title": "Robotics Championship Victory", "description": "Led team to victory", "prompt_fit": "Shows leadership", "insights": ["Leadership", "Tech"]},
                {"title": "New Technical Challenge", "description": "Different technical story", "prompt_fit": "Shows problem solving", "insights": ["Problem solving", "Growth"]},
                {"title": "Innovation Project", "description": "Created new solution", "prompt_fit": "Shows creativity", "insights": ["Innovation", "Impact"]}
            ]
        }
        
        with patch.object(SimpleMemory, 'load', return_value=self.user_profile), \
             patch.object(SimpleMemory, 'save'):
            
            with patch('essay_agent.tools.brainstorm.get_chat_llm') as mock_llm:
                mock_llm.return_value = FakeListLLM(responses=[json.dumps(reuse_response)])
                
                result = self.tool._run(
                    essay_prompt="Describe a leadership experience",
                    profile=self.profile_json,
                    user_id="test_user",
                    college_id="mit"  # Different college from Harvard
                )
                
                story_titles = [story["title"] for story in result["stories"]]
                # Should be able to reuse robotics story from Harvard for MIT
                assert "Robotics Championship Victory" in story_titles

    def test_prompt_type_detection_integration(self):
        """Test that prompt type detection works correctly in full workflow."""
        
        test_cases = [
            ("Tell us about your identity and background", "identity"),
            ("What is your greatest passion?", "passion"),
            ("Describe a challenge you overcame", "challenge"),
            ("Tell us about an accomplishment", "achievement"),
            ("How have you contributed to your community?", "community"),
            ("Write about anything important to you", "general")
        ]
        
        for prompt_text, expected_type in test_cases:
            detected_type = self.tool._categorize_prompt_type(prompt_text)
            assert detected_type == expected_type, f"Expected {expected_type}, got {detected_type} for prompt: {prompt_text}"

    def test_college_story_tracking_persistence(self):
        """Test that college story usage is properly tracked and persisted."""
        
        story_response = {
            "stories": [
                {"title": "New MIT Story", "description": "MIT specific story", "prompt_fit": "Perfect fit", "insights": ["MIT", "Specific"]},
                {"title": "Tech Innovation", "description": "Created new tech", "prompt_fit": "Shows innovation", "insights": ["Innovation", "Tech"]},
                {"title": "Problem Solver", "description": "Solved complex issue", "prompt_fit": "Shows capability", "insights": ["Problem solving", "Logic"]}
            ]
        }
        
        with patch.object(SimpleMemory, 'load', return_value=self.user_profile) as mock_load, \
             patch.object(SimpleMemory, 'save') as mock_save:
            
            with patch('essay_agent.tools.brainstorm.get_chat_llm') as mock_llm:
                mock_llm.return_value = FakeListLLM(responses=[json.dumps(story_response)])
                
                result = self.tool._run(
                    essay_prompt="Describe a technical challenge",
                    profile=self.profile_json,
                    user_id="test_user",
                    college_id="mit"
                )
                
                # Verify that save was called (stories were persisted)
                mock_save.assert_called_once()
                
                # Verify that the profile was updated with new stories
                call_args = mock_save.call_args
                updated_profile = call_args[0][1]  # Second argument is the profile
                
                # Should have new defining moments added
                story_titles = [dm.title for dm in updated_profile.defining_moments]
                assert "New MIT Story" in story_titles

    def test_error_handling_story_conflicts(self):
        """Test error handling when story conflicts are detected."""
        
        # Try to reuse a story that's already been used for the same college
        conflict_response = {
            "stories": [
                {"title": "Robotics Championship Victory", "description": "Already used story", "prompt_fit": "Conflict", "insights": ["Conflict"]},
                {"title": "New Story", "description": "This is fine", "prompt_fit": "No conflict", "insights": ["Good"]},
                {"title": "Another Story", "description": "Also fine", "prompt_fit": "No conflict", "insights": ["Also good"]}
            ]
        }
        
        with patch.object(SimpleMemory, 'load', return_value=self.user_profile), \
             patch.object(SimpleMemory, 'save'):
            
            with patch('essay_agent.tools.brainstorm.get_chat_llm') as mock_llm:
                mock_llm.return_value = FakeListLLM(responses=[json.dumps(conflict_response)])
                
                # Should raise error when trying to reuse Harvard's robotics story for Harvard
                with pytest.raises(ValueError, match="Story reuse detected for harvard"):
                    self.tool._run(
                        essay_prompt="Describe a leadership experience",
                        profile=self.profile_json,
                        user_id="test_user",
                        college_id="harvard"  # Same college where robotics story was used
                    ) 