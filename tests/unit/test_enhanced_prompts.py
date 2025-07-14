"""
Test suite for Section 7.4 Enhanced Prompt Engineering

Tests that prompts include chain-of-thought reasoning, structural planning,
and self-validation mechanisms.
"""

import pytest
from essay_agent.prompts.brainstorm import BRAINSTORM_PROMPT
from essay_agent.prompts.outline import OUTLINE_PROMPT
from essay_agent.prompts.draft import DRAFT_PROMPT
from essay_agent.prompts.templates import render_template


class TestEnhancedBrainstormPrompt:
    """Test enhanced brainstorm prompt with chain-of-thought reasoning."""
    
    def test_chain_of_thought_steps_present(self):
        """Test that brainstorm prompt includes explicit reasoning steps."""
        prompt_text = str(BRAINSTORM_PROMPT.template)
        
        # Check for all 5 reasoning steps
        assert "STEP 1: ANALYZE THE PROMPT TYPE" in prompt_text
        assert "STEP 2: IDENTIFY SUITABLE STORIES FROM PROFILE" in prompt_text
        assert "STEP 3: APPLY DIVERSIFICATION FILTERING" in prompt_text
        assert "STEP 4: SELECT THE 3 BEST MATCHES" in prompt_text
        assert "STEP 5: VALIDATE EACH SELECTION" in prompt_text
    
    def test_prompt_type_awareness(self):
        """Test that brainstorm prompt includes prompt type awareness."""
        prompt_text = str(BRAINSTORM_PROMPT.template)
        
        # Check for prompt type identification
        assert "Identify the specific prompt type: {prompt_type}" in prompt_text
        assert "This is a {prompt_type} prompt asking for {recommended_categories}" in prompt_text
        assert "Matches {prompt_type} category requirements" in prompt_text
    
    def test_selection_criteria_explicit(self):
        """Test that selection criteria are explicit and detailed."""
        prompt_text = str(BRAINSTORM_PROMPT.template)
        
        # Check for explicit selection criteria
        assert "Direct relevance to {prompt_type} category" in prompt_text
        assert "Authenticity (grounded in {profile})" in prompt_text
        assert "Uniqueness (avoids clichés)" in prompt_text
        assert "Growth potential (shows development)" in prompt_text
        assert "Prompt compliance (answers {essay_prompt})" in prompt_text
    
    def test_validation_checklist_present(self):
        """Test that validation checklist is present and comprehensive."""
        prompt_text = str(BRAINSTORM_PROMPT.template)
        
        # Check for validation checklist
        assert "□ Directly answers the prompt:" in prompt_text
        assert "□ Grounded in student's actual experiences" in prompt_text
        assert "□ Matches {prompt_type} category requirements" in prompt_text
        assert "□ Avoids repetition with {college_story_history}" in prompt_text
        assert "□ Shows clear growth/insight arc" in prompt_text
        assert "□ Avoids overused essay clichés" in prompt_text
    
    def test_required_variables_present(self):
        """Test that all required template variables are present."""
        required_vars = {
            "essay_prompt", "profile", "college_name", "college_story_history",
            "cross_college_suggestions", "prompt_type", "recommended_categories", "today"
        }
        assert required_vars.issubset(set(BRAINSTORM_PROMPT.input_variables))


