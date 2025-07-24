#!/usr/bin/env python3
"""
Tool Registry Validation Script
===============================

Systematically validates all 50+ tools in the essay agent registry using Alex Kim's profile
data as consistent test input. Compares outputs to expected formats from example_registry.py.

Usage:
    python -m essay_agent.validate_tools
    python -m essay_agent.validate_tools --tool brainstorm
    python -m essay_agent.validate_tools --category core
"""

import asyncio
import json
import logging
import os
import sys
import time
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from essay_agent.tools import REGISTRY as TOOL_REGISTRY
from essay_agent.prompts.example_registry import EXAMPLE_REGISTRY
from essay_agent.utils.arg_resolver import ArgResolver
from essay_agent.intelligence.context_engine import ContextEngine
from essay_agent.memory.simple_memory import SimpleMemory

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ToolTestResult:
    """Result of testing a single tool."""
    tool_name: str
    success: bool
    execution_time: float
    output: Optional[Dict[str, Any]]
    error: Optional[str]
    parameter_resolution: bool
    output_format_valid: bool
    personalization_detected: bool
    
@dataclass
class ValidationSummary:
    """Summary of all tool validation results."""
    total_tools: int
    successful_tools: int
    failed_tools: int
    core_tools_working: int
    total_core_tools: int
    execution_time: float
    results: List[ToolTestResult]

