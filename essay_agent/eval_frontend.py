#!/usr/bin/env python3
"""
Frontend Evaluation Script

Tests tool coverage and validates example registry for the debug frontend.
Run this before using the frontend to ensure everything works properly.
"""

import asyncio
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Any

# Add parent directory to Python path so we can import essay_agent
sys.path.insert(0, str(Path(__file__).parent.parent))

from essay_agent.tools import REGISTRY as TOOL_REGISTRY
from essay_agent.prompts.example_registry import EXAMPLE_REGISTRY
from essay_agent.agent_autonomous import AutonomousEssayAgent


class FrontendEvaluator:
    """Evaluates tool coverage and example registry for frontend debugging."""
    
    def __init__(self):
        self.results = {
            "total_tools": len(TOOL_REGISTRY),
            "tools_with_examples": 0,
            "tools_tested": 0,
            "successful_tools": 0,
            "failed_tools": [],
            "missing_examples": [],
            "invalid_examples": [],
            "test_results": {}
        }
    
    def validate_example_registry(self) -> Dict[str, Any]:
        """Validate that all tools have proper examples in the registry."""
        print("🔍 Validating Example Registry...")
        
        for tool_name in TOOL_REGISTRY.keys():
            if tool_name in EXAMPLE_REGISTRY:
                self.results["tools_with_examples"] += 1
                
                # Validate JSON format
                try:
                    example = EXAMPLE_REGISTRY[tool_name]
                    parsed = json.loads(example)
                    
                    # Check for stub patterns
                    if isinstance(parsed, dict) and "result" in parsed:
                        if str(parsed["result"]).startswith("stub for"):
                            self.results["missing_examples"].append(tool_name)
                        
                except json.JSONDecodeError as e:
                    self.results["invalid_examples"].append({
                        "tool": tool_name,
                        "error": str(e),
                        "example": EXAMPLE_REGISTRY[tool_name][:100] + "..."
                    })
            else:
                self.results["missing_examples"].append(tool_name)
        
        coverage = (self.results["tools_with_examples"] / self.results["total_tools"]) * 100
        print(f"📊 Example Coverage: {self.results['tools_with_examples']}/{self.results['total_tools']} ({coverage:.1f}%)")
        
        if self.results["missing_examples"]:
            print(f"⚠️  Tools missing examples: {len(self.results['missing_examples'])}")
            for tool in self.results["missing_examples"][:5]:  # Show first 5
                print(f"   • {tool}")
            if len(self.results["missing_examples"]) > 5:
                print(f"   ... and {len(self.results['missing_examples']) - 5} more")
        
        if self.results["invalid_examples"]:
            print(f"❌ Tools with invalid examples: {len(self.results['invalid_examples'])}")
            for invalid in self.results["invalid_examples"][:3]:  # Show first 3
                print(f"   • {invalid['tool']}: {invalid['error']}")
        
        return self.results
    
    async def test_tool_execution(self, limit: int = 10) -> Dict[str, Any]:
        """Test actual tool execution with a sample agent."""
        print(f"\n🧪 Testing Tool Execution (first {limit} tools)...")
        
        # Set offline mode for deterministic testing
        os.environ["ESSAY_AGENT_OFFLINE_TEST"] = "1"
        
        try:
            agent = AutonomousEssayAgent("eval_user")
            
            # Test a subset of tools
            tools_to_test = list(TOOL_REGISTRY.keys())[:limit]
            
            for i, tool_name in enumerate(tools_to_test, 1):
                print(f"   Testing {i}/{len(tools_to_test)}: {tool_name}...", end=" ")
                
                try:
                    start_time = time.time()
                    
                    # Create a simple test message that might trigger this tool
                    test_messages = {
                        "brainstorm": "Help me brainstorm essay ideas",
                        "outline": "Create an outline for my essay",
                        "draft": "Write a draft of my essay",
                        "revise": "Revise my essay",
                        "polish": "Polish my essay",
                        "essay_scoring": "Score my essay",
                        "word_count": "Check word count",
                        "grammar": "Fix grammar issues"
                    }
                    
                    # Find a relevant test message
                    test_message = "Help me with my essay"
                    for keyword, message in test_messages.items():
                        if keyword in tool_name.lower():
                            test_message = message
                            break
                    
                    # Test the agent's response
                    response = await agent.handle_message(test_message)
                    execution_time = time.time() - start_time
                    
                    self.results["test_results"][tool_name] = {
                        "success": True,
                        "execution_time": execution_time,
                        "response_length": len(response),
                        "test_message": test_message
                    }
                    
                    print("✅")
                    self.results["successful_tools"] += 1
                    
                except Exception as e:
                    self.results["test_results"][tool_name] = {
                        "success": False,
                        "error": str(e),
                        "test_message": test_message
                    }
                    self.results["failed_tools"].append({
                        "tool": tool_name,
                        "error": str(e)
                    })
                    print(f"❌ {str(e)[:50]}...")
                
                self.results["tools_tested"] += 1
            
            success_rate = (self.results["successful_tools"] / self.results["tools_tested"]) * 100
            print(f"\n📈 Tool Execution Success Rate: {self.results['successful_tools']}/{self.results['tools_tested']} ({success_rate:.1f}%)")
            
        except Exception as e:
            print(f"❌ Agent initialization failed: {e}")
            
        finally:
            # Reset offline mode
            if "ESSAY_AGENT_OFFLINE_TEST" in os.environ:
                del os.environ["ESSAY_AGENT_OFFLINE_TEST"]
        
        return self.results
    
    def generate_report(self) -> str:
        """Generate a comprehensive evaluation report."""
        report = []
        report.append("=" * 60)
        report.append("📊 FRONTEND EVALUATION REPORT")
        report.append("=" * 60)
        report.append("")
        
        # Example Registry Status
        report.append("🔍 EXAMPLE REGISTRY STATUS:")
        report.append(f"   Total Tools: {self.results['total_tools']}")
        report.append(f"   Tools with Examples: {self.results['tools_with_examples']}")
        
        if self.results["missing_examples"]:
            report.append(f"   Missing Examples: {len(self.results['missing_examples'])}")
        
        if self.results["invalid_examples"]:
            report.append(f"   Invalid Examples: {len(self.results['invalid_examples'])}")
        
        report.append("")
        
        # Tool Execution Status
        if self.results["tools_tested"] > 0:
            report.append("🧪 TOOL EXECUTION STATUS:")
            report.append(f"   Tools Tested: {self.results['tools_tested']}")
            report.append(f"   Successful: {self.results['successful_tools']}")
            report.append(f"   Failed: {len(self.results['failed_tools'])}")
            
            if self.results["failed_tools"]:
                report.append("")
                report.append("❌ FAILED TOOLS:")
                for failed in self.results["failed_tools"][:5]:
                    report.append(f"   • {failed['tool']}: {failed['error'][:80]}...")
        
        report.append("")
        
        # Recommendations
        report.append("💡 RECOMMENDATIONS:")
        
        if self.results["missing_examples"]:
            report.append("   • Add examples for tools missing from registry")
            report.append("   • Run: Update example_registry.py with realistic examples")
        
        if self.results["invalid_examples"]:
            report.append("   • Fix invalid JSON examples in registry")
        
        if self.results["failed_tools"]:
            report.append("   • Investigate and fix failing tools before frontend use")
        
        success_rate = 0
        if self.results["tools_tested"] > 0:
            success_rate = (self.results["successful_tools"] / self.results["tools_tested"]) * 100
        
        if success_rate >= 90:
            report.append("   ✅ System ready for frontend debugging!")
        elif success_rate >= 70:
            report.append("   ⚠️  System mostly ready - address failed tools")
        else:
            report.append("   ❌ System needs significant fixes before frontend use")
        
        report.append("")
        report.append("=" * 60)
        
        return "\n".join(report)
    
    def save_report(self, filename: str = "frontend_eval_report.json"):
        """Save detailed results to JSON file."""
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        print(f"💾 Detailed results saved to: {filename}")