class TestEnhancedOutlinePrompt:
    """Test enhanced outline prompt with structural word count planning."""
    
    def test_structural_planning_steps(self):
        """Test that outline prompt includes structural planning steps."""
        prompt_text = str(OUTLINE_PROMPT.template)
        
        # Check for structural planning step
        assert "STEP 3: PLAN STRUCTURAL WORD DISTRIBUTION" in prompt_text
        assert "STEP 5: VALIDATE WORD COUNT FEASIBILITY" in prompt_text
    
    def test_word_distribution_planning(self):
        """Test that word distribution planning is detailed."""
        prompt_text = str(OUTLINE_PROMPT.template)
        
        # Check for word distribution details
        assert "Hook: ~{hook_words} words ({hook_percentage}%)" in prompt_text
        assert "Context: ~{context_words} words ({context_percentage}%)" in prompt_text
        assert "Conflict: ~{conflict_words} words ({conflict_percentage}%)" in prompt_text
        assert "Growth: ~{growth_words} words ({growth_percentage}%)" in prompt_text
        assert "Reflection: ~{reflection_words} words ({reflection_percentage}%)" in prompt_text
    
    def test_structural_constraints(self):
        """Test that structural constraints are explicit."""
        prompt_text = str(OUTLINE_PROMPT.template)
        
        # Check for structural constraints
        assert "Your outline must support exactly {word_count} words" in prompt_text
        assert "Plan sections that can realistically support their word targets" in prompt_text
        assert "Ensure each section has sufficient depth for its allocation" in prompt_text
    
    def test_word_count_validation(self):
        """Test that word count validation is included."""
        prompt_text = str(OUTLINE_PROMPT.template)
        
        # Check for validation instructions
        assert "Check that each section can realistically support its target word allocation" in prompt_text
        assert "Ensure narrative flow supports the planned word distribution" in prompt_text
        assert "Verify that the story has enough depth for {word_count} words" in prompt_text
    
    def test_new_template_variables(self):
        """Test that new template variables are present."""
        new_vars = {
            "hook_words", "context_words", "conflict_words", "growth_words", "reflection_words",
            "hook_percentage", "context_percentage", "conflict_percentage", "growth_percentage", "reflection_percentage"
        }
        assert new_vars.issubset(set(OUTLINE_PROMPT.input_variables))


class TestEnhancedDraftPrompt:
    """Test enhanced draft prompt with self-validation mechanisms."""
    
    def test_self_validation_step(self):
        """Test that draft prompt includes self-validation step."""
        prompt_text = str(DRAFT_PROMPT.template)
        
        # Check for validation step
        assert "STEP 5: VALIDATE BEFORE SUBMITTING" in prompt_text
        assert "Complete validation checklist before output" in prompt_text
    
    def test_word_count_validation_instructions(self):
        """Test that word count validation instructions are present."""
        prompt_text = str(DRAFT_PROMPT.template)
        
        # Check for word count validation
        assert "Count your words and check against target: {word_count}" in prompt_text
        assert "If significantly under target, expand key sections" in prompt_text
        assert "If significantly over target, trim carefully" in prompt_text
    
    def test_comprehensive_validation_checklist(self):
        """Test that comprehensive validation checklist is present."""
        prompt_text = str(DRAFT_PROMPT.template)
        
        # Check for validation categories
        assert "WORD COUNT VALIDATION:" in prompt_text
        assert "PROMPT COMPLIANCE:" in prompt_text
        assert "CONTENT AUTHENTICITY:" in prompt_text
        assert "QUALITY STANDARDS:" in prompt_text
        assert "TECHNICAL VALIDATION:" in prompt_text
    
    def test_specific_validation_items(self):
        """Test that specific validation items are present."""
        prompt_text = str(DRAFT_PROMPT.template)
        
        # Check for specific validation items
        assert "Count the words in your draft" in prompt_text
        assert "Check if within 10% of target: {word_count} words" in prompt_text
        assert "Draft directly addresses the essay prompt" in prompt_text
        assert "All details match the outline provided" in prompt_text
        assert "JSON format is correct and parseable" in prompt_text
    
    def test_word_count_range_variables(self):
        """Test that word count range variables are included."""
        new_vars = {"word_count_min", "word_count_max"}
        assert new_vars.issubset(set(DRAFT_PROMPT.input_variables))
    
    def test_final_validation_check(self):
        """Test that final validation check is emphasized."""
        prompt_text = str(DRAFT_PROMPT.template)
        
        # Check for final validation emphasis
        assert "FINAL CHECK**: Only submit if ALL validation criteria are met" in prompt_text


