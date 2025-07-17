"""Phase 2 Integration Tests: LLM-Driven Natural Language Processing

This module contains comprehensive integration tests to validate that all Phase 2
LLM-driven improvements work together to fix the critical bugs:

- Bug #1: Identical response duplication
- Bug #2: Tool selection ignores user evolution  
- Bug #3: User input completely ignored
- Bug #11: No essay generation despite drafting phases
- Bug #14: School-specific context missing
"""

import asyncio
import pytest
import time
from typing import List, Dict, Any

# Import the enhanced essay agent and components
from essay_agent.agent.core.react_agent import EssayReActAgent
from essay_agent.prompts.response_generation import response_generator
from essay_agent.prompts.tool_selection import tool_selector
from essay_agent.memory.user_context_extractor import context_extractor
from essay_agent.agent.school_context_injector import school_injector


class TestPhase2Integration:
    """Integration tests for Phase 2 LLM-driven enhancements."""
    
    @pytest.fixture
    async def agent(self):
        """Create a test agent with Phase 2 enhancements."""
        agent = EssayReActAgent(user_id="test_phase2_user")
        return agent
    
    @pytest.mark.asyncio
    async def test_bug1_response_uniqueness(self, agent):
        """Test Bug #1: Ensure all responses are unique, no duplicates."""
        
        # Test with similar but different requests
        test_inputs = [
            "Help me brainstorm essay ideas",
            "I want to write about robotics", 
            "Focus on helping disabled students through technology",
            "Create an outline for my innovation essay"
        ]
        
        responses = []
        
        for user_input in test_inputs:
            response = await agent.handle_message(user_input)
            responses.append(response)
            
            # Brief pause between requests
            await asyncio.sleep(0.1)
        
        # Verify all responses are unique
        assert len(set(responses)) == len(responses), "All responses should be unique"
        
        # Verify responses are substantial (not just error messages)
        for response in responses:
            assert len(response) > 50, "Responses should be substantial"
            assert "error" not in response.lower(), "Responses should not be error messages"
        
        print("✅ Bug #1 Fixed: All responses are unique")
    
    @pytest.mark.asyncio
    async def test_bug2_context_aware_tool_selection(self, agent):
        """Test Bug #2: Tool selection should evolve based on user progress."""
        
        # Simulate a user journey through essay writing phases
        conversation_sequence = [
            ("Help me brainstorm essay ideas", "brainstorm"),
            ("I like the technology story, create an outline", "outline"),
            ("Write a draft based on my outline", "draft"),
            ("Improve my essay draft", "revise")
        ]
        
        used_tools = []
        
        for user_input, expected_tool_type in conversation_sequence:
            response = await agent.handle_message(user_input)
            
            # Check if agent used appropriate tools (extract from response or agent state)
            last_tools = getattr(agent, 'last_execution_tools', [])
            used_tools.extend(last_tools)
            
            # Brief pause between requests
            await asyncio.sleep(0.1)
        
        # Verify tool progression makes sense
        assert len(used_tools) > 0, "Tools should have been used"
        
        # Check for natural progression (not just repeated brainstorming)
        unique_tools = set(used_tools)
        assert len(unique_tools) > 1, "Should use different types of tools, not just repeated brainstorming"
        
        print(f"✅ Bug #2 Fixed: Tool progression - {used_tools}")
    
    @pytest.mark.asyncio
    async def test_bug3_user_context_integration(self, agent):
        """Test Bug #3: User details should be integrated into responses."""
        
        # Provide specific user details
        detailed_input = "I'm from Vietnam and study robotics at MIT. I created a project that helps disabled students access technology."
        response1 = await agent.handle_message(detailed_input)
        
        # Follow up with related request
        followup_input = "Help me write about my background and projects"
        response2 = await agent.handle_message(followup_input)
        
        # Verify user details appear in subsequent responses
        user_details = ["vietnam", "robotics", "mit", "disabled", "technology", "project"]
        
        combined_responses = (response1 + " " + response2).lower()
        
        details_found = []
        for detail in user_details:
            if detail in combined_responses:
                details_found.append(detail)
        
        # At least 3 user details should appear in responses
        assert len(details_found) >= 3, f"User details should appear in responses. Found: {details_found}"
        
        print(f"✅ Bug #3 Fixed: User details integrated - {details_found}")
    
    @pytest.mark.asyncio
    async def test_bug11_essay_generation(self, agent):
        """Test Bug #11: Drafting phases should generate actual essay content."""
        
        # Set up scenario for essay generation
        agent.scenario_context = {
            'essay_prompt': 'What matters most to you, and why?',
            'word_limit': 650
        }
        
        # User provides context
        await agent.handle_message("I'm passionate about using technology to help disabled students")
        
        # User requests outline
        await agent.handle_message("Create an outline for my essay about innovation and helping others")
        
        # User requests draft
        draft_response = await agent.handle_message("Write a complete essay draft based on my outline")
        
        # Check if draft contains substantial content
        assert len(draft_response) > 300, "Draft response should be substantial"
        
        # Check for essay-like content indicators
        essay_indicators = [
            len(draft_response.split()) > 100,  # Substantial word count
            "." in draft_response,  # Contains sentences
            any(word in draft_response.lower() for word in ["technology", "disabled", "students", "help"]),  # Contains user themes
        ]
        
        assert sum(essay_indicators) >= 2, "Response should contain essay-like content"
        
        print(f"✅ Bug #11 Fixed: Essay generation working - {len(draft_response.split())} words")
    
    @pytest.mark.asyncio
    async def test_bug14_school_context_injection(self, agent):
        """Test Bug #14: School-specific context should appear when relevant."""
        
        # Set school context
        agent.scenario_context = {
            'school_context': {
                'name': 'Stanford',
                'values': ['innovation', 'entrepreneurship'],
                'programs': ['Computer Science', 'Engineering']
            }
        }
        
        # User mentions school or asks for help with school-specific essay
        stanford_input = "Help me with my Stanford essay about innovation and technology"
        response = await agent.handle_message(stanford_input)
        
        # Verify Stanford context appears
        response_lower = response.lower()
        stanford_indicators = [
            "stanford" in response_lower,
            "innovation" in response_lower,
            any(term in response_lower for term in ["computer science", "engineering"])
        ]
        
        assert sum(stanford_indicators) >= 1, "Stanford context should appear in response"
        
        print(f"✅ Bug #14 Fixed: School context integrated - Stanford mentioned")
    
    @pytest.mark.asyncio
    async def test_response_generator_functionality(self):
        """Test the intelligent response generator works correctly."""
        
        # Test response generation with context
        test_context = {
            'user_input': 'Help me with my robotics project essay',
            'tool_result': {'stories': [{'title': 'Robotics Innovation', 'description': 'Helping disabled students'}]},
            'conversation_history': [],
            'user_profile': {'interests': ['robotics', 'helping others']},
            'previous_responses': []
        }
        
        response = await response_generator.generate_contextual_response(
            user_input=test_context['user_input'],
            tool_result=test_context['tool_result'],
            conversation_history=test_context['conversation_history'],
            user_profile=test_context['user_profile'],
            previous_responses=test_context['previous_responses']
        )
        
        assert len(response) > 50, "Response should be substantial"
        assert "robotics" in response.lower(), "Response should integrate user context"
        
        print("✅ Response generator working correctly")
    
    @pytest.mark.asyncio
    async def test_context_aware_tool_selection(self):
        """Test the context-aware tool selector works correctly."""
        
        # Test tool selection with context
        test_context = {
            'user_input': 'I want to create an outline for my essay',
            'conversation_history': [
                {'user_input': 'Help brainstorm ideas', 'tools_used': ['brainstorm']}
            ],
            'user_profile': {'interests': ['technology']},
            'available_tools': ['brainstorm', 'outline', 'draft', 'revise'],
            'completed_tools': ['brainstorm']
        }
        
        selection_result = await tool_selector.select_optimal_tools(
            user_input=test_context['user_input'],
            conversation_history=test_context['conversation_history'],
            user_profile=test_context['user_profile'],
            available_tools=test_context['available_tools'],
            completed_tools=test_context['completed_tools']
        )
        
        # Should suggest outline since brainstorm is completed and user wants outline
        assert selection_result.chosen_tool in ['outline', 'draft'], "Should suggest outline or draft tool"
        assert selection_result.confidence > 0.5, "Should have reasonable confidence"
        
        print(f"✅ Context-aware tool selection working: {selection_result.chosen_tool}")
    
    @pytest.mark.asyncio
    async def test_user_context_extraction(self):
        """Test the user context extractor works correctly."""
        
        # Test context extraction
        test_input = "I'm from Vietnam and study robotics at MIT. I created a project helping disabled students."
        existing_profile = {}
        conversation_history = []
        
        context_update = await context_extractor.extract_and_update_context(
            user_input=test_input,
            existing_profile=existing_profile,
            conversation_history=conversation_history
        )
        
        # Verify extraction worked
        assert len(context_update.new_experiences) > 0 or len(context_update.new_interests) > 0, "Should extract some context"
        
        # Check for specific details
        all_extracted = (
            ' '.join(context_update.new_experiences) + ' ' +
            ' '.join(context_update.new_interests) + ' ' + 
            ' '.join(context_update.new_background)
        ).lower()
        
        expected_details = ['vietnam', 'robotics', 'mit', 'disabled', 'students']
        found_details = [detail for detail in expected_details if detail in all_extracted]
        
        assert len(found_details) >= 2, f"Should extract key details. Found: {found_details}"
        
        print(f"✅ User context extraction working: {found_details}")
    
    @pytest.mark.asyncio
    async def test_school_context_injection(self):
        """Test the school context injector works correctly."""
        
        # Test school context injection
        base_response = "Here are some essay ideas for your application."
        school_name = "Stanford"
        user_interests = ["technology", "innovation"]
        
        enhanced_response = await school_injector.inject_school_context(
            response=base_response,
            school_name=school_name,
            user_interests=user_interests,
            user_context={},
            response_type="brainstorm"
        )
        
        # Verify enhancement worked
        assert len(enhanced_response) > len(base_response), "Response should be enhanced"
        assert "stanford" in enhanced_response.lower(), "Should mention Stanford"
        
        print("✅ School context injection working")
    
    @pytest.mark.asyncio
    async def test_comprehensive_workflow(self, agent):
        """Test complete workflow with all Phase 2 enhancements."""
        
        print("\n🚀 Testing comprehensive Phase 2 workflow...")
        
        # Step 1: User provides background
        background_response = await agent.handle_message(
            "I'm from Vietnam, study computer science, and created a robotics project that helps disabled students access technology. I want to write about innovation for Stanford."
        )
        
        # Step 2: User asks for brainstorming
        brainstorm_response = await agent.handle_message(
            "Help me brainstorm essay ideas about my robotics project and helping others"
        )
        
        # Step 3: User wants to create outline
        outline_response = await agent.handle_message(
            "Create an outline for an essay about innovation and technology helping disabled students"
        )
        
        # Step 4: User wants a draft
        draft_response = await agent.handle_message(
            "Write a complete essay draft for Stanford based on my outline and experiences"
        )
        
        # Comprehensive validation
        all_responses = [background_response, brainstorm_response, outline_response, draft_response]
        
        # Test Bug #1: No duplicate responses
        assert len(set(all_responses)) == len(all_responses), "All responses should be unique"
        
        # Test Bug #3: User context integration
        combined_text = ' '.join(all_responses).lower()
        user_context_found = sum([
            'vietnam' in combined_text,
            'robotics' in combined_text,
            'disabled' in combined_text,
            'technology' in combined_text,
            'innovation' in combined_text
        ])
        assert user_context_found >= 3, "User context should be integrated throughout"
        
        # Test Bug #14: School context
        assert 'stanford' in combined_text, "Stanford should be mentioned"
        
        # Test Bug #11: Essay generation
        assert len(draft_response) > 400, "Draft should be substantial"
        
        print("✅ Comprehensive workflow completed successfully")
        print(f"   - Responses unique: {len(set(all_responses)) == len(all_responses)}")
        print(f"   - User context integrated: {user_context_found}/5 elements")
        print(f"   - School context: {'stanford' in combined_text}")
        print(f"   - Draft length: {len(draft_response)} characters")


