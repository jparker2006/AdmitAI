"""Integration tests for brainstorming tools workflow."""

import json
import pytest
from langchain.llms.fake import FakeListLLM

from essay_agent.tools.brainstorm_tools import (
    StorySuggestionTool,
    StoryMatchingTool,
    StoryExpansionTool,
    UniquenessValidationTool,
)
from essay_agent.tools import REGISTRY


class TestBrainstormingWorkflow:
    """Test the complete brainstorming workflow with realistic data."""
    
    def setup_method(self):
        """Set up test data for each test."""
        self.essay_prompt = "Describe a time when you challenged a belief or idea. What prompted you to act? What did you learn from the experience?"
        
        self.user_profile = """
        Name: Sarah Chen
        Grade: 12
        Intended Major: Computer Science
        
        Academic Background:
        - GPA: 3.8
        - AP Computer Science A: 5
        - AP Calculus BC: 4
        - President of Coding Club
        - Volunteer tutor for math and programming
        
        Extracurricular Activities:
        - Debate team captain (2 years)
        - Started "Girls in STEM" mentoring program
        - Internship at local tech startup
        - Volunteer at senior center teaching technology
        
        Defining Moments:
        - Challenged gender stereotypes in computer science class
        - Organized hackathon for underrepresented students
        - Confronted bias in tech internship environment
        - Started coding tutorial videos for beginners
        
        Core Values:
        - Equality and inclusion
        - Lifelong learning
        - Helping others succeed
        - Innovation and creativity
        """
        
        self.sample_story = """
        During my junior year in AP Computer Science, I noticed that female students were being interrupted more frequently during class discussions and their ideas were often dismissed or credited to male students. When I brought this up with my teacher, he said I was "being too sensitive" and that I should focus on my code instead of "making everything about gender."
        
        This response frustrated me because I knew what I was observing was real. I decided to document instances of this bias over the next month, keeping detailed notes of interruptions, idea attribution, and participation patterns. When I presented this data to my teacher, he was initially defensive but eventually acknowledged the pattern.
        
        Together, we implemented new discussion protocols that ensured equal speaking time and proper attribution of ideas. The classroom dynamic improved dramatically, and several female students who had been quiet began contributing more actively.
        
        This experience taught me that challenging bias requires both courage and evidence. It also showed me the importance of speaking up for others and creating inclusive environments where everyone can thrive.
        """
    
    def test_story_suggestion_workflow(self, monkeypatch):
        """Test the story suggestion workflow."""
        # Mock LLM response for story suggestions
        fake_story_suggestions = {
            "stories": [
                {
                    "title": "Gender Bias in CS Class",
                    "description": "Documented and challenged gender bias in computer science classroom discussions.",
                    "relevance_score": 0.95,
                    "themes": ["equality", "courage", "evidence-based advocacy"],
                    "prompt_fit_explanation": "Directly addresses challenging beliefs about gender roles in STEM",
                    "unique_elements": ["Data-driven approach to bias documentation"]
                },
                {
                    "title": "Hackathon for Inclusion",
                    "description": "Organized hackathon specifically for underrepresented students in technology.",
                    "relevance_score": 0.85,
                    "themes": ["inclusion", "leadership", "innovation"],
                    "prompt_fit_explanation": "Challenges status quo in tech through inclusive event creation",
                    "unique_elements": ["Event organization for social change"]
                },
                {
                    "title": "Teaching Seniors Technology",
                    "description": "Challenged ageist assumptions by teaching complex technology to senior citizens.",
                    "relevance_score": 0.75,
                    "themes": ["service", "patience", "breaking stereotypes"],
                    "prompt_fit_explanation": "Challenged beliefs about age and technology capability",
                    "unique_elements": ["Intergenerational mentoring"]
                },
                {
                    "title": "Startup Bias Confrontation",
                    "description": "Addressed discriminatory practices during tech internship experience.",
                    "relevance_score": 0.80,
                    "themes": ["workplace ethics", "advocacy", "professionalism"],
                    "prompt_fit_explanation": "Challenged workplace culture and discriminatory practices",
                    "unique_elements": ["Professional environment advocacy"]
                },
                {
                    "title": "Coding Tutorial Videos",
                    "description": "Created inclusive programming tutorials challenging intimidating tech culture.",
                    "relevance_score": 0.70,
                    "themes": ["education", "accessibility", "creativity"],
                    "prompt_fit_explanation": "Challenged elitist beliefs about who can learn programming",
                    "unique_elements": ["Creative educational content"]
                }
            ],
            "analysis_notes": "Strong profile with multiple examples of challenging bias and promoting inclusion"
        }
        
        fake_llm = FakeListLLM(responses=[json.dumps(fake_story_suggestions)])
        monkeypatch.setattr("essay_agent.tools.brainstorm_tools.get_chat_llm", lambda **_: fake_llm)
        
        # Test story suggestion
        tool = StorySuggestionTool()
        result = tool(essay_prompt=self.essay_prompt, profile=self.user_profile)
        
        assert "ok" in result
        assert len(result["ok"]["stories"]) == 5
        assert result["ok"]["stories"][0]["title"] == "Gender Bias in CS Class"
        assert result["ok"]["stories"][0]["relevance_score"] == 0.95
        assert "equality" in result["ok"]["stories"][0]["themes"]
    
    def test_story_matching_workflow(self, monkeypatch):
        """Test the story matching workflow."""
        # Mock LLM response for story matching
        fake_matching_result = {
            "match_score": 9.2,
            "rationale": "This story perfectly addresses the prompt's request for challenging a belief or idea. The student identified gender bias (belief/idea), documented it systematically (what prompted action), and learned about evidence-based advocacy (what was learned). The story demonstrates intellectual courage and practical problem-solving.",
            "strengths": [
                "Directly addresses prompt with specific belief challenge",
                "Shows clear progression from observation to action to learning",
                "Demonstrates leadership and advocacy skills",
                "Includes concrete evidence and systematic approach"
            ],
            "weaknesses": [
                "Could include more emotional reflection on personal impact",
                "Missing specific dialogue or interactions"
            ],
            "improvement_suggestions": [
                "Add more personal emotional journey throughout the experience",
                "Include specific conversations with teacher or classmates",
                "Expand on how this experience shaped future actions"
            ],
            "optimization_priority": "Enhance emotional narrative while maintaining factual strength"
        }
        
        fake_llm = FakeListLLM(responses=[json.dumps(fake_matching_result)])
        monkeypatch.setattr("essay_agent.tools.brainstorm_tools.get_chat_llm", lambda **_: fake_llm)
        
        # Test story matching
        tool = StoryMatchingTool()
        result = tool(story=self.sample_story, essay_prompt=self.essay_prompt)
        
        assert "ok" in result
        assert result["ok"]["match_score"] == 9.2
        assert "perfectly addresses the prompt" in result["ok"]["rationale"]
        assert "Directly addresses prompt" in result["ok"]["strengths"][0]
        assert "emotional reflection" in result["ok"]["weaknesses"][0]
    
    def test_story_expansion_workflow(self, monkeypatch):
        """Test the story expansion workflow."""
        # Mock LLM response for story expansion
        fake_expansion_result = {
            "expansion_questions": [
                "What specific examples of bias did you document in your notes?",
                "How did you feel when your teacher initially dismissed your concerns?",
                "What was the teacher's exact reaction when you presented the data?",
                "How did the female students respond to the new discussion protocols?",
                "What specific changes did you notice in classroom dynamics afterward?",
                "How has this experience influenced your approach to addressing bias since then?"
            ],
            "focus_areas": [
                "Emotional journey and personal growth",
                "Specific evidence and data collection process",
                "Impact on classroom community"
            ],
            "missing_details": [
                "Dialogue with teacher and classmates",
                "Specific examples of documented bias",
                "Personal emotional reactions throughout process",
                "Long-term impact on student and school culture"
            ],
            "development_priority": "Focus on the emotional transformation and specific evidence-gathering process"
        }
        
        fake_llm = FakeListLLM(responses=[json.dumps(fake_expansion_result)])
        monkeypatch.setattr("essay_agent.tools.brainstorm_tools.get_chat_llm", lambda **_: fake_llm)
        
        # Test story expansion
        tool = StoryExpansionTool()
        result = tool(story_seed=self.sample_story[:500])  # Use truncated version as seed
        
        assert "ok" in result
        assert len(result["ok"]["expansion_questions"]) == 6
        assert "What specific examples of bias" in result["ok"]["expansion_questions"][0]
        assert "Emotional journey" in result["ok"]["focus_areas"][0]
        assert "Dialogue with teacher" in result["ok"]["missing_details"][0]
    
    def test_uniqueness_validation_workflow(self, monkeypatch):
        """Test the uniqueness validation workflow."""
        # Mock LLM response for uniqueness validation
        fake_uniqueness_result = {
            "uniqueness_score": 0.85,
            "is_unique": True,
            "cliche_risks": [
                "Avoid generic 'I learned to speak up' conclusion",
                "Don't oversimplify complex bias issues"
            ],
            "differentiation_suggestions": [
                "Emphasize the data-driven approach to addressing bias",
                "Focus on systemic change rather than individual courage",
                "Highlight the collaborative solution-finding process"
            ],
            "unique_elements": [
                "Systematic documentation of bias patterns",
                "Evidence-based approach to addressing discrimination",
                "Collaborative problem-solving with authority figure"
            ],
            "risk_mitigation": [
                "Avoid 'savior' narrative by emphasizing community benefit",
                "Focus on learning and growth rather than just success"
            ],
            "recommendation": "Strong unique angle with data-driven approach - avoid common 'standing up to authority' cliché by emphasizing collaborative problem-solving"
        }
        
        fake_llm = FakeListLLM(responses=[json.dumps(fake_uniqueness_result)])
        monkeypatch.setattr("essay_agent.tools.brainstorm_tools.get_chat_llm", lambda **_: fake_llm)
        
        # Test uniqueness validation
        tool = UniquenessValidationTool()
        result = tool(
            story_angle="Student documents gender bias in computer science class and works with teacher to implement inclusive discussion protocols",
            previous_essays=[
                "Essay about volunteering at soup kitchen",
                "Essay about overcoming fear of public speaking"
            ]
        )
        
        assert "ok" in result
        assert result["ok"]["uniqueness_score"] == 0.85
        assert result["ok"]["is_unique"] is True
        assert "data-driven approach" in result["ok"]["differentiation_suggestions"][0]
        assert "Systematic documentation" in result["ok"]["unique_elements"][0]
    
    def test_complete_brainstorming_workflow(self, monkeypatch):
        """Test a complete brainstorming workflow using all tools in sequence."""
        # Mock responses for all tools
        story_suggestions_response = {
            "stories": [
                {
                    "title": "Gender Bias Documentation",
                    "description": "Systematically documented gender bias in CS class and created solutions.",
                    "relevance_score": 0.95,
                    "themes": ["equality", "evidence-based advocacy"],
                    "prompt_fit_explanation": "Directly challenges beliefs about gender roles in STEM",
                    "unique_elements": ["Data-driven advocacy"]
                }
            ] * 5,
            "analysis_notes": "Strong advocacy background"
        }
        
        matching_response = {
            "match_score": 9.0,
            "rationale": "Excellent match with clear belief challenge",
            "strengths": ["Clear progression", "Evidence-based approach"],
            "weaknesses": ["Needs more emotion"],
            "improvement_suggestions": ["Add personal reflection"],
            "optimization_priority": "Enhance emotional depth"
        }
        
        expansion_response = {
            "expansion_questions": [
                "What specific bias instances did you document?",
                "How did you feel during the confrontation?",
                "What was the teacher's initial reaction?",
                "How did other students respond?",
                "What changes occurred afterward?"
            ],
            "focus_areas": ["Documentation process", "Emotional journey"],
            "missing_details": ["Specific dialogue", "Personal feelings"],
            "development_priority": "Focus on evidence-gathering process"
        }
        
        uniqueness_response = {
            "uniqueness_score": 0.8,
            "is_unique": True,
            "cliche_risks": ["Avoid generic advocacy message"],
            "differentiation_suggestions": ["Emphasize systematic approach"],
            "unique_elements": ["Data-driven method"],
            "risk_mitigation": ["Focus on collaboration"],
            "recommendation": "Strong unique angle with systematic approach"
        }
        
        responses = [
            json.dumps(story_suggestions_response),
            json.dumps(matching_response),
            json.dumps(expansion_response),
            json.dumps(uniqueness_response)
        ]
        
        fake_llm = FakeListLLM(responses=responses)
        monkeypatch.setattr("essay_agent.tools.brainstorm_tools.get_chat_llm", lambda **_: fake_llm)
        
        # Step 1: Generate story suggestions
        suggest_tool = StorySuggestionTool()
        suggestions = suggest_tool(essay_prompt=self.essay_prompt, profile=self.user_profile)
        assert "ok" in suggestions
        selected_story = suggestions["ok"]["stories"][0]
        
        # Step 2: Match story to prompt
        match_tool = StoryMatchingTool()
        match_result = match_tool(
            story=selected_story["description"],
            essay_prompt=self.essay_prompt
        )
        assert "ok" in match_result
        assert match_result["ok"]["match_score"] == 9.0
        
        # Step 3: Expand the story
        expand_tool = StoryExpansionTool()
        expansion = expand_tool(story_seed=selected_story["description"])
        assert "ok" in expansion
        assert len(expansion["ok"]["expansion_questions"]) == 5
        
        # Step 4: Validate uniqueness
        uniqueness_tool = UniquenessValidationTool()
        uniqueness = uniqueness_tool(
            story_angle=selected_story["description"],
            previous_essays=[]
        )
        assert "ok" in uniqueness
        assert uniqueness["ok"]["is_unique"] is True
        
        # Verify workflow produces coherent results
        assert selected_story["themes"] == ["equality", "evidence-based advocacy"]
        assert "Evidence-based approach" in match_result["ok"]["strengths"][1]
        assert "Documentation process" in expansion["ok"]["focus_areas"][0]
        assert "Data-driven method" in uniqueness["ok"]["unique_elements"][0]
    
    def test_registry_integration(self):
        """Test that all tools are properly registered and accessible."""
        # Test direct tool access
        assert "suggest_stories" in REGISTRY
        assert "match_story" in REGISTRY
        assert "expand_story" in REGISTRY
        assert "validate_uniqueness" in REGISTRY
        
        # Test tools are callable through registry
        suggest_tool = REGISTRY["suggest_stories"]
        match_tool = REGISTRY["match_story"]
        expand_tool = REGISTRY["expand_story"]
        uniqueness_tool = REGISTRY["validate_uniqueness"]
        
        assert callable(suggest_tool)
        assert callable(match_tool)
        assert callable(expand_tool)
        assert callable(uniqueness_tool)
        
        # Test tool descriptions
        assert "5 relevant personal story suggestions" in suggest_tool.description
        assert "Rate how well a specific story matches" in match_tool.description
        assert "Generate strategic follow-up questions" in expand_tool.description
        assert "unique and help avoid overused" in uniqueness_tool.description 