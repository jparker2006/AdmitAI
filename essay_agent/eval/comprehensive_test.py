#!/usr/bin/env python3
"""
Comprehensive Essay Agent Evaluation Suite
Tests all 36 tools across complete user journeys to identify bugs systematically.
"""

import asyncio
import json
import logging
import time
import traceback
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import argparse

from essay_agent.cli import main as cli_main
from essay_agent.agent.core.react_agent import EssayReActAgent
from essay_agent.agent.memory.agent_memory import AgentMemory
from essay_agent.models import UserProfile
from essay_agent.tools import get_available_tools


@dataclass
class TestResult:
    """Individual test result"""
    test_id: str
    test_name: str
    category: str
    status: str  # "PASS", "FAIL", "ERROR"
    execution_time: float
    tools_used: List[str]
    error_details: Optional[str] = None
    quality_score: Optional[float] = None
    output_sample: Optional[str] = None
    bug_reports: List[Dict[str, Any]] = None

    def __post_init__(self):
        if self.bug_reports is None:
            self.bug_reports = []


@dataclass 
class EvaluationSummary:
    """Overall evaluation summary"""
    total_tests: int
    passed_tests: int
    failed_tests: int
    error_tests: int
    total_execution_time: float
    tools_coverage: Dict[str, int]  # tool_name -> times_used
    critical_bugs: List[Dict[str, Any]]
    high_bugs: List[Dict[str, Any]]
    medium_bugs: List[Dict[str, Any]]
    low_bugs: List[Dict[str, Any]]


