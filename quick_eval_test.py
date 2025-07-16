#!/usr/bin/env python3
"""
Quick 10-test evaluation to verify system health before full comprehensive testing
"""

import asyncio
import sys
import time
from pathlib import Path

# Add essay_agent to path
sys.path.insert(0, str(Path(__file__).parent))

from essay_agent.agent.core.react_agent import EssayReActAgent
from essay_agent.agent.memory.agent_memory import AgentMemory


async def quick_health_check():
    """Run 10 quick tests to verify system health"""
    print("🏥 Quick Health Check - 10 Essential Tests")
    print("=" * 60)
    
    results = []
    
    # Test 1: Agent Initialization
    print("1️⃣ Testing agent initialization...")
    try:
        memory = AgentMemory("health_check_user")
        agent = EssayReActAgent(user_id="health_check_user", memory=memory)
        results.append(("Agent Init", "PASS", None))
        print("   ✅ Agent initialized successfully")
    except Exception as e:
        results.append(("Agent Init", "FAIL", str(e)))
        print(f"   ❌ Agent init failed: {str(e)}")
    
    # Test 2: Basic Chat
    print("2️⃣ Testing basic chat...")
    try:
        response = await agent.chat("Hello, can you help me with my essay?")
        if response and len(response) > 10:
            results.append(("Basic Chat", "PASS", None))
            print("   ✅ Basic chat working")
        else:
            results.append(("Basic Chat", "FAIL", "No meaningful response"))
            print("   ❌ Basic chat failed - no response")
    except Exception as e:
        results.append(("Basic Chat", "FAIL", str(e)))
        print(f"   ❌ Basic chat failed: {str(e)}")
    
    # Test 3: Brainstorm Tool
    print("3️⃣ Testing brainstorm tool...")
    try:
        response = await agent.chat("Help me brainstorm ideas for my identity essay")
        if response and ("story" in response.lower() or "idea" in response.lower()):
            results.append(("Brainstorm Tool", "PASS", None))
            print("   ✅ Brainstorm tool working")
        else:
            results.append(("Brainstorm Tool", "FAIL", "No brainstorm content"))
            print("   ❌ Brainstorm tool failed")
    except Exception as e:
        results.append(("Brainstorm Tool", "FAIL", str(e)))
        print(f"   ❌ Brainstorm tool failed: {str(e)}")
    
    # Test 4: Outline Tool
    print("4️⃣ Testing outline tool...")
    try:
        response = await agent.chat("Create an outline for my essay about leadership")
        if response and ("outline" in response.lower() or "structure" in response.lower()):
            results.append(("Outline Tool", "PASS", None))
            print("   ✅ Outline tool working")
        else:
            results.append(("Outline Tool", "FAIL", "No outline content"))
            print("   ❌ Outline tool failed")
    except Exception as e:
        results.append(("Outline Tool", "FAIL", str(e)))
        print(f"   ❌ Outline tool failed: {str(e)}")
    
    # Test 5: Draft Tool
    print("5️⃣ Testing draft tool...")
    try:
        response = await agent.chat("Write a short introduction paragraph for my essay")
        if response and len(response) > 50:
            results.append(("Draft Tool", "PASS", None))
            print("   ✅ Draft tool working")
        else:
            results.append(("Draft Tool", "FAIL", "No draft content"))
            print("   ❌ Draft tool failed")
    except Exception as e:
        results.append(("Draft Tool", "FAIL", str(e)))
        print(f"   ❌ Draft tool failed: {str(e)}")
    
    # Test 6: Memory Persistence
    print("6️⃣ Testing memory persistence...")
    try:
        await agent.chat("Remember that I'm applying to Stanford")
        response = await agent.chat("What school am I applying to?")
        if "stanford" in response.lower():
            results.append(("Memory", "PASS", None))
            print("   ✅ Memory working")
        else:
            results.append(("Memory", "FAIL", "Context not retained"))
            print("   ❌ Memory failed - context not retained")
    except Exception as e:
        results.append(("Memory", "FAIL", str(e)))
        print(f"   ❌ Memory failed: {str(e)}")
    
    # Test 7: Error Handling
    print("7️⃣ Testing error handling...")
    try:
        response = await agent.chat("@#$%^&*() invalid input test")
        if response:  # Any response means graceful handling
            results.append(("Error Handling", "PASS", None))
            print("   ✅ Error handling working")
        else:
            results.append(("Error Handling", "FAIL", "No response to invalid input"))
            print("   ❌ Error handling failed")
    except Exception as e:
        # Exception is acceptable for invalid input, but should be handled gracefully
        results.append(("Error Handling", "PARTIAL", str(e)))
        print(f"   ⚠️ Error handling partial: {str(e)}")
    
    # Test 8: Performance Check
    print("8️⃣ Testing performance...")
    try:
        start_time = time.time()
        response = await agent.chat("Quick test")
        execution_time = time.time() - start_time
        
        if execution_time < 5.0:  # Should respond in under 5 seconds
            results.append(("Performance", "PASS", None))
            print(f"   ✅ Performance good: {execution_time:.2f}s")
        else:
            results.append(("Performance", "FAIL", f"Too slow: {execution_time:.2f}s"))
            print(f"   ❌ Performance slow: {execution_time:.2f}s")
    except Exception as e:
        results.append(("Performance", "FAIL", str(e)))
        print(f"   ❌ Performance test failed: {str(e)}")
    
    # Test 9: Multiple Tools in Sequence
    print("9️⃣ Testing tool chaining...")
    try:
        await agent.chat("I want to write about overcoming challenges")
        await agent.chat("Help me brainstorm")
        response = await agent.chat("Now create an outline")
        
        if response and len(response) > 20:
            results.append(("Tool Chaining", "PASS", None))
            print("   ✅ Tool chaining working")
        else:
            results.append(("Tool Chaining", "FAIL", "Tool chain failed"))
            print("   ❌ Tool chaining failed")
    except Exception as e:
        results.append(("Tool Chaining", "FAIL", str(e)))
        print(f"   ❌ Tool chaining failed: {str(e)}")
    
    # Test 10: System Health Summary
    print("🔟 Testing system health summary...")
    try:
        response = await agent.chat("Summarize our conversation so far")
        if response and len(response) > 30:
            results.append(("Health Summary", "PASS", None))
            print("   ✅ Health summary working")
        else:
            results.append(("Health Summary", "FAIL", "No summary"))
            print("   ❌ Health summary failed")
    except Exception as e:
        results.append(("Health Summary", "FAIL", str(e)))
        print(f"   ❌ Health summary failed: {str(e)}")
    
    # Print Results
    print("\n" + "=" * 60)
    print("🏥 HEALTH CHECK RESULTS")
    print("=" * 60)
    
    passed = len([r for r in results if r[1] == "PASS"])
    failed = len([r for r in results if r[1] == "FAIL"])
    partial = len([r for r in results if r[1] == "PARTIAL"])
    
    print(f"✅ Passed: {passed}/10")
    print(f"❌ Failed: {failed}/10")
    print(f"⚠️ Partial: {partial}/10")
    print(f"🎯 Health Score: {(passed + partial*0.5)/10*100:.1f}%")
    
    if failed == 0:
        print("\n🎉 SYSTEM HEALTHY - Ready for comprehensive evaluation!")
        return True
    elif failed <= 2:
        print("\n⚠️ SYSTEM MOSTLY HEALTHY - Consider fixing issues before full eval")
        return True
    else:
        print("\n🚨 SYSTEM UNHEALTHY - Fix critical issues before evaluation!")
        return False


async def main():
    """Main entry point"""
    healthy = await quick_health_check()
    
    if healthy:
        print("\n" + "=" * 60)
        print("🚀 Ready to run comprehensive evaluation!")
        print("Execute: python run_comprehensive_eval.py")
        print("=" * 60)
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main())) 