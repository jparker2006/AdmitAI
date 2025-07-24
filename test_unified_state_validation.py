#!/usr/bin/env python3
"""
Test Unified State Tools Critical Fixes
======================================

Validates that our fixes for user profile loading, output structure, 
and state updates work correctly.
"""

import json
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from essay_agent.models.agent_state import EssayAgentState, create_initial_state
from essay_agent.state_manager import EssayStateManager
from essay_agent.tools.independent_tools import SmartBrainstormTool
from essay_agent.memory.simple_memory import SimpleMemory


def test_profile_loading():
    """Test that Alex Kim's profile loads correctly"""
    
    print("\n" + "="*60)
    print("🧪 TEST 1: Profile Loading")
    print("="*60)
    
    # Test SimpleMemory.load directly
    try:
        memory = SimpleMemory()
        profile = memory.load("alex_kim")
        
        print(f"✅ Profile loaded successfully")
        print(f"📦 Profile type: {type(profile)}")
        
        if hasattr(profile, 'model_dump'):
            profile_dict = profile.model_dump()
            print(f"📋 Profile keys: {list(profile_dict.keys())}")
            
            # Check for Alex Kim's specific data
            user_info = profile_dict.get("user_info", {})
            print(f"👤 User name: {user_info.get('name', 'NOT FOUND')}")
            
            academic_profile = profile_dict.get("academic_profile", {})
            activities = academic_profile.get("activities", [])
            print(f"🎯 Activities count: {len(activities)}")
            
            if activities:
                for i, activity in enumerate(activities):
                    name = activity.get("name", "unnamed")
                    role = activity.get("role", "no role")
                    print(f"   {i+1}. {role} of {name}")
                    
        return True
        
    except Exception as e:
        print(f"❌ Profile loading failed: {e}")
        return False