class ComprehensiveTestRunner:
    """Runs comprehensive evaluation suite testing all tools and user journeys"""
    
    def __init__(self, output_dir: str = "eval_results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.results: List[TestResult] = []
        self.bug_counter = 0
        self.available_tools = get_available_tools()
        
        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Test data
        self.test_schools = [
            "Stanford", "Harvard", "MIT", "Yale", "Princeton", 
            "Columbia", "UPenn", "Brown", "Cornell", "Duke"
        ]
        
        self.essay_prompts = {
            "identity": "Some students have a background, identity, interest, or talent that is so meaningful they believe their application would be incomplete without it. If this sounds like you, then please share your story.",
            "challenge": "The lessons we take from obstacles we encounter can be fundamental to later success. Recount a time when you faced a challenge, setback, or failure. How did it affect you, and what did you learn from the experience?",
            "passion": "Reflect on a time when you questioned or challenged a belief or idea. What prompted your thinking? What was the outcome?",
            "achievement": "Describe a problem you've solved or a problem you'd like to solve. It can be an intellectual challenge, a research query, an ethical dilemma - anything that is of personal importance, no matter the scale.",
            "community": "Discuss an accomplishment, event, or realization that sparked a period of personal growth and a new understanding of yourself or others."
        }

    async def run_all_tests(self) -> EvaluationSummary:
        """Run all 100 comprehensive tests"""
        self.logger.info("🔬 Starting Comprehensive Essay Agent Evaluation Suite")
        start_time = time.time()
        
        # Phase 1: Tool Coverage Tests (36 tests)
        await self._run_tool_coverage_tests()
        
        # Phase 2: User Journey Tests (24 tests) 
        await self._run_user_journey_tests()
        
        # Phase 3: Edge Cases & Error Handling (20 tests)
        await self._run_edge_case_tests()
        
        # Phase 4: Advanced Integration Tests (20 tests)
        await self._run_integration_tests()
        
        total_time = time.time() - start_time
        summary = self._generate_summary(total_time)
        
        # Save results
        self._save_results(summary)
        self._print_summary(summary)
        
        return summary

    async def _run_tool_coverage_tests(self):
        """Phase 1: Test every tool at least once (36 tests)"""
        self.logger.info("📋 Phase 1: Testing all 36 tools...")
        
        tool_tests = [
            # Brainstorming Tools (6 tests)
            ("brainstorm", "brainstorm", "Help me brainstorm for Stanford identity essay"),
            ("brainstorm_specific", "brainstorm_specific", "Brainstorm ideas about my robotics club experience"),
            ("generate_story_ideas", "generate_story_ideas", "Generate story ideas for overcoming challenges"),
            ("story_development", "story_development", "Develop my story about learning to code"),
            ("story_themes", "story_themes", "What themes emerge from my volunteer work?"),
            ("story_analysis", "story_analysis", "Analyze why my debate tournament story is compelling"),
            
            # Planning Tools (4 tests)
            ("outline", "outline", "Create outline for my Harvard leadership essay"),
            ("structure_essay", "structure_essay", "Structure my essay about cultural identity"),
            ("plan_essay", "plan_essay", "Plan my essay about academic passion for computer science"),
            ("organize_content", "organize_content", "Organize my ideas about community service impact"),
            
            # Writing Tools (8 tests)
            ("write_introduction", "write_introduction", "Write compelling intro for my challenge essay"),
            ("write_body_paragraph", "write_body_paragraph", "Write body paragraph about my research experience"),
            ("write_conclusion", "write_conclusion", "Write conclusion tying together my growth themes"),
            ("draft_essay", "draft_essay", "Draft full essay about my identity as first-gen student"),
            ("rewrite_paragraph", "rewrite_paragraph", "Rewrite this paragraph to be more compelling"),
            ("improve_transitions", "improve_transitions", "Improve transitions between these paragraphs"),
            ("add_details", "add_details", "Add vivid details to my story about moving to America"),
            ("enhance_voice", "enhance_voice", "Make my voice stronger in this personal statement"),
            
            # Revision Tools (8 tests)
            ("revise_for_clarity", "revise_for_clarity", "Make this paragraph clearer and more direct"),
            ("revise_for_impact", "revise_for_impact", "Increase emotional impact of my conclusion"),
            ("strengthen_opening", "strengthen_opening", "Strengthen the opening of my diversity essay"),
            ("improve_flow", "improve_flow", "Improve flow between my intro and first body paragraph"),
            ("polish_language", "polish_language", "Polish the language in my final draft"),
            ("adjust_tone", "adjust_tone", "Adjust tone to be more reflective and mature"),
            ("refine_word_choice", "refine_word_choice", "Refine word choice to avoid repetition"),
            ("final_edit", "final_edit", "Do final edit pass on my completed essay"),
            
            # Analysis Tools (6 tests)
            ("analyze_essay", "analyze_essay", "Analyze strengths and weaknesses of my draft"),
            ("check_word_count", "check_word_count", "Check if my essay meets 650-word requirement"),
            ("evaluate_prompt_response", "evaluate_prompt_response", "Evaluate how well I addressed the prompt"),
            ("assess_narrative_structure", "assess_narrative_structure", "Assess the narrative structure of my story"),
            ("review_coherence", "review_coherence", "Review coherence and logical flow"),
            ("score_essay", "score_essay", "Score my essay using college admissions rubric"),
            
            # Specialized Tools (4 tests)
            ("clarify", "clarify", "I'm confused about how to start my essay"),
            ("provide_feedback", "provide_feedback", "Give feedback on my latest draft"),
            ("suggest_improvements", "suggest_improvements", "Suggest specific improvements for my essay"),
            ("generate_alternatives", "generate_alternatives", "Generate alternative approaches to this topic"),
        ]
        
        for test_id, tool_name, user_input in tool_tests:
            await self._run_single_tool_test(test_id, tool_name, user_input)

    async def _run_user_journey_tests(self):
        """Phase 2: Test complete user journeys (24 tests)"""
        self.logger.info("🎯 Phase 2: Testing complete user journeys...")
        
        # New User Complete Journeys (12 tests)
        new_user_journeys = [
            ("stanford_identity", "Stanford", "identity", "New user, blank slate to final draft"),
            ("harvard_challenge", "Harvard", "challenge", "New user, guided brainstorming to completion"),
            ("mit_stem_passion", "MIT", "passion", "New user, technical focus development"),
            ("yale_community", "Yale", "community", "New user, service experience development"),
            ("princeton_growth", "Princeton", "achievement", "New user, personal development narrative"),
            ("columbia_diversity", "Columbia", "identity", "New user, cultural background exploration"),
            ("upenn_intellectual", "UPenn", "passion", "New user, academic passion deep-dive"),
            ("brown_open", "Brown", "identity", "New user, interdisciplinary interests"),
            ("cornell_problem", "Cornell", "achievement", "New user, analytical approach"),
            ("duke_leadership", "Duke", "community", "New user, leadership experience crafting"),
            ("northwestern_why", "Northwestern", "identity", "New user, fit and goals alignment"),
            ("uc_personal", "UC Berkeley", "challenge", "New user, specific prompt response"),
        ]
        
        for journey_id, school, prompt_type, description in new_user_journeys:
            await self._run_user_journey_test(journey_id, school, prompt_type, description, is_new_user=True)
        
        # Existing User Journeys (12 tests)
        existing_user_journeys = [
            ("returning_similar", "Stanford", "identity", "Suggest past essay adaptation"),
            ("multi_essay_portfolio", "Harvard", "challenge", "Ensure story diversity across applications"),
            ("profile_driven_brainstorm", "MIT", "passion", "Use activities/classes for ideas"),
            ("revision_existing", "Yale", "community", "Improve previously written essay"),
            ("cross_prompt_reuse", "Princeton", "achievement", "Adapt story for different prompt type"),
            ("advanced_complex", "Columbia", "identity", "Multi-tool sophisticated workflow"),
            ("rich_profile", "UPenn", "passion", "Leverage extensive background data"),
            ("time_constrained", "Brown", "challenge", "Efficient workflow under deadline pressure"),
            ("perfectionist", "Cornell", "community", "Multiple revision cycles and refinement"),
            ("struggling_user", "Duke", "achievement", "Extensive support and guidance needed"),
            ("international_user", "Northwestern", "identity", "Cultural context and ESL considerations"),
            ("non_traditional", "UC Berkeley", "challenge", "Career change, gap year, unique background"),
        ]
        
        for journey_id, school, prompt_type, description in existing_user_journeys:
            await self._run_user_journey_test(journey_id, school, prompt_type, description, is_new_user=False)

    async def _run_edge_case_tests(self):
        """Phase 3: Test edge cases and error handling (20 tests)"""
        self.logger.info("⚠️ Phase 3: Testing edge cases and error handling...")
        
        edge_cases = [
            # Input Validation Tests (5 tests)
            ("empty_input", "Empty/minimal user input", "Help me write"),
            ("long_input", "Extremely long input", "I want to write about my life story which is very long... " * 200),
            ("nonsensical_input", "Nonsensical input", "🌟✨💫 asdf qwerty random text emoji test 123 @#$%"),
            ("inappropriate_content", "Inappropriate content", "Write about illegal activities and violence"),
            ("technical_input", "Technical input", "def fibonacci(n): return n if n <= 1 else fibonacci(n-1) + fibonacci(n-2)"),
            
            # Tool Failure Scenarios (5 tests)
            ("tool_param_mismatch", "Tool parameter mismatch", "brainstorm with wrong parameters"),
            ("missing_context", "Missing required context", "rewrite paragraph without providing text"),
            ("tool_chain_failure", "Tool chain failures", "complex workflow with intentional failures"),
            ("timeout_scenario", "Timeout scenarios", "extremely long processing request"),
            ("memory_corruption", "Memory/state corruption", "invalid conversation state"),
            
            # User Experience Edge Cases (5 tests)
            ("rapid_fire", "Rapid-fire requests", "multiple quick commands"),
            ("context_switching", "Context switching", "jump between different essays"),
            ("conversation_interrupt", "Conversation interruption", "start new topic without finishing"),
            ("help_seeking", "Help-seeking behavior", "I don't understand how this works"),
            ("frustration", "Frustration scenarios", "This is confusing and not working"),
            
            # System Boundary Tests (5 tests)
            ("non_essay_request", "Non-essay requests", "Help me with my resume"),
            ("invalid_school", "Out-of-scope schools", "University of Mars"),
            ("invalid_prompt", "Invalid essay prompts", "Write about nothing in particular"),
            ("memory_limits", "Memory limits", "extremely long conversation"),
            ("concurrent_usage", "Concurrent usage", "multiple simultaneous conversations"),
        ]
        
        for test_id, description, test_input in edge_cases:
            await self._run_edge_case_test(test_id, description, test_input)

    async def _run_integration_tests(self):
        """Phase 4: Test advanced integrations (20 tests)"""
        self.logger.info("🔧 Phase 4: Testing advanced integrations...")
        
        integration_tests = [
            # Multi-Tool Workflows (8 tests)
            ("complete_essay_workflow", "Complete essay from scratch", "Full tool chain execution"),
            ("iterative_refinement", "Iterative refinement", "Multiple revision cycles using different tools"),
            ("comparative_analysis", "Comparative analysis", "Generate multiple versions, compare quality"),
            ("complex_restructuring", "Complex restructuring", "Major essay reorganization mid-process"),
            ("style_adaptation", "Style adaptation", "Adjust essay for different school cultures"),
            ("topic_pivoting", "Topic pivoting", "Change essay focus while preserving content"),
            ("quality_improvement", "Quality improvement", "Systematic enhancement using analysis tools"),
            ("deadline_pressure", "Deadline pressure", "Efficient completion under time constraints"),
            
            # Memory & Context Tests (6 tests)
            ("long_conversation", "Long conversation persistence", "50+ turn conversations"),
            ("cross_session", "Cross-session continuity", "Resume conversations after restart"),
            ("profile_evolution", "Profile evolution", "User data updates affecting recommendations"),
            ("multi_essay_context", "Multi-essay context", "Track multiple essays simultaneously"),
            ("context_retrieval", "Context retrieval", "Access relevant past conversations"),
            ("memory_conflict", "Memory conflict resolution", "Handle contradictory user information"),
            
            # Performance & Reliability (6 tests)
            ("high_load", "High-load simulation", "Rapid successive tool calls"),
            ("error_recovery", "Error recovery", "Graceful handling of various failure modes"),
            ("quality_consistency", "Response quality consistency", "Ensure stable output quality"),
            ("latency_measurement", "Latency measurement", "Track tool execution times"),
            ("resource_usage", "Resource usage", "Monitor memory and CPU consumption"),
            ("stress_testing", "Stress testing", "Push system to operational limits"),
        ]
        
        for test_id, test_name, description in integration_tests:
            await self._run_integration_test(test_id, test_name, description)

    async def _run_single_tool_test(self, test_id: str, tool_name: str, user_input: str):
        """Run a single tool test"""
        self.logger.info(f"🔧 Testing tool: {tool_name}")
        
        start_time = time.time()
        result = TestResult(
            test_id=f"tool_{test_id}",
            test_name=f"Tool Test: {tool_name}",
            category="Tool Coverage",
            status="FAIL",
            execution_time=0.0,
            tools_used=[tool_name],
        )
        
        try:
            # Create test agent
            agent = await self._create_test_agent(f"tool_test_{test_id}")
            
            # Run conversation
            response = await agent.chat(user_input)
            
            # Check if tool was actually used
            if hasattr(agent, '_last_tool_executions'):
                tools_used = [exec.tool_name for exec in agent._last_tool_executions]
                if tool_name in tools_used:
                    result.status = "PASS"
                    result.quality_score = self._evaluate_response_quality(response)
                else:
                    result.status = "FAIL"
                    result.error_details = f"Tool {tool_name} was not executed"
            else:
                # Check response for success indicators
                if response and len(response) > 10:
                    result.status = "PASS"
                    result.quality_score = self._evaluate_response_quality(response)
                else:
                    result.status = "FAIL"
                    result.error_details = "No meaningful response generated"
            
            result.output_sample = response[:200] if response else None
            
        except Exception as e:
            result.status = "ERROR"
            result.error_details = str(e)
            self._create_bug_report(
                test_id=result.test_id,
                severity="HIGH",
                category="Tool Execution",
                description=f"Tool {tool_name} failed with exception",
                error=str(e),
                reproduction_steps=[
                    f"Call tool {tool_name}",
                    f"With input: {user_input}",
                    f"Exception: {str(e)}"
                ]
            )
            result.bug_reports.append(self._get_last_bug_report())
        
        result.execution_time = time.time() - start_time
        self.results.append(result)

    async def _run_user_journey_test(self, journey_id: str, school: str, prompt_type: str, description: str, is_new_user: bool):
        """Run a complete user journey test"""
        self.logger.info(f"🎯 Testing user journey: {journey_id}")
        
        start_time = time.time()
        result = TestResult(
            test_id=f"journey_{journey_id}",
            test_name=f"User Journey: {description}",
            category="User Journey",
            status="FAIL",
            execution_time=0.0,
            tools_used=[],
        )
        
        try:
            # Create test agent with appropriate profile
            user_id = f"journey_test_{journey_id}"
            agent = await self._create_test_agent(user_id, is_new_user=is_new_user)
            
            # Get prompt for essay type
            essay_prompt = self.essay_prompts.get(prompt_type, self.essay_prompts["identity"])
            
            # Simulate complete user journey
            responses = []
            tools_used = []
            
            # Step 1: Initial request
            initial_request = f"I need to write a {prompt_type} essay for {school}. The prompt is: {essay_prompt}"
            response = await agent.chat(initial_request)
            responses.append(response)
            
            # Step 2: Follow conversation flow
            if is_new_user:
                # New user - brainstorming phase
                brainstorm_request = "Help me brainstorm ideas for this essay"
                response = await agent.chat(brainstorm_request)
                responses.append(response)
            else:
                # Existing user - leverage profile
                profile_request = "Can you suggest ideas based on my background?"
                response = await agent.chat(profile_request)
                responses.append(response)
            
            # Step 3: Outline phase
            outline_request = "Create an outline for my essay"
            response = await agent.chat(outline_request)
            responses.append(response)
            
            # Step 4: Draft phase
            draft_request = "Write a first draft of my essay"
            response = await agent.chat(draft_request)
            responses.append(response)
            
            # Step 5: Revision phase
            revision_request = "Please review and improve my essay"
            response = await agent.chat(revision_request)
            responses.append(response)
            
            # Evaluate journey success
            if all(responses) and all(len(r) > 10 for r in responses):
                result.status = "PASS"
                result.quality_score = sum(self._evaluate_response_quality(r) for r in responses) / len(responses)
            else:
                result.status = "FAIL"
                result.error_details = "One or more conversation steps failed"
            
            result.output_sample = responses[-1][:200] if responses else None
            
        except Exception as e:
            result.status = "ERROR"
            result.error_details = str(e)
            self._create_bug_report(
                test_id=result.test_id,
                severity="HIGH",
                category="User Journey",
                description=f"User journey {journey_id} failed",
                error=str(e),
                reproduction_steps=[
                    f"Start {journey_id} user journey",
                    f"School: {school}, Type: {prompt_type}",
                    f"Exception: {str(e)}"
                ]
            )
            result.bug_reports.append(self._get_last_bug_report())
        
        result.execution_time = time.time() - start_time
        self.results.append(result)

    async def _run_edge_case_test(self, test_id: str, description: str, test_input: str):
        """Run an edge case test"""
        self.logger.info(f"⚠️ Testing edge case: {test_id}")
        
        start_time = time.time()
        result = TestResult(
            test_id=f"edge_{test_id}",
            test_name=f"Edge Case: {description}",
            category="Edge Cases",
            status="FAIL",
            execution_time=0.0,
            tools_used=[],
        )
        
        try:
            agent = await self._create_test_agent(f"edge_test_{test_id}")
            response = await agent.chat(test_input)
            
            # Edge cases should be handled gracefully
            if response and "error" not in response.lower():
                result.status = "PASS"
                result.quality_score = self._evaluate_response_quality(response)
            else:
                result.status = "FAIL"
                result.error_details = "Edge case not handled gracefully"
            
            result.output_sample = response[:200] if response else None
            
        except Exception as e:
            # Some edge cases are expected to fail, but should fail gracefully
            if "graceful" in str(e).lower():
                result.status = "PASS"
            else:
                result.status = "ERROR"
                result.error_details = str(e)
                self._create_bug_report(
                    test_id=result.test_id,
                    severity="MEDIUM",
                    category="Edge Case Handling",
                    description=f"Edge case {test_id} not handled properly",
                    error=str(e),
                    reproduction_steps=[
                        f"Send edge case input: {test_input}",
                        f"Exception: {str(e)}"
                    ]
                )
                result.bug_reports.append(self._get_last_bug_report())
        
        result.execution_time = time.time() - start_time
        self.results.append(result)

    async def _run_integration_test(self, test_id: str, test_name: str, description: str):
        """Run an integration test"""
        self.logger.info(f"🔧 Testing integration: {test_id}")
        
        start_time = time.time()
        result = TestResult(
            test_id=f"integration_{test_id}",
            test_name=f"Integration: {test_name}",
            category="Integration",
            status="FAIL",
            execution_time=0.0,
            tools_used=[],
        )
        
        try:
            agent = await self._create_test_agent(f"integration_test_{test_id}")
            
            # Run integration-specific test logic
            if "complete_essay" in test_id:
                responses = await self._test_complete_essay_workflow(agent)
            elif "memory" in test_id:
                responses = await self._test_memory_features(agent)
            elif "performance" in test_id:
                responses = await self._test_performance_features(agent)
            else:
                # Generic integration test
                response = await agent.chat(f"Test {description}")
                responses = [response]
            
            if responses and all(r for r in responses):
                result.status = "PASS"
                result.quality_score = sum(self._evaluate_response_quality(r) for r in responses) / len(responses)
            else:
                result.status = "FAIL"
                result.error_details = "Integration test failed"
            
            result.output_sample = responses[-1][:200] if responses else None
            
        except Exception as e:
            result.status = "ERROR"
            result.error_details = str(e)
            self._create_bug_report(
                test_id=result.test_id,
                severity="MEDIUM",
                category="Integration",
                description=f"Integration test {test_id} failed",
                error=str(e),
                reproduction_steps=[
                    f"Run integration test: {test_name}",
                    f"Description: {description}",
                    f"Exception: {str(e)}"
                ]
            )
            result.bug_reports.append(self._get_last_bug_report())
        
        result.execution_time = time.time() - start_time
        self.results.append(result)

    async def _create_test_agent(self, user_id: str, is_new_user: bool = True) -> EssayReActAgent:
        """Create a test agent with appropriate configuration"""
        memory = AgentMemory(user_id)
        
        if not is_new_user:
            # Create sample profile for existing user
            profile = UserProfile(
                name="Test User",
                grade="12",
                school_type="public",
                gpa=3.8,
                test_scores={"SAT": 1450},
                activities=["Robotics Club", "Volunteer Tutor", "Student Government"],
                interests=["Computer Science", "Community Service"],
                essays_written=["identity", "challenge"]
            )
            memory.store_user_profile(profile)
        
        agent = EssayReActAgent(user_id=user_id, memory=memory)
        return agent

    async def _test_complete_essay_workflow(self, agent) -> List[str]:
        """Test complete essay workflow"""
        responses = []
        
        # Brainstorm
        response = await agent.chat("Help me brainstorm for Stanford identity essay")
        responses.append(response)
        
        # Outline
        response = await agent.chat("Create an outline")
        responses.append(response)
        
        # Draft
        response = await agent.chat("Write a first draft")
        responses.append(response)
        
        # Revise
        response = await agent.chat("Revise and improve")
        responses.append(response)
        
        return responses

    async def _test_memory_features(self, agent) -> List[str]:
        """Test memory and context features"""
        responses = []
        
        # Build context
        response = await agent.chat("I'm applying to Stanford for computer science")
        responses.append(response)
        
        # Test context retention
        response = await agent.chat("What did I just tell you about my application?")
        responses.append(response)
        
        # Test profile building
        response = await agent.chat("I'm also interested in robotics and volunteer work")
        responses.append(response)
        
        return responses

    async def _test_performance_features(self, agent) -> List[str]:
        """Test performance characteristics"""
        responses = []
        
        # Test rapid requests
        start_time = time.time()
        for i in range(5):
            response = await agent.chat(f"Quick test {i}")
            responses.append(response)
        
        execution_time = time.time() - start_time
        
        # Check if performance is acceptable (< 10 seconds for 5 requests)
        if execution_time > 10:
            raise Exception(f"Performance test failed: {execution_time:.2f}s for 5 requests")
        
        return responses

    def _evaluate_response_quality(self, response: str) -> float:
        """Evaluate response quality (0.0 to 1.0)"""
        if not response:
            return 0.0
        
        quality_score = 0.0
        
        # Length check (reasonable response length)
        if 10 <= len(response) <= 2000:
            quality_score += 0.3
        
        # Content check (contains essay-related terms)
        essay_terms = ["essay", "story", "application", "college", "university", "prompt", "draft", "outline"]
        if any(term in response.lower() for term in essay_terms):
            quality_score += 0.4
        
        # Helpfulness check (contains actionable advice)
        helpful_terms = ["suggest", "recommend", "consider", "try", "help", "improve", "develop"]
        if any(term in response.lower() for term in helpful_terms):
            quality_score += 0.3
        
        return min(quality_score, 1.0)

    def _create_bug_report(self, test_id: str, severity: str, category: str, description: str, 
                          error: str, reproduction_steps: List[str]):
        """Create a structured bug report"""
        self.bug_counter += 1
        bug_id = f"BUG-EVAL-{self.bug_counter:03d}"
        
        bug_report = {
            "bug_id": bug_id,
            "test_id": test_id,
            "severity": severity,
            "category": category,
            "description": description,
            "error_details": error,
            "reproduction_steps": reproduction_steps,
            "timestamp": datetime.now().isoformat(),
            "tools_involved": [],
            "conversation_context": "",
        }
        
        # Save bug report
        bug_file = self.output_dir / f"{bug_id}.json"
        with open(bug_file, 'w') as f:
            json.dump(bug_report, f, indent=2)
        
        self.logger.warning(f"🐛 Bug report created: {bug_id}")
        return bug_report

    def _get_last_bug_report(self) -> Dict[str, Any]:
        """Get the last created bug report"""
        if self.bug_counter > 0:
            bug_id = f"BUG-EVAL-{self.bug_counter:03d}"
            bug_file = self.output_dir / f"{bug_id}.json"
            if bug_file.exists():
                with open(bug_file, 'r') as f:
                    return json.load(f)
        return {}

    def _generate_summary(self, total_time: float) -> EvaluationSummary:
        """Generate evaluation summary"""
        passed = len([r for r in self.results if r.status == "PASS"])
        failed = len([r for r in self.results if r.status == "FAIL"])
        errors = len([r for r in self.results if r.status == "ERROR"])
        
        # Count tool usage
        tools_coverage = {}
        for result in self.results:
            for tool in result.tools_used:
                tools_coverage[tool] = tools_coverage.get(tool, 0) + 1
        
        # Classify bugs by severity
        critical_bugs = []
        high_bugs = []
        medium_bugs = []
        low_bugs = []
        
        for result in self.results:
            for bug in result.bug_reports:
                if bug.get("severity") == "CRITICAL":
                    critical_bugs.append(bug)
                elif bug.get("severity") == "HIGH":
                    high_bugs.append(bug)
                elif bug.get("severity") == "MEDIUM":
                    medium_bugs.append(bug)
                else:
                    low_bugs.append(bug)
        
        return EvaluationSummary(
            total_tests=len(self.results),
            passed_tests=passed,
            failed_tests=failed,
            error_tests=errors,
            total_execution_time=total_time,
            tools_coverage=tools_coverage,
            critical_bugs=critical_bugs,
            high_bugs=high_bugs,
            medium_bugs=medium_bugs,
            low_bugs=low_bugs
        )

    def _save_results(self, summary: EvaluationSummary):
        """Save evaluation results"""
        # Save individual results
        results_file = self.output_dir / "test_results.json"
        with open(results_file, 'w') as f:
            json.dump([asdict(r) for r in self.results], f, indent=2)
        
        # Save summary
        summary_file = self.output_dir / "evaluation_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(asdict(summary), f, indent=2)
        
        # Save bug list
        bugs_file = self.output_dir / "all_bugs.json"
        all_bugs = summary.critical_bugs + summary.high_bugs + summary.medium_bugs + summary.low_bugs
        with open(bugs_file, 'w') as f:
            json.dump(all_bugs, f, indent=2)
        
        self.logger.info(f"💾 Results saved to {self.output_dir}")

    def _print_summary(self, summary: EvaluationSummary):
        """Print evaluation summary"""
        print("\n" + "="*80)
        print("🔬 COMPREHENSIVE ESSAY AGENT EVALUATION RESULTS")
        print("="*80)
        
        print(f"\n📊 TEST SUMMARY:")
        print(f"  Total Tests: {summary.total_tests}")
        print(f"  ✅ Passed: {summary.passed_tests} ({summary.passed_tests/summary.total_tests*100:.1f}%)")
        print(f"  ❌ Failed: {summary.failed_tests} ({summary.failed_tests/summary.total_tests*100:.1f}%)")
        print(f"  💥 Errors: {summary.error_tests} ({summary.error_tests/summary.total_tests*100:.1f}%)")
        print(f"  ⏱️ Total Time: {summary.total_execution_time:.2f}s")
        
        print(f"\n🔧 TOOL COVERAGE:")
        print(f"  Total Tools Available: {len(self.available_tools)}")
        print(f"  Tools Tested: {len(summary.tools_coverage)}")
        print(f"  Coverage: {len(summary.tools_coverage)/len(self.available_tools)*100:.1f}%")
        
        print(f"\n🐛 BUG SUMMARY:")
        print(f"  🔴 Critical: {len(summary.critical_bugs)}")
        print(f"  🟠 High: {len(summary.high_bugs)}")
        print(f"  🟡 Medium: {len(summary.medium_bugs)}")
        print(f"  🟢 Low: {len(summary.low_bugs)}")
        print(f"  📝 Total Bugs: {len(summary.critical_bugs + summary.high_bugs + summary.medium_bugs + summary.low_bugs)}")
        
        if summary.critical_bugs:
            print(f"\n🚨 CRITICAL BUGS REQUIRING IMMEDIATE ATTENTION:")
            for bug in summary.critical_bugs[:5]:  # Show first 5
                print(f"  • {bug.get('bug_id', 'Unknown')}: {bug.get('description', 'No description')}")
        
        print(f"\n📁 Detailed results saved to: {self.output_dir}")
        print("="*80)


async def main():
    """Main entry point for comprehensive testing"""
    parser = argparse.ArgumentParser(description="Comprehensive Essay Agent Evaluation Suite")
    parser.add_argument("--run-all", action="store_true", help="Run all 100 tests")
    parser.add_argument("--category", choices=["tools", "journeys", "edge-cases", "integration"], help="Run specific test category")
    parser.add_argument("--generate-report", action="store_true", help="Generate detailed report")
    parser.add_argument("--output-dir", default="eval_results", help="Output directory for results")
    
    args = parser.parse_args()
    
    runner = ComprehensiveTestRunner(output_dir=args.output_dir)
    
    if args.run_all:
        summary = await runner.run_all_tests()
        print(f"\n🎯 EVALUATION COMPLETE: {summary.passed_tests}/{summary.total_tests} tests passed")
        
        if summary.critical_bugs or summary.high_bugs:
            print("\n🚨 CRITICAL ISSUES FOUND - Review bug reports before proceeding")
            return 1
        else:
            print("\n✅ SYSTEM READY - No critical issues found")
            return 0
    
    elif args.category:
        if args.category == "tools":
            await runner._run_tool_coverage_tests()
        elif args.category == "journeys":
            await runner._run_user_journey_tests()
        elif args.category == "edge-cases":
            await runner._run_edge_case_tests()
        elif args.category == "integration":
            await runner._run_integration_tests()
        
        summary = runner._generate_summary(0)
        runner._save_results(summary)
        runner._print_summary(summary)
        
    else:
        parser.print_help()


if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main())) 