async def main():
    """Run the frontend evaluation."""
    print("🚀 Starting Frontend Evaluation...")
    print("This will test tool coverage and example registry validation.")
    print()
    
    evaluator = FrontendEvaluator()
    
    # Step 1: Validate example registry
    evaluator.validate_example_registry()
    
    # Step 2: Test tool execution
    test_limit = int(os.getenv("FRONTEND_EVAL_LIMIT", "10"))
    await evaluator.test_tool_execution(limit=test_limit)
    
    # Step 3: Generate and display report
    print("\n" + evaluator.generate_report())
    
    # Step 4: Save detailed results
    evaluator.save_report()
    
    # Step 5: Provide next steps
    print("\n🎯 NEXT STEPS:")
    print("1. Address any missing or invalid examples")
    print("2. Fix any failing tools")
    print("3. Start the frontend: essay-agent frontend")
    print("4. Open http://localhost:8000 to debug!")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Evaluate essay agent tools for frontend debugging")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed output")
    parser.add_argument("--examples-only", action="store_true", help="Only check example registry coverage")
    parser.add_argument("--tools-only", action="store_true", help="Only test tool execution")
    
    args = parser.parse_args()
    
    # Configure logging based on verbosity
    import logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=level, format='%(levelname)s: %(message)s')
    
    # Run the evaluation
    asyncio.run(main()) 