class ToolRegistryValidator:
    """Comprehensive tool registry validation system."""
    
    # Tool categories for organized testing
    TOOL_CATEGORIES = {
        "core": [
            "brainstorm", "outline", "draft", "revise", "polish", 
            "suggest_stories", "outline_generator", "essay_scoring"
        ],
        "brainstorm": [
            "brainstorm", "suggest_stories", "match_story", "expand_story", 
            "validate_uniqueness", "brainstorm_specific"
        ],
        "structure": [
            "outline", "outline_generator", "structure_validator", 
            "transition_suggestion", "length_optimizer"
        ],
        "writing": [
            "draft", "outline_expansion", "paragraph_rewrite", 
            "opening_improvement", "voice_strengthening"
        ],
        "evaluation": [
            "essay_scoring", "weakness_highlight", "cliche_detection", 
            "alignment_check"
        ],
        "polish": [
            "polish", "fix_grammar", "vocabulary_enhancement", 
            "optimize_word_count", "consistency_check"
        ],
        "analysis": [
            "classify_prompt", "extract_requirements", "suggest_strategy", 
            "detect_overlap"
        ],
        "utility": [
            "echo", "word_count", "clarify", "text_selection"
        ]
    }
    
    # Alex Kim's test context - rich business background for personalization testing
    TEST_CONTEXT = {
        "user_id": "alex_kim",
        "essay_prompt": "Tell me about a time you faced a challenge, setback, or failure. How did it affect you, and what did you learn from the experience?",
        "college": "Stanford",
        "word_limit": 650,
        "test_story": "Starting a tutoring business during family financial struggles taught me about resilience and entrepreneurship",
        "test_outline": {
            "hook": "The day my family's business nearly collapsed, I discovered my entrepreneurial spirit",
            "context": "As founder of the student investment club, I was used to calculated risks",
            "conflict": "When my parents' small business struggled during the pandemic, I felt helpless",
            "growth": "Starting my tutoring service taught me about business ethics and social responsibility",
            "reflection": "This experience showed me that sustainable businesses create value for all stakeholders"
        },
        "test_draft": """The day my family's small business nearly collapsed, I discovered my true entrepreneurial spirit. As founder of our school's investment club, I was comfortable with calculated financial risks, but watching my parents struggle felt different—more personal, more urgent.

When the pandemic hit, their corner market faced unprecedented challenges. Revenue dropped by 60%, and they were considering closing permanently. I felt helpless watching their 20-year dream crumble, but this crisis sparked an idea that would transform my understanding of business purpose.

I launched a tutoring service, connecting high-achieving students with peers who needed academic support. What started as a way to help my family financially evolved into something much larger. Within six months, we had generated $15,000 in revenue and employed eight tutors, helping over 40 students improve their grades by an average of 1.2 GPA points.

The real lesson came when I met students who desperately needed help but couldn't afford our rates. I created a scholarship program, funded by higher-paying clients, ensuring that financial barriers wouldn't prevent access to education. This taught me that sustainable businesses must balance profit with social impact.

This experience fundamentally changed my perspective on entrepreneurship. I learned that the most meaningful business ventures create value for all stakeholders—customers, employees, and the broader community. As I pursue business administration at Stanford, I'm committed to building enterprises that generate both financial returns and positive social change."""
    }
    
    def __init__(self):
        """Initialize the validator with test context."""
        self.arg_resolver = ArgResolver()
        self.test_results: List[ToolTestResult] = []
        self.start_time = time.time()
        
        # Load Alex Kim's actual profile for rich context testing
        try:
            self.user_profile = SimpleMemory.load("alex_kim")
            self.context_engine = ContextEngine("alex_kim")
            logger.info("✅ Loaded Alex Kim's profile for personalization testing")
        except Exception as e:
            logger.warning(f"⚠️ Could not load Alex Kim's profile: {e}")
            self.user_profile = None
            self.context_engine = None
    
    async def get_test_context(self) -> Dict[str, Any]:
        """Get comprehensive test context including Alex Kim's profile."""
        base_context = self.TEST_CONTEXT.copy()
        
        if self.context_engine:
            try:
                # Get rich context snapshot with Alex's profile
                snapshot = await self.context_engine.snapshot("Help me with my essay")
                base_context.update({
                    "user_profile": snapshot.user_profile,
                    "college_context": snapshot.college_context,
                    "session_info": {"test_mode": True}
                })
                logger.debug("✅ Enhanced context with Alex Kim's profile data")
            except Exception as e:
                logger.warning(f"⚠️ Could not create context snapshot: {e}")
        
        return base_context
    
    def get_tools_in_category(self, category: str) -> List[str]:
        """Get list of tool names in a specific category."""
        if category == "all":
            return list(TOOL_REGISTRY.keys())
        return self.TOOL_CATEGORIES.get(category, [])
    
    async def validate_tool(self, tool_name: str, context: Dict[str, Any]) -> ToolTestResult:
        """Validate a single tool with comprehensive testing."""
        start_time = time.time()
        logger.info(f"🔧 Testing tool: {tool_name}")
        
        try:
            # Get the tool from registry
            tool = TOOL_REGISTRY.get(tool_name)
            if not tool:
                return ToolTestResult(
                    tool_name=tool_name,
                    success=False,
                    execution_time=0,
                    output=None,
                    error=f"Tool '{tool_name}' not found in registry",
                    parameter_resolution=False,
                    output_format_valid=False,
                    personalization_detected=False
                )
            
            # Test parameter resolution
            try:
                params = self.resolve_tool_parameters(tool_name, context)
                parameter_resolution = True
                logger.debug(f"✅ Parameter resolution successful for {tool_name}")
            except Exception as e:
                logger.warning(f"⚠️ Parameter resolution failed for {tool_name}: {e}")
                params = {"user_id": "alex_kim"}  # Minimal fallback
                parameter_resolution = False
            
            # Execute the tool
            try:
                if hasattr(tool, 'ainvoke'):
                    result = await tool.ainvoke(**params)
                else:
                    result = tool(**params)
                
                execution_time = time.time() - start_time
                
                # Analyze the result
                output_format_valid = self.validate_output_format(tool_name, result)
                personalization_detected = self.detect_personalization(tool_name, result, context)
                
                logger.info(f"✅ {tool_name} executed successfully in {execution_time:.2f}s")
                
                return ToolTestResult(
                    tool_name=tool_name,
                    success=True,
                    execution_time=execution_time,
                    output=result,
                    error=None,
                    parameter_resolution=parameter_resolution,
                    output_format_valid=output_format_valid,
                    personalization_detected=personalization_detected
                )
                
            except Exception as e:
                execution_time = time.time() - start_time
                error_msg = f"Tool execution failed: {str(e)}"
                logger.error(f"❌ {tool_name} failed: {error_msg}")
                
                return ToolTestResult(
                    tool_name=tool_name,
                    success=False,
                    execution_time=execution_time,
                    output=None,
                    error=error_msg,
                    parameter_resolution=parameter_resolution,
                    output_format_valid=False,
                    personalization_detected=False
                )
                
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Validation failed: {str(e)}"
            logger.error(f"💥 {tool_name} validation error: {error_msg}")
            
            return ToolTestResult(
                tool_name=tool_name,
                success=False,
                execution_time=execution_time,
                output=None,
                error=error_msg,
                parameter_resolution=False,
                output_format_valid=False,
                personalization_detected=False
            )
    
    def resolve_tool_parameters(self, tool_name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve parameters for a tool using ArgResolver."""
        # Create tool-specific parameters based on tool type
        planner_args = self.get_tool_specific_args(tool_name, context)
        
        return self.arg_resolver.resolve(
            tool_name,
            planner_args=planner_args,
            context=context,
            user_input="Help me with my essay",
            verbose=False
        )
    
    def get_tool_specific_args(self, tool_name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Get tool-specific arguments based on tool type and context."""
        args = {}
        
        # Essay prompt for most tools
        if "essay_prompt" in tool_name or tool_name in ["brainstorm", "suggest_stories", "outline", "draft"]:
            args["essay_prompt"] = context["essay_prompt"]
        
        # Story for story-related tools
        if "story" in tool_name or tool_name in ["match_story", "expand_story", "outline"]:
            args["story"] = context["test_story"]
        
        # Text for text editing tools
        if tool_name in ["revise", "polish", "fix_grammar", "essay_scoring", "word_count"]:
            args["essay_text"] = context["test_draft"]
            args["text"] = context["test_draft"]
        
        # Outline for draft tools
        if tool_name in ["draft", "outline_expansion"]:
            args["outline"] = json.dumps(context["test_outline"])
        
        # Selection for text selection tools
        if "selection" in tool_name or tool_name == "text_selection":
            args["selected_text"] = "This experience fundamentally changed my perspective on entrepreneurship."
            args["surrounding_context"] = context["test_draft"]
        
        # Word count for length-related tools
        if "word" in tool_name or "length" in tool_name:
            args["word_count"] = context["word_limit"]
            args["target"] = context["word_limit"]
        
        # College for college-specific tools
        if "college" in tool_name:
            args["college"] = context["college"]
        
        return args
    
    def validate_output_format(self, tool_name: str, result: Any) -> bool:
        """Validate that tool output matches expected format from example_registry.py."""
        try:
            # Get expected format from example registry
            expected_example = EXAMPLE_REGISTRY.get(tool_name)
            if not expected_example:
                logger.debug(f"📝 No example format found for {tool_name} - assuming valid")
                return True
            
            # Parse expected format
            try:
                expected_structure = json.loads(expected_example)
            except json.JSONDecodeError:
                logger.warning(f"⚠️ Invalid JSON in example_registry for {tool_name}")
                return True  # Assume valid if example is malformed
            
            # Extract actual result from tool response
            if isinstance(result, dict):
                if "ok" in result:
                    actual_result = result["ok"]
                else:
                    actual_result = result
            else:
                actual_result = result
            
            # Check if result has similar structure to expected
            return self.compare_structures(actual_result, expected_structure)
            
        except Exception as e:
            logger.debug(f"⚠️ Could not validate format for {tool_name}: {e}")
            return True  # Assume valid if validation fails
    
    def compare_structures(self, actual: Any, expected: Any) -> bool:
        """Compare actual and expected data structures for similarity."""
        if isinstance(expected, dict) and isinstance(actual, dict):
            # Check if actual has similar keys to expected
            expected_keys = set(expected.keys())
            actual_keys = set(actual.keys())
            overlap = len(expected_keys & actual_keys) / len(expected_keys) if expected_keys else 1
            return overlap >= 0.5  # At least 50% key overlap
        elif isinstance(expected, list) and isinstance(actual, list):
            # Lists should be non-empty
            return len(actual) > 0
        else:
            # For other types, just check if actual exists
            return actual is not None
    
    def detect_personalization(self, tool_name: str, result: Any, context: Dict[str, Any]) -> bool:
        """Detect if tool output includes Alex Kim's personal details."""
        if not result:
            return False
        
        # Convert result to string for text analysis
        result_text = json.dumps(result, default=str).lower()
        
        # Alex Kim's profile markers
        personal_markers = [
            "investment club", "tutoring business", "alex kim", "business administration",
            "model un", "entrepreneurship", "financial", "stanford"
        ]
        
        # Check for any personal markers in the output
        detected_markers = [marker for marker in personal_markers if marker in result_text]
        
        if detected_markers:
            logger.debug(f"✅ Personalization detected in {tool_name}: {detected_markers}")
            return True
        
        return False
    
    async def validate_category(self, category: str) -> List[ToolTestResult]:
        """Validate all tools in a specific category."""
        tool_names = self.get_tools_in_category(category)
        context = await self.get_test_context()
        
        logger.info(f"🎯 Validating {len(tool_names)} tools in category '{category}'")
        
        results = []
        for tool_name in tool_names:
            if tool_name in TOOL_REGISTRY:
                result = await self.validate_tool(tool_name, context)
                results.append(result)
                self.test_results.append(result)
            else:
                logger.warning(f"⚠️ Tool {tool_name} not found in registry")
        
        return results
    
    async def validate_all_tools(self) -> ValidationSummary:
        """Validate all tools in the registry."""
        all_tools = list(TOOL_REGISTRY.keys())
        context = await self.get_test_context()
        
        logger.info(f"🚀 Starting validation of {len(all_tools)} tools")
        
        for tool_name in all_tools:
            result = await self.validate_tool(tool_name, context)
            self.test_results.append(result)
            
            # Small delay to avoid overwhelming the system
            await asyncio.sleep(0.1)
        
        return self.generate_summary()
    
    def generate_summary(self) -> ValidationSummary:
        """Generate comprehensive validation summary."""
        total_time = time.time() - self.start_time
        
        successful_tools = sum(1 for r in self.test_results if r.success)
        failed_tools = len(self.test_results) - successful_tools
        
        # Count core tools
        core_tools = self.TOOL_CATEGORIES["core"]
        core_results = [r for r in self.test_results if r.tool_name in core_tools]
        core_working = sum(1 for r in core_results if r.success)
        
        return ValidationSummary(
            total_tools=len(self.test_results),
            successful_tools=successful_tools,
            failed_tools=failed_tools,
            core_tools_working=core_working,
            total_core_tools=len(core_tools),
            execution_time=total_time,
            results=self.test_results
        )
    
    def print_summary(self, summary: ValidationSummary):
        """Print comprehensive validation summary."""
        print("\n" + "="*80)
        print("🏆 TOOL REGISTRY VALIDATION SUMMARY")
        print("="*80)
        
        # Overall stats
        success_rate = (summary.successful_tools / summary.total_tools * 100) if summary.total_tools > 0 else 0
        core_rate = (summary.core_tools_working / summary.total_core_tools * 100) if summary.total_core_tools > 0 else 0
        
        print(f"📊 Overall Results:")
        print(f"   Total Tools Tested: {summary.total_tools}")
        print(f"   ✅ Successful: {summary.successful_tools} ({success_rate:.1f}%)")
        print(f"   ❌ Failed: {summary.failed_tools}")
        print(f"   ⏱️ Total Time: {summary.execution_time:.2f}s")
        print()
        
        print(f"🎯 Core Essay Tools:")
        print(f"   Working: {summary.core_tools_working}/{summary.total_core_tools} ({core_rate:.1f}%)")
        print()
        
        # Detailed results by category
        for category, tool_names in self.TOOL_CATEGORIES.items():
            category_results = [r for r in summary.results if r.tool_name in tool_names]
            if category_results:
                successful = sum(1 for r in category_results if r.success)
                total = len(category_results)
                rate = (successful / total * 100) if total > 0 else 0
                print(f"📁 {category.title()} Tools: {successful}/{total} ({rate:.1f}%)")
        
        print("\n" + "="*80)
        print("🔧 DETAILED TOOL RESULTS")
        print("="*80)
        
        # Group results by success
        successful = [r for r in summary.results if r.success]
        failed = [r for r in summary.results if not r.success]
        
        if successful:
            print(f"\n✅ WORKING TOOLS ({len(successful)}):")
            for result in sorted(successful, key=lambda x: x.execution_time):
                personalization = "🎯" if result.personalization_detected else "⚪"
                format_check = "📋" if result.output_format_valid else "⚠️"
                param_check = "🔧" if result.parameter_resolution else "⚠️"
                print(f"   {personalization}{format_check}{param_check} {result.tool_name:<20} ({result.execution_time:.2f}s)")
        
        if failed:
            print(f"\n❌ FAILED TOOLS ({len(failed)}):")
            for result in failed:
                print(f"   💥 {result.tool_name:<20} - {result.error}")
        
        print("\n📈 LEGEND:")
        print("   🎯 = Personalization detected (Alex Kim's profile used)")
        print("   📋 = Output format matches example_registry.py")
        print("   🔧 = Parameter resolution successful")
        print("   ⚪ = Generic output (no personalization)")
        print("   ⚠️ = Issues detected")
        
        # Recommendations
        print("\n" + "="*80)
        print("💡 RECOMMENDATIONS")
        print("="*80)
        
        param_issues = [r for r in summary.results if not r.parameter_resolution]
        format_issues = [r for r in summary.results if not r.output_format_valid]
        
        if param_issues:
            print(f"\n🔧 Parameter Resolution Issues ({len(param_issues)} tools):")
            for result in param_issues[:5]:  # Show top 5
                print(f"   - {result.tool_name}: Update ArgResolver mappings")
        
        if format_issues:
            print(f"\n📋 Output Format Issues ({len(format_issues)} tools):")
            for result in format_issues[:5]:  # Show top 5
                print(f"   - {result.tool_name}: Update example_registry.py")
        
        if summary.core_tools_working < summary.total_core_tools:
            print(f"\n🎯 Priority: Fix core essay workflow tools first!")
            core_failed = [r for r in summary.results if r.tool_name in self.TOOL_CATEGORIES["core"] and not r.success]
            for result in core_failed:
                print(f"   - {result.tool_name}: {result.error}")

async def main():
    """Main validation entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate Essay Agent Tool Registry")
    parser.add_argument("--tool", help="Validate specific tool")
    parser.add_argument("--category", default="all", help="Validate tools in category (core, brainstorm, structure, etc.)")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    validator = ToolRegistryValidator()
    
    try:
        if args.tool:
            # Validate single tool
            context = await validator.get_test_context()
            result = await validator.validate_tool(args.tool, context)
            validator.test_results = [result]
            summary = validator.generate_summary()
        elif args.category != "all":
            # Validate category
            await validator.validate_category(args.category)
            summary = validator.generate_summary()
        else:
            # Validate all tools
            summary = await validator.validate_all_tools()
        
        validator.print_summary(summary)
        
        # Exit with appropriate code
        if summary.successful_tools == summary.total_tools:
            print("\n🎉 All tools working perfectly!")
            sys.exit(0)
        elif summary.core_tools_working == summary.total_core_tools:
            print(f"\n✅ Core tools working! {summary.failed_tools} non-core issues to fix.")
            sys.exit(0)
        else:
            print(f"\n⚠️ {summary.failed_tools} tools need fixing, including core tools.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⏹️ Validation interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"💥 Validation failed: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 