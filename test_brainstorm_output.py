#!/usr/bin/env python3
"""
Test Smart Brainstorm Tool - Full Output
=======================================

Run just the smart_brainstorm tool to see complete output.
"""

import asyncio
import json
from essay_agent.state_manager import EssayStateManager
from essay_agent.tools.independent_tools import SmartBrainstormTool

def create_alex_kim_state():
    """Create test state with Alex Kim's profile for Stanford essay"""
    manager = EssayStateManager()
    
    # Create state for Alex Kim's Stanford essay
    state = manager.create_new_essay(
        user_id="alex_kim",
        essay_prompt="Stanford students possess an intellectual vitality. Tell us about an idea or experience that has been intellectually exciting for you.",
        college="Stanford",
        word_limit=650
    )
    
    return state

def test_brainstorm_full_output():
    """Test smart brainstorm and show complete output"""
    print("🚀 Testing Smart Brainstorm Tool")
    print("="*50)
    
    # Create state
    state = create_alex_kim_state()
    
    print(f"User Profile: {state.user_profile.get('name', 'Unknown')}")
    print(f"Essay Prompt: {state.essay_prompt}")
    print(f"College: {state.college}")
    print(f"Word Limit: {state.word_limit}")
    print("")
    
    # Initialize brainstorm tool
    brainstorm_tool = SmartBrainstormTool()
    
    print("🧠 Running Smart Brainstorm...")
    print("-" * 50)
    
    try:
        # Execute brainstorm
        result = brainstorm_tool._run(state)
        
        print("✅ BRAINSTORM SUCCESS!")
        print("="*50)
        
        # Show complete results
        if 'ideas' in result:
            ideas = result['ideas']
            print(f"Generated {len(ideas)} ideas:")
            print("")
            
            for i, idea in enumerate(ideas, 1):
                print(f"💡 IDEA {i}:")
                print(f"   Title: {idea.get('title', 'No title')}")
                print(f"   Description: {idea.get('description', 'No description')}")
                if 'personal_connection' in idea:
                    print(f"   Personal Connection: {idea['personal_connection']}")
                if 'intellectual_angle' in idea:
                    print(f"   Intellectual Angle: {idea['intellectual_angle']}")
                print("")
        
        # Show any additional result data
        print("📋 FULL RESULT DATA:")
        print("-" * 30)
        print(json.dumps(result, indent=2))
        
        # Show updated state
        print("")
        print("🔄 UPDATED STATE:")
        print("-" * 30)
        print(f"Ideas in state: {len(state.brainstormed_ideas)}")
        if state.brainstormed_ideas:
            print("State contains:")
            for idea in state.brainstormed_ideas:
                print(f"  - {idea.get('title', 'Untitled')}")
        
    except Exception as e:
        print(f"❌ BRAINSTORM FAILED: {e}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    test_brainstorm_full_output() 