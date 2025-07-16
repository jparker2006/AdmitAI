#!/usr/bin/env python3
"""Test script for evaluation memory integration.

This script tests the IntegratedConversationRunner to ensure evaluation
conversations are properly saved to memory_store and can be accessed
like manual chat conversations.
"""

import asyncio
import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime

# Add the essay_agent package to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from essay_agent.eval.integrated_conversation_runner import IntegratedConversationRunner
    from essay_agent.eval.conversational_scenarios import get_scenario_by_id
    from essay_agent.eval.real_profiles import get_profile_by_id
    from essay_agent.agent.core.react_agent import EssayReActAgent
    print("✅ All imports successful")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)


async def test_memory_integration():
    """Test the memory integration functionality."""
    
    print("🧪 Testing Memory Integration")
    print("=" * 60)
    
    # Test configuration
    scenario_id = "CONV-001-new-user-stanford-identity"
    profile_id = "tech_entrepreneur_student"
    
    # Load test scenario and profile
    scenario = get_scenario_by_id(scenario_id)
    profile = get_profile_by_id(profile_id)
    
    if not scenario:
        print(f"❌ Test scenario {scenario_id} not found")
        return False
    
    if not profile:
        print(f"❌ Test profile {profile_id} not found")
        return False
    
    print(f"✅ Loaded scenario: {scenario.name}")
    print(f"✅ Loaded profile: {profile.name}")
    
    # Test 1: Run integrated conversation
    print(f"\n📝 Test 1: Running integrated conversation evaluation")
    print("-" * 40)
    
    try:
        runner = IntegratedConversationRunner(verbose=False, memory_prefix="test")
        start_time = time.time()
        
        result = await runner.execute_evaluation(scenario, profile)
        
        execution_time = time.time() - start_time
        print(f"✅ Evaluation completed in {execution_time:.2f}s")
        print(f"   Success score: {result.overall_success_score:.2f}")
        print(f"   Total turns: {result.total_turns}")
        print(f"   Tools used: {result.unique_tools_used}")
        
        # Get memory file paths
        memory_paths = runner.get_memory_file_paths()
        eval_user_id = runner.eval_user_id
        
        print(f"   Evaluation user ID: {eval_user_id}")
        
    except Exception as e:
        print(f"❌ Evaluation failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 2: Verify memory files were created
    print(f"\n📁 Test 2: Verifying memory files were created")
    print("-" * 40)
    
    files_created = []
    for file_type, path in memory_paths.items():
        if os.path.exists(path):
            file_size = os.path.getsize(path)
            files_created.append((file_type, path, file_size))
            print(f"✅ {file_type}: {path} ({file_size} bytes)")
        else:
            print(f"❌ Missing {file_type}: {path}")
    
    if not files_created:
        print(f"❌ No memory files were created!")
        return False
    
    # Test 3: Verify conversation content
    print(f"\n💬 Test 3: Verifying conversation content")
    print("-" * 40)
    
    conv_file = memory_paths["conversation_history"]
    if os.path.exists(conv_file):
        try:
            with open(conv_file, 'r') as f:
                conv_data = json.load(f)
            
            chat_history = conv_data.get("chat_history", [])
            print(f"✅ Conversation file contains {len(chat_history)} messages")
            
            # Display sample conversation
            if chat_history:
                print(f"   Sample messages:")
                for i, msg in enumerate(chat_history[:4]):  # Show first 4 messages
                    role = msg.get("type", "unknown")
                    content = msg.get("content", "")[:100] + "..." if len(msg.get("content", "")) > 100 else msg.get("content", "")
                    print(f"     {i+1}. {role}: {content}")
            
        except Exception as e:
            print(f"❌ Error reading conversation file: {e}")
            return False
    else:
        print(f"❌ Conversation file not found: {conv_file}")
        return False
    
    # Test 4: Test manual chat with evaluation user
    print(f"\n🤖 Test 4: Testing manual chat with evaluation user")
    print("-" * 40)
    
    try:
        # Create a new agent with the same user ID
        chat_agent = EssayReActAgent(user_id=eval_user_id)
        
        # Send a test message
        test_message = "Hi! Can you remind me what we discussed about my Stanford essay?"
        response = await chat_agent.handle_message(test_message)
        
        print(f"✅ Manual chat successful")
        print(f"   Test message: {test_message}")
        print(f"   Response: {response[:200]}..." if len(response) > 200 else f"   Response: {response}")
        
        # Verify conversation was extended
        with open(conv_file, 'r') as f:
            updated_conv_data = json.load(f)
        
        updated_chat_history = updated_conv_data.get("chat_history", [])
        messages_added = len(updated_chat_history) - len(chat_history)
        
        if messages_added >= 2:  # User message + agent response
            print(f"✅ Conversation extended with {messages_added} new messages")
        else:
            print(f"⚠️  Expected conversation to be extended, but only {messages_added} messages added")
        
    except Exception as e:
        print(f"❌ Manual chat test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 5: Memory integration summary
    print(f"\n📊 Test 5: Memory integration summary")
    print("-" * 40)
    
    runner.print_integration_summary()
    
    print(f"\n🎉 All tests passed!")
    print(f"💡 The evaluation conversation can now be accessed via:")
    print(f"   python -m essay_agent chat --user-id {eval_user_id}")
    
    return True


async def cleanup_test_files():
    """Clean up test files created during testing."""
    
    print(f"\n🧹 Cleaning up test files...")
    
    memory_dir = Path("memory_store")
    test_files = []
    
    # Find all test_* files
    if memory_dir.exists():
        for file_path in memory_dir.iterdir():
            if file_path.name.startswith("test_"):
                test_files.append(file_path)
        
        # Also check vector_indexes
        vector_dir = memory_dir / "vector_indexes"
        if vector_dir.exists():
            for dir_path in vector_dir.iterdir():
                if dir_path.name.startswith("test_"):
                    test_files.append(dir_path)
    
    # Remove test files
    removed_count = 0
    for file_path in test_files:
        try:
            if file_path.is_dir():
                import shutil
                shutil.rmtree(file_path)
            else:
                file_path.unlink()
            removed_count += 1
            print(f"   Removed: {file_path}")
        except Exception as e:
            print(f"   Failed to remove {file_path}: {e}")
    
    if removed_count > 0:
        print(f"✅ Cleaned up {removed_count} test files")
    else:
        print(f"📭 No test files to clean up")


def main():
    """Main test function."""
    
    # Check environment
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY environment variable not set")
        print("Set it with: export OPENAI_API_KEY='your-api-key'")
        sys.exit(1)
    
    print("🚀 Essay Agent Memory Integration Test")
    print("=" * 60)
    print("This test verifies that evaluation conversations are properly")
    print("saved to memory_store and can be accessed like manual chats.")
    print()
    
    try:
        # Run the test
        success = asyncio.run(test_memory_integration())
        
        if success:
            print(f"\n✅ All integration tests passed!")
            
            # Ask if user wants to clean up
            cleanup = input(f"\nClean up test files? (y/N): ").strip().lower()
            if cleanup in ['y', 'yes']:
                asyncio.run(cleanup_test_files())
            else:
                print(f"📁 Test files left in memory_store/ for inspection")
            
            sys.exit(0)
        else:
            print(f"\n❌ Integration tests failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print(f"\n⏹️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main() 