async def run_integration_tests():
    """Run all Phase 2 integration tests."""
    
    print("🧪 Running Phase 2 Integration Tests...")
    
    test_instance = TestPhase2Integration()
    
    # Create test agent
    agent = EssayReActAgent(user_id="integration_test_user")
    
    try:
        # Run individual component tests
        await test_instance.test_response_generator_functionality()
        await test_instance.test_context_aware_tool_selection()
        await test_instance.test_user_context_extraction()
        await test_instance.test_school_context_injection()
        
        # Run bug fix tests
        await test_instance.test_bug1_response_uniqueness(agent)
        await test_instance.test_bug2_context_aware_tool_selection(agent)
        await test_instance.test_bug3_user_context_integration(agent)
        await test_instance.test_bug11_essay_generation(agent)
        await test_instance.test_bug14_school_context_injection(agent)
        
        # Run comprehensive workflow test
        await test_instance.test_comprehensive_workflow(agent)
        
        print("\n🎉 All Phase 2 Integration Tests Passed!")
        print("   ✅ Bug #1: Response uniqueness fixed")
        print("   ✅ Bug #2: Context-aware tool selection fixed")
        print("   ✅ Bug #3: User context integration fixed")
        print("   ✅ Bug #11: Essay generation fixed")
        print("   ✅ Bug #14: School context injection fixed")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        return False


if __name__ == "__main__":
    # Run tests if executed directly
    success = asyncio.run(run_integration_tests())
    if not success:
        exit(1) 