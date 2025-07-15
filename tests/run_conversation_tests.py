#!/usr/bin/env python3
"""
Quick script to run conversation flow tests and demonstrate the testing framework.

Usage:
  python tests/run_conversation_tests.py --demo       # Show available fixtures  
  python tests/run_conversation_tests.py --quick      # Run one happy path test
  python tests/run_conversation_tests.py --all        # Run all tests
"""

import sys
import os
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tests.fixtures import (
    TEST_PROFILES, ESSAY_PROMPTS, get_scenario_summary,
    get_test_scenario, ALL_SCENARIOS
)
from tests.conversation_flow_tests import ConversationFlowTestRunner


def show_demo():
    """Demonstrate the test fixtures"""
    print("🎭 Essay Agent Test Fixtures Demo")
    print("=" * 50)
    
    print("\n📊 Test Overview:")
    summary = get_scenario_summary()
    for key, value in summary.items():
        print(f"  {key}: {value}")
    
    print("\n👥 Available User Profiles:")
    for profile_type, profile in TEST_PROFILES.items():
        user_info = profile["user_info"]
        print(f"  • {profile_type}: {user_info['name']} ({user_info['intended_major']})")
    
    print("\n📝 Available Essay Prompts:")
    prompt_count = {}
    for prompt_id, prompt in ESSAY_PROMPTS.items():
        college = prompt["college"]
        essay_type = prompt["type"]
        word_limit = prompt["word_limit"]
        print(f"  • {prompt_id}: {college} {essay_type} ({word_limit} words)")
        prompt_count[college] = prompt_count.get(college, 0) + 1
    
    print(f"\n🏫 Prompts by College:")
    for college, count in prompt_count.items():
        print(f"  • {college}: {count} prompts")
    
    print("\n🧪 Sample Test Scenarios:")
    for scenario in ALL_SCENARIOS[:3]:  # Show first 3
        print(f"  • {scenario.id}: {scenario.name}")
        print(f"    Profile: {scenario.profile_type}")
        print(f"    Prompt: {scenario.prompt_id}")
        print(f"    Steps: {len(scenario.conversation_flow)}")


def run_quick_test():
    """Run a single happy path test to verify everything works"""
    print("🚀 Running Quick Test - Happy Path Scenario")
    print("=" * 50)
    
    # Get the first happy path scenario
    scenario = get_test_scenario("HP-001")
    if not scenario:
        print("❌ Test scenario HP-001 not found")
        return False
    
    print(f"📋 Running: {scenario.name}")
    print(f"   Profile: {scenario.profile_type}")
    print(f"   Prompt: {scenario.prompt_id}")
    
    # Create test runner
    runner = ConversationFlowTestRunner()
    
    try:
        # Run the scenario
        result = runner.run_scenario(scenario)
        
        # Print results
        status = "✅ PASS" if result.success else "❌ FAIL"
        print(f"\n{status} Test Result:")
        print(f"   Execution Time: {result.execution_time:.1f}s")
        print(f"   Tool Results: {len(result.tool_results)}")
        print(f"   Conversation Turns: {len(result.conversation_responses)}")
        
        if result.errors:
            print(f"   Errors: {len(result.errors)}")
            for error in result.errors[:3]:
                print(f"     • {error}")
        
        if result.validation_errors:
            print(f"   Validation Errors: {len(result.validation_errors)}")
            for error in result.validation_errors[:3]:
                print(f"     • {error}")
        
        return result.success
        
    except Exception as e:
        print(f"❌ Test execution failed: {str(e)}")
        return False


def run_all_tests():
    """Run all conversation flow tests"""
    print("🧪 Running All Conversation Flow Tests")
    print("=" * 50)
    
    runner = ConversationFlowTestRunner()
    
    try:
        summary = runner.run_test_suite()
        
        print(f"\n🎯 Final Results:")
        print(f"   Pass Rate: {summary['pass_rate']:.1f}%")
        print(f"   Total Tests: {summary['total_tests']}")
        print(f"   Passed: {summary['passed_tests']}")
        print(f"   Failed: {summary['failed_tests']}")
        
        return summary['pass_rate'] >= 90.0
        
    except Exception as e:
        print(f"❌ Test suite execution failed: {str(e)}")
        return False


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Conversation Flow Test Runner")
    parser.add_argument("--demo", action="store_true", help="Show test fixtures demo")
    parser.add_argument("--quick", action="store_true", help="Run quick test (one scenario)")
    parser.add_argument("--all", action="store_true", help="Run all tests")
    
    args = parser.parse_args()
    
    if args.demo:
        show_demo()
        return 0
    elif args.quick:
        success = run_quick_test()
        return 0 if success else 1
    elif args.all:
        success = run_all_tests()
        return 0 if success else 1
    else:
        print("❓ No action specified. Use --demo, --quick, or --all")
        parser.print_help()
        return 1


if __name__ == "__main__":
    exit(main()) 