#!/usr/bin/env python3
"""
Utility script to run evaluation conversations and extract readable conversation content.

This script helps bridge the gap between evaluation results and actual conversation content
by running evaluations and immediately displaying the real user inputs and agent responses.
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

# Add the essay_agent package to path
sys.path.insert(0, str(Path(__file__).parent))

from essay_agent.eval.conversation_runner import ConversationRunner
from essay_agent.eval.conversational_scenarios import get_scenario_by_id, ALL_SCENARIOS
from essay_agent.eval.real_profiles import get_profile_by_id, ALL_PROFILES


def print_conversation_content(result):
    """Extract and beautifully display the actual conversation content."""
    
    print(f"\n{'='*80}")
    print(f"🗨️  ACTUAL CONVERSATION CONTENT")
    print(f"{'='*80}")
    print(f"Scenario: {result.scenario_id}")
    print(f"Profile: {result.user_profile_id}")
    print(f"Total Turns: {result.total_turns}")
    print(f"Duration: {result.total_duration_seconds:.1f}s")
    print(f"Success Score: {result.overall_success_score:.2f}")
    
    print(f"\n{'='*80}")
    print(f"TURN-BY-TURN CONVERSATION")
    print(f"{'='*80}")
    
    for turn in result.conversation_turns:
        print(f"\n--- TURN {turn.turn_number} [{turn.phase_name}] ---")
        print(f"⏰ {turn.timestamp.strftime('%H:%M:%S')}")
        print(f"🔧 Tools Used: {', '.join(turn.tools_used) if turn.tools_used else 'None'}")
        print(f"💾 Memory Accessed: {', '.join(turn.memory_accessed) if turn.memory_accessed else 'None'}")
        print(f"⚡ Response Time: {turn.response_time_seconds:.2f}s")
        print(f"📊 Behavior Match: {turn.expected_behavior_match:.2f}")
        
        print(f"\n👤 USER INPUT:")
        print(f"    {turn.user_input}")
        
        print(f"\n🤖 AGENT RESPONSE:")
        # Pretty format the agent response with proper indentation
        response_lines = turn.agent_response.split('\n')
        for line in response_lines:
            print(f"    {line}")
        
        print(f"\n✅ Success Indicators Met: {', '.join(turn.success_indicators_met) if turn.success_indicators_met else 'None'}")
        print(f"📝 Word Count: {turn.word_count}")
    
    # Summary statistics
    print(f"\n{'='*80}")
    print(f"CONVERSATION ANALYSIS")
    print(f"{'='*80}")
    
    total_words = sum(turn.word_count for turn in result.conversation_turns)
    avg_response_time = sum(turn.response_time_seconds for turn in result.conversation_turns) / len(result.conversation_turns)
    
    print(f"📝 Total Agent Words: {total_words}")
    print(f"⚡ Average Response Time: {avg_response_time:.2f}s")
    print(f"🔧 Unique Tools Used: {result.unique_tools_used}")
    print(f"💾 Memory Utilization Score: {result.memory_utilization_score:.2f}")
    print(f"🎯 Conversation Naturalness: {result.conversation_naturalness:.2f}")
    print(f"🎯 Goal Achievement: {result.goal_achievement:.2f}")
    
    if result.tools_used_summary:
        print(f"\n🔧 TOOL USAGE BREAKDOWN:")
        for tool, count in result.tools_used_summary.items():
            print(f"    {tool}: {count}x")
    
    if result.issues_encountered:
        print(f"\n⚠️  ISSUES ENCOUNTERED:")
        for issue in result.issues_encountered:
            print(f"    - {issue}")
    
    if result.notable_successes:
        print(f"\n✅ NOTABLE SUCCESSES:")
        for success in result.notable_successes:
            print(f"    - {success}")


async def run_evaluation_with_conversation_extract(scenario_id: str, profile_id: str = None, save_to_file: bool = True):
    """Run evaluation and extract conversation content."""
    
    # Load scenario
    scenario = get_scenario_by_id(scenario_id)
    if not scenario:
        print(f"❌ Scenario '{scenario_id}' not found")
        print("\n📋 Available scenarios:")
        for s in ALL_SCENARIOS[:10]:  # Show first 10
            print(f"    {s.eval_id}: {s.name}")
        return None
    
    # Load profile
    profile = None
    if profile_id:
        profile = get_profile_by_id(profile_id)
        if not profile:
            print(f"❌ Profile '{profile_id}' not found")
            print("\n👥 Available profiles:")
            for p in ALL_PROFILES[:5]:  # Show first 5
                print(f"    {p.profile_id}: {p.name}")
            return None
    
    print(f"🚀 Running evaluation with conversation extraction...")
    print(f"   Scenario: {scenario.name}")
    print(f"   Profile: {profile.name if profile else 'Auto-selected'}")
    
    # Run the evaluation
    runner = ConversationRunner(verbose=False)  # Don't duplicate output
    result = await runner.execute_evaluation(scenario, profile)
    
    # Display the conversation content
    print_conversation_content(result)
    
    # Optionally save to file
    if save_to_file:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"conversation_extract_{scenario_id}_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(result.to_dict(), f, indent=2, default=str)
        
        print(f"\n💾 Full conversation data saved to: {filename}")
    
    return result


def main():
    """Main function with command-line interface."""
    
    if len(sys.argv) < 2:
        print("Usage: python extract_eval_conversations.py <scenario_id> [profile_id]")
        print("\nExamples:")
        print("  python extract_eval_conversations.py CONV-001-new-user-stanford-identity")
        print("  python extract_eval_conversations.py CONV-002-returning-user-add-details first_gen_college_student")
        print("\nThis will run the evaluation and show you the actual conversation content!")
        sys.exit(1)
    
    scenario_id = sys.argv[1]
    profile_id = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Run the evaluation
    result = asyncio.run(run_evaluation_with_conversation_extract(scenario_id, profile_id))
    
    if result:
        print(f"\n🎉 Evaluation complete! You can now see exactly what the agent said to users.")


if __name__ == "__main__":
    main() 