def test_state_manager_profile_integration():
    """Test that StateManager properly loads and converts profile"""
    
    print("\n" + "="*60)
    print("🧪 TEST 2: State Manager Profile Integration")
    print("="*60)
    
    try:
        manager = EssayStateManager()
        
        # Create new essay session for Alex Kim
        state = manager.create_new_essay(
            user_id="alex_kim",
            essay_prompt="Tell us about a time you were challenged by a perspective that differed from your own.",
            college="Stanford",
            word_limit=650
        )
        
        print(f"✅ Essay state created successfully")
        print(f"👤 User in state: {state.user_id}")
        print(f"📋 Profile in state: {type(state.user_profile)}")
        print(f"📝 Essay prompt: {state.essay_prompt[:50]}...")
        
        # Check profile data structure
        if state.user_profile:
            print(f"🎯 Profile keys: {list(state.user_profile.keys())}")
            
            user_info = state.user_profile.get("user_info", {})
            name = user_info.get("name", "NOT FOUND")
            print(f"👤 Name in state: {name}")
            
            if name == "Alex Kim":
                print("✅ Profile loading SUCCESS - Alex Kim found!")
                return True
            else:
                print(f"❌ Profile loading FAILED - Expected 'Alex Kim', got '{name}'")
                return False
        else:
            print("❌ No profile data in state")
            return False
        
    except Exception as e:
        print(f"❌ State manager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_smart_brainstorm_tool():
    """Test SmartBrainstormTool with Alex Kim's profile"""
    
    print("\n" + "="*60)
    print("🧪 TEST 3: SmartBrainstormTool Output Quality")
    print("="*60)
    
    try:
        # Create state with Alex Kim's profile
        manager = EssayStateManager()
        state = manager.create_new_essay(
            user_id="alex_kim",
            essay_prompt="Describe a problem you've solved or a problem you'd like to solve.",
            college="Stanford",
            word_limit=650
        )
        
        # Create and run brainstorm tool
        tool = SmartBrainstormTool()
        result = tool._run(state)
        
        print(f"✅ Tool executed successfully")
        print(f"📦 Result type: {type(result)}")
        print(f"🎯 Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
        
        # Check for ideas
        ideas = result.get("ideas", [])
        print(f"💡 Ideas generated: {len(ideas)}")
        
        # Validate idea structure
        for i, idea in enumerate(ideas):
            print(f"\n📋 Idea {i+1}:")
            print(f"   Title: {idea.get('title', 'MISSING')}")
            print(f"   Description: {idea.get('description', 'MISSING')[:60]}...")
            
            # Check for new schema fields
            personal_connection = idea.get('personal_connection', 'MISSING')
            intellectual_angle = idea.get('intellectual_angle', 'MISSING')
            
            print(f"   Personal Connection: {personal_connection[:40]}...")
            print(f"   Intellectual Angle: {intellectual_angle[:40]}...")
            
            # Check if it references Alex's background
            title_and_desc = f"{idea.get('title', '')} {idea.get('description', '')}".lower()
            business_terms = ["investment", "business", "tutoring", "model un", "financial", "club"]
            has_business_ref = any(term in title_and_desc for term in business_terms)
            
            if has_business_ref:
                print(f"   ✅ References business background!")
            else:
                print(f"   ⚠️ No clear business background reference")
        
        # Check state was updated properly
        print(f"\n🏛️ State content library keys: {list(state.content_library.keys())}")
        
        # Check brainstormed_ideas property (which accesses content_library)
        state_ideas = state.brainstormed_ideas
        state_ideas_count = len(state_ideas)
        print(f"🏛️ State brainstormed_ideas count: {state_ideas_count}")
        
        # Also check content_library directly
        content_lib_ideas = state.content_library.get("ideas", [])
        content_lib_count = len(content_lib_ideas)
        print(f"🏛️ Content library ideas count: {content_lib_count}")
        
        # Both should match the number of generated ideas
        if state_ideas_count == len(ideas) and content_lib_count > 0:
            print("✅ State update SUCCESS - brainstormed_ideas property working correctly")
            return True
        else:
            print(f"❌ State update issues: tool={len(ideas)}, brainstormed_ideas={state_ideas_count}, content_lib={content_lib_count}")
            return False
        
    except Exception as e:
        print(f"❌ SmartBrainstormTool test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_output_schema_consistency():
    """Test that all tools produce consistent output schemas"""
    
    print("\n" + "="*60)
    print("🧪 TEST 4: Output Schema Consistency")
    print("="*60)
    
    try:
        # Test the parsing function directly
        from essay_agent.tools.independent_tools import SmartBrainstormTool
        
        tool = SmartBrainstormTool()
        
        # Test with various response formats
        test_responses = [
            "1. Starting Investment Club - I founded our school's first investment club. Shows leadership and financial literacy.",
            "• Business Challenge: Launched tutoring business during family financial crisis\n• Leadership Growth: Led Model UN with 200 participants",
            "**Breaking Financial Barriers** - When my family faced financial difficulties, I started a tutoring business that generated $15,000 in revenue."
        ]
        
        all_consistent = True
        
        for i, response in enumerate(test_responses):
            print(f"\n📝 Testing response format {i+1}:")
            print(f"   Input: {response[:50]}...")
            
            ideas = tool._parse_ideas(response)
            
            for j, idea in enumerate(ideas):
                required_fields = ["title", "description", "personal_connection", "intellectual_angle"]
                missing_fields = [field for field in required_fields if field not in idea]
                
                if missing_fields:
                    print(f"   ❌ Idea {j+1} missing fields: {missing_fields}")
                    all_consistent = False
            else:
                    print(f"   ✅ Idea {j+1} has all required fields")
        
        if all_consistent:
            print("\n✅ Schema consistency SUCCESS")
            return True
        else:
            print("\n❌ Schema consistency FAILED")
            return False
            
    except Exception as e:
        print(f"❌ Schema consistency test failed: {e}")
        return False


def main():
    """Run all critical fix validation tests"""
    
    print("🚀 UNIFIED STATE TOOLS - CRITICAL FIXES VALIDATION")
    print("=" * 60)
    print("Testing fixes for:")
    print("  1. User profile loading (Alex Kim → Unknown)")
    print("  2. Output structure consistency")  
    print("  3. State update logic errors")
    print("  4. Personalization quality")
    
    # Track test results
    results = {}
    
    # Run tests
    results["profile_loading"] = test_profile_loading()
    results["state_manager"] = test_state_manager_profile_integration()
    results["brainstorm_tool"] = test_smart_brainstorm_tool()
    results["schema_consistency"] = test_output_schema_consistency()
    
    # Summary
    print("\n" + "="*60)
    print("🎯 TEST RESULTS SUMMARY")
    print("="*60)
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {test_name}: {status}")
    
    print(f"\n📊 Overall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 ALL TESTS PASSED - Fixes are working!")
        return True
    else:
        print("⚠️ Some tests failed - Need more fixes")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 