class TestPromptRendering:
    """Test that enhanced prompts can be rendered with proper variables."""
    
    def test_brainstorm_prompt_rendering(self):
        """Test that enhanced brainstorm prompt renders correctly."""
        template_vars = {
            "essay_prompt": "Test prompt",
            "profile": "Test profile",
            "college_name": "Test College",
            "college_story_history": ["Story 1"],
            "cross_college_suggestions": ["Story 2"],
            "prompt_type": "identity",
            "recommended_categories": ["heritage", "family"],
            "today": "2024-01-01"
        }
        
        # Should render without errors
        rendered = render_template(BRAINSTORM_PROMPT, **template_vars)
        assert isinstance(rendered, str)
        assert len(rendered) > 0
        assert "Test prompt" in rendered
        assert "identity" in rendered
    
    def test_outline_prompt_rendering(self):
        """Test that enhanced outline prompt renders correctly."""
        template_vars = {
            "story": "Test story",
            "essay_prompt": "Test prompt", 
            "word_count": 650,
            "hook_words": 81,
            "context_words": 146,
            "conflict_words": 179,
            "growth_words": 179,
            "reflection_words": 114,
            "hook_percentage": "10-15",
            "context_percentage": "20-25",
            "conflict_percentage": "25-30",
            "growth_percentage": "25-30",
            "reflection_percentage": "15-20",
            "today": "2024-01-01"
        }
        
        # Should render without errors
        rendered = render_template(OUTLINE_PROMPT, **template_vars)
        assert isinstance(rendered, str)
        assert len(rendered) > 0
        assert "Test story" in rendered
        assert "650" in rendered
        assert "81" in rendered  # hook_words
    
    def test_draft_prompt_rendering(self):
        """Test that enhanced draft prompt renders correctly."""
        template_vars = {
            "outline": "Test outline",
            "voice_profile": "Test voice",
            "word_count": 650,
            "word_count_min": 585,
            "word_count_max": 715,
            "today": "2024-01-01"
        }
        
        # Should render without errors
        rendered = render_template(DRAFT_PROMPT, **template_vars)
        assert isinstance(rendered, str)
        assert len(rendered) > 0
        assert "Test outline" in rendered
        assert "650" in rendered
        assert "585" in rendered  # word_count_min
        assert "715" in rendered  # word_count_max


class TestBackwardsCompatibility:
    """Test that enhanced prompts maintain backwards compatibility."""
    
    def test_brainstorm_existing_variables(self):
        """Test that existing brainstorm variables still work."""
        existing_vars = {"essay_prompt", "profile", "today"}
        assert existing_vars.issubset(set(BRAINSTORM_PROMPT.input_variables))
    
    def test_outline_existing_variables(self):
        """Test that existing outline variables still work."""
        existing_vars = {"story", "essay_prompt", "word_count", "today"}
        assert existing_vars.issubset(set(OUTLINE_PROMPT.input_variables))
    
    def test_draft_existing_variables(self):
        """Test that existing draft variables still work."""
        existing_vars = {"outline", "voice_profile", "word_count", "today"}
        assert existing_vars.issubset(set(DRAFT_PROMPT.input_variables))


class TestPromptQuality:
    """Test that enhanced prompts maintain high quality standards."""
    
    def test_prompt_length_reasonable(self):
        """Test that prompts are not excessively long."""
        # Should be comprehensive but not overwhelming
        assert len(str(BRAINSTORM_PROMPT.template)) < 15000
        assert len(str(OUTLINE_PROMPT.template)) < 10000
        assert len(str(DRAFT_PROMPT.template)) < 12000
    
    def test_prompts_have_clear_structure(self):
        """Test that prompts have clear structural organization."""
        for prompt_name, prompt in [
            ("brainstorm", BRAINSTORM_PROMPT),
            ("outline", OUTLINE_PROMPT),
            ("draft", DRAFT_PROMPT)
        ]:
            prompt_text = str(prompt.template)
            
            # Should have clear sections
            assert "MISSION" in prompt_text
            assert "REQUIREMENTS" in prompt_text
            assert "OUTPUT" in prompt_text
            assert "CHECKLIST" in prompt_text
            assert "INSTRUCTION" in prompt_text
    
    def test_prompts_emphasize_quality(self):
        """Test that prompts emphasize quality and authenticity."""
        for prompt_name, prompt in [
            ("brainstorm", BRAINSTORM_PROMPT),
            ("outline", OUTLINE_PROMPT),
            ("draft", DRAFT_PROMPT)
        ]:
            prompt_text = str(prompt.template)
            
            # Should emphasize quality
            assert "authentic" in prompt_text.lower()
            assert "quality" in prompt_text.lower()
            assert "compelling" in prompt_text.lower() 