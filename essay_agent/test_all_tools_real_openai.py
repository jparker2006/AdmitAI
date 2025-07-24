#!/usr/bin/env python3
"""
Comprehensive Tool Testing with Real OpenAI Calls
=================================================

Tests ALL 49 tools in the registry with real OpenAI API calls using exactly
the same parameters and context that the planner would use in production.
"""

import asyncio
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from essay_agent.tools import REGISTRY as TOOL_REGISTRY
from essay_agent.tools.tool_reliability import execute_tool_reliably, ReliabilityLevel
from essay_agent.memory.simple_memory import SimpleMemory
from essay_agent.intelligence.context_engine import ContextEngine

# Configure logging to see OpenAI calls
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TestResult:
    """Result of testing a single tool."""
    tool_name: str
    category: str
    success: bool
    execution_time: float
    result_preview: str
    error: Optional[str]
    openai_tokens_used: int
    personalization_detected: bool

class ComprehensiveToolTester:
    """Tests all tools with real OpenAI calls using planner-style parameters."""
    
    def __init__(self):
        self.results: List[TestResult] = []
        self.total_tokens_used = 0
        
        # Load Alex Kim's real profile for personalization testing
        self.user_context = self._load_alex_kim_context()
        
        # Realistic test data that planner would have
        self.test_data = {
            # Stanford challenge prompt (real Common App prompt)
            "essay_prompt": """Describe a topic, idea, or concept you find so engaging that it makes you lose all track of time. Why does it captivate you? What or who do you turn to when you want to learn more?""",
            
            # Alex's story based on his profile
            "test_story": """During my junior year, I founded our school's first student investment club. What started as curiosity about financial markets became an obsession that consumed my free time. I'd spend hours analyzing company fundamentals, reading SEC filings, and tracking market trends. The intersection of mathematics, psychology, and real-world impact fascinated me. When peers struggled with financial literacy, I started a tutoring service, teaching investment principles while building my own entrepreneurial skills. This experience taught me that true engagement comes when learning directly impacts others' lives.""",
            
            # Sample outline based on Alex's story
            "test_outline": {
                "hook": "The moment I discovered that Apple's quarterly earnings could predict my classmates' lunch money habits, I knew I'd found my calling.",
                "context": "As a high school student fascinated by both mathematics and human behavior, I craved understanding how financial markets reflected societal trends.",
                "challenge": "Founding the investment club seemed impossible—convincing administrators, recruiting members, and navigating complex regulations while maintaining my academic performance.",
                "action": "I spent months researching investment strategies, building financial models, and eventually launching both the club and a tutoring service to help peers understand financial literacy.",
                "growth": "Through teaching others, I discovered that my passion wasn't just about making money—it was about democratizing financial knowledge and empowering informed decision-making.",
                "reflection": "This experience showed me that the most engaging pursuits combine personal curiosity with meaningful impact on others' lives."
            },
            
            # Sample draft based on Alex's story
            "test_draft": """The moment I discovered that Apple's quarterly earnings could predict my classmates' lunch money habits, I knew I'd found my calling. As a high school student fascinated by both mathematics and human behavior, I craved understanding how financial markets reflected societal trends.

Founding the investment club seemed impossible—convincing administrators, recruiting members, and navigating complex regulations while maintaining my academic performance. The bureaucracy alone nearly defeated me. Three months of proposal revisions, liability waivers, and faculty sponsor searches tested my determination.

But I persisted because I believed financial literacy shouldn't be reserved for economics majors. I spent months researching investment strategies, building Excel models that projected portfolio performance, and eventually launching both the club and a tutoring service. Teaching my peers about compound interest and risk assessment became as thrilling as analyzing market volatility myself.

Through teaching others, I discovered that my passion wasn't just about making money—it was about democratizing financial knowledge and empowering informed decision-making. When Sarah, a sophomore, used our club's lessons to help her immigrant parents navigate their first investment account, I realized the true power of accessible education.

This experience showed me that the most engaging pursuits combine personal curiosity with meaningful impact on others' lives. At Stanford, I plan to explore how behavioral economics can inform policy, continuing this journey of turning fascination into social change.""",
            
            # College context
            "college": "Stanford",
            "word_limit": 650,
            "current_word_count": 178,
            
            # Voice profile based on Alex
            "voice_profile": {
                "tone": "analytical yet warm",
                "strengths": ["quantitative thinking", "entrepreneurship", "teaching"],
                "background": "investment club founder, tutoring business owner, Model UN leader",
                "interests": ["financial markets", "education policy", "social impact"]
            }
        }
    
    def _load_alex_kim_context(self) -> Dict[str, Any]:
        """Load Alex Kim's real profile and context."""
        try:
            # Load user profile
            profile = SimpleMemory.load("alex_kim")
            
            # Create context engine and get snapshot
            context_engine = ContextEngine("alex_kim")
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            snapshot = loop.run_until_complete(
                context_engine.snapshot("Help me with my Stanford essay")
            )
            loop.close()
            
            return {
                "user_id": "alex_kim",
                "user_profile": snapshot.user_profile,
                "college_context": snapshot.college_context,
                "conversation_history": snapshot.conversation_history
            }
            
        except Exception as e:
            logger.warning(f"Could not load Alex Kim context: {e}")
            return {
                "user_id": "alex_kim",
                "user_profile": {
                    "name": "Alex Kim",
                    "academic_interests": ["economics", "business", "finance"],
                    "extracurriculars": ["investment club founder", "tutoring business", "Model UN"],
                    "achievements": ["profitable tutoring service", "club leadership"]
                }
            }
    
    def _categorize_tool(self, tool_name: str) -> str:
        """Categorize tool by name patterns."""
        if any(x in tool_name for x in ['brainstorm', 'story', 'idea']):
            return '🧠 BRAINSTORMING'
        elif any(x in tool_name for x in ['outline', 'structure']):
            return '📋 STRUCTURE'
        elif any(x in tool_name for x in ['draft', 'write', 'expand']):
            return '✍️ WRITING'
        elif any(x in tool_name for x in ['revise', 'improve', 'rewrite']):
            return '🔄 REVISION'
        elif any(x in tool_name for x in ['polish', 'grammar', 'vocabulary']):
            return '✨ POLISH'
        elif any(x in tool_name for x in ['score', 'evaluate', 'assess']):
            return '📊 EVALUATION'
        elif any(x in tool_name for x in ['guidance', 'help', 'assist']):
            return '🎯 GUIDANCE'
        else:
            return '🔧 UTILITY'
    
    def _build_tool_context(self, tool_name: str) -> Dict[str, Any]:
        """Build realistic context for a specific tool as the planner would."""
        base_context = {
            **self.user_context,
            **self.test_data
        }
        
        # Add tool-specific context that planner would provide
        if tool_name in ['brainstorm', 'brainstorm_specific', 'suggest_stories']:
            base_context.update({
                "user_input": "Help me brainstorm essay ideas about my passion for financial markets",
                "prompt_analysis": "seeking personal engagement story with academic connection"
            })
            
        elif tool_name in ['outline', 'outline_generator', 'structure_validator']:
            base_context.update({
                "selected_story": self.test_data["test_story"],
                "user_input": "Create an outline for my investment club story"
            })
            
        elif tool_name in ['draft', 'expand_outline_section', 'rewrite_paragraph']:
            base_context.update({
                "outline": self.test_data["test_outline"],
                "user_input": "Write a draft based on my outline",
                "section_to_expand": "challenge"
            })
            
        elif tool_name in ['revise', 'improve_selection', 'rewrite_selection']:
            base_context.update({
                "essay_text": self.test_data["test_draft"],
                "user_input": "Improve the opening paragraph",
                "selected_text": "The moment I discovered that Apple's quarterly earnings could predict my classmates' lunch money habits, I knew I'd found my calling."
            })
            
        elif tool_name in ['polish', 'fix_grammar', 'enhance_vocabulary', 'final_polish']:
            base_context.update({
                "essay_text": self.test_data["test_draft"],
                "user_input": "Polish this essay for final submission"
            })
            
        elif tool_name in ['essay_scoring', 'weakness_highlight', 'alignment_check']:
            base_context.update({
                "essay_text": self.test_data["test_draft"],
                "user_input": "Evaluate this essay for Stanford admission"
            })
            
        elif tool_name == 'word_count':
            base_context.update({
                "text": self.test_data["test_draft"]
            })
            
        elif tool_name == 'clarify':
            base_context.update({
                "user_input": "I'm not sure how to start my essay about financial markets"
            })
            
        return base_context
    
    async def test_single_tool(self, tool_name: str) -> TestResult:
        """Test a single tool with real OpenAI calls."""
        category = self._categorize_tool(tool_name)
        start_time = time.time()
        
        try:
            print(f"🔧 Testing {tool_name} ({category})...")
            
            # Build realistic context as planner would
            context = self._build_tool_context(tool_name)
            
            # Execute with real OpenAI calls using reliability framework
            result = await execute_tool_reliably(
                tool_name=tool_name,
                context=context,
                user_input=context.get("user_input", ""),
                reliability_level=ReliabilityLevel.STANDARD
            )
            
            execution_time = time.time() - start_time
            
            # Extract result for analysis
            success = result.get("success", False)
            tool_result = result.get("result", {})
            error = result.get("error")
            
            # Create preview of result (first 200 chars)
            result_str = json.dumps(tool_result, default=str)
            result_preview = result_str[:200] + "..." if len(result_str) > 200 else result_str
            
            # Check for personalization (Alex Kim's background)
            personalization_detected = any(
                marker in result_str.lower() 
                for marker in ["investment", "tutoring", "business", "alex", "club", "financial"]
            )
            
            # Estimate tokens used (rough approximation)
            tokens_used = len(result_str.split()) * 1.3  # Rough token estimation
            self.total_tokens_used += tokens_used
            
            status = "✅" if success else "❌"
            personalization = "🎯" if personalization_detected else "⚪"
            
            print(f"   {status}{personalization} {execution_time:.2f}s - {result_preview[:100]}...")
            
            return TestResult(
                tool_name=tool_name,
                category=category,
                success=success,
                execution_time=execution_time,
                result_preview=result_preview,
                error=error,
                openai_tokens_used=int(tokens_used),
                personalization_detected=personalization_detected
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = str(e)
            
            print(f"   ❌💥 {execution_time:.2f}s - ERROR: {error_msg[:100]}...")
            
            return TestResult(
                tool_name=tool_name,
                category=category,
                success=False,
                execution_time=execution_time,
                result_preview="",
                error=error_msg,
                openai_tokens_used=0,
                personalization_detected=False
            )
    
    async def test_all_tools(self) -> None:
        """Test all 49 tools with real OpenAI calls."""
        print("🚀 COMPREHENSIVE TOOL TESTING WITH REAL OPENAI CALLS")
        print("=" * 70)
        print(f"Testing {len(TOOL_REGISTRY)} tools with Alex Kim's profile")
        print(f"Essay Topic: Stanford passion essay about financial markets")
        print()
        
        # Ensure OpenAI API key is available
        if not os.getenv("OPENAI_API_KEY"):
            print("❌ ERROR: OPENAI_API_KEY environment variable not set!")
            print("Please set your OpenAI API key to run real API tests.")
            return
        
        print("✅ OpenAI API key found - making real API calls")
        print()
        
        # Test tools by category
        categories = {}
        for tool_name in TOOL_REGISTRY.keys():
            category = self._categorize_tool(tool_name)
            if category not in categories:
                categories[category] = []
            categories[category].append(tool_name)
        
        # Test each category
        for category, tools in sorted(categories.items()):
            print(f"{category} ({len(tools)} tools):")
            print("-" * 50)
            
            for tool_name in sorted(tools):
                result = await self.test_single_tool(tool_name)
                self.results.append(result)
                
                # Small delay to avoid rate limiting
                await asyncio.sleep(0.5)
            
            print()
        
        # Generate comprehensive report
        await self._generate_report()
    
    async def _generate_report(self) -> None:
        """Generate comprehensive test report."""
        successful_tools = [r for r in self.results if r.success]
        failed_tools = [r for r in self.results if not r.success]
        personalized_tools = [r for r in self.results if r.personalization_detected]
        
        total_time = sum(r.execution_time for r in self.results)
        avg_time = total_time / len(self.results) if self.results else 0
        
        print("📊 COMPREHENSIVE TESTING REPORT")
        print("=" * 70)
        print(f"🎯 Overall Results:")
        print(f"   Total Tools Tested: {len(self.results)}")
        print(f"   Successful: {len(successful_tools)} ({len(successful_tools)/len(self.results)*100:.1f}%)")
        print(f"   Failed: {len(failed_tools)} ({len(failed_tools)/len(self.results)*100:.1f}%)")
        print(f"   Personalized: {len(personalized_tools)} ({len(personalized_tools)/len(self.results)*100:.1f}%)")
        print(f"   Total Execution Time: {total_time:.2f} seconds")
        print(f"   Average Time per Tool: {avg_time:.2f} seconds")
        print(f"   Estimated Tokens Used: {self.total_tokens_used:,}")
        print()
        
        # Category breakdown
        category_stats = {}
        for result in self.results:
            if result.category not in category_stats:
                category_stats[result.category] = {"total": 0, "success": 0, "personalized": 0}
            category_stats[result.category]["total"] += 1
            if result.success:
                category_stats[result.category]["success"] += 1
            if result.personalization_detected:
                category_stats[result.category]["personalized"] += 1
        
        print("📋 Category Performance:")
        for category, stats in sorted(category_stats.items()):
            success_rate = stats["success"] / stats["total"] * 100
            personalization_rate = stats["personalized"] / stats["total"] * 100
            print(f"   {category}")
            print(f"      Success Rate: {success_rate:.1f}% ({stats['success']}/{stats['total']})")
            print(f"      Personalization: {personalization_rate:.1f}% ({stats['personalized']}/{stats['total']})")
        print()
        
        # Failed tools analysis
        if failed_tools:
            print("❌ Failed Tools:")
            for result in failed_tools:
                print(f"   - {result.tool_name}: {result.error[:100]}...")
            print()
        
        # Top performing tools
        top_tools = sorted(successful_tools, key=lambda x: x.execution_time)[:10]
        print("🏆 Fastest Successful Tools:")
        for result in top_tools:
            personalization = "🎯" if result.personalization_detected else "⚪"
            print(f"   {personalization} {result.tool_name}: {result.execution_time:.2f}s")
        print()
        
        # Personalization showcase
        if personalized_tools:
            print("🎯 Personalization Examples (Alex Kim's Background Detected):")
            for result in personalized_tools[:5]:  # Show first 5
                preview = result.result_preview.replace('"', '').replace('\\n', ' ')[:150]
                print(f"   - {result.tool_name}: {preview}...")
            print()
        
        print("✅ COMPREHENSIVE TESTING COMPLETE!")
        print("All tools tested with real OpenAI API calls using planner-style parameters.")

async def main():
    """Main execution function."""
    tester = ComprehensiveToolTester()
    await tester.test_all_tools()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️ Testing interrupted by user")
    except Exception as e:
        print(f"\n💥 Testing failed: {e}")
        import traceback
        traceback.print_exc() 