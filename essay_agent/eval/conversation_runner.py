"""
Conversation flow execution engine for evaluating the essay agent ReAct system.

This module executes conversational evaluation scenarios by simulating realistic
user behavior, managing conversation flow phases, and tracking comprehensive
metrics about agent performance and conversation outcomes.
"""

import asyncio
import json
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import logging

from .conversational_scenarios import ConversationScenario, ConversationPhase
from .real_profiles import UserProfile
from .college_prompts import CollegePrompt, get_prompt_by_id
from ..agent.core.react_agent import EssayReActAgent
# EvaluationMemory is defined in this file below
from ..llm_client import get_chat_llm


@dataclass
class ConversationTurn:
    """Represents a single turn in the conversation."""
    turn_number: int
    timestamp: datetime
    user_input: str
    agent_response: str
    tools_used: List[str]
    memory_accessed: List[str]
    phase_name: str
    success_indicators_met: List[str]
    expected_behavior_match: float  # 0.0 to 1.0
    response_time_seconds: float
    word_count: int


@dataclass
class PhaseResult:
    """Results from executing a conversation phase."""
    phase_name: str
    completed: bool
    success_score: float  # 0.0 to 1.0
    turns_taken: int
    tools_used: List[str]
    memory_utilized: List[str]
    expected_behavior_match: float
    user_satisfaction: float
    issues_encountered: List[str]
    duration_seconds: float


@dataclass
class ConversationResult:
    """Complete results from a conversation evaluation."""
    scenario_id: str
    user_profile_id: str
    execution_timestamp: datetime
    
    # Overall metrics
    total_turns: int
    total_duration_seconds: float
    completion_status: str  # "completed", "partial", "failed"
    overall_success_score: float  # 0.0 to 1.0
    
    # Phase-by-phase results
    phase_results: List[PhaseResult]
    conversation_turns: List[ConversationTurn]
    
    # Tool and memory usage
    tools_used_summary: Dict[str, int]
    memory_utilization_score: float
    unique_tools_used: int
    
    # Quality metrics
    conversation_naturalness: float
    goal_achievement: float
    prompt_response_quality: float
    
    # Final essay assessment (if applicable)
    final_essay_word_count: Optional[int]
    final_essay_quality_score: Optional[float]
    prompt_relevance_score: Optional[float]
    
    # Issues and insights
    issues_encountered: List[str]
    improvement_suggestions: List[str]
    notable_successes: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


class ConversationRunner:
    """Executes conversational evaluation scenarios with realistic user simulation."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.logger = logging.getLogger(__name__)
        
        # Initialize core components
        self.llm_client = get_chat_llm()
        self.agent = None  # Will be initialized with user profile
        self.user_memory = None
        
        # Conversation state
        self.current_scenario = None
        self.current_profile = None
        self.conversation_history = []
        self.phase_results = []
        
        # Metrics tracking
        self.start_time = None
        self.turn_count = 0
        
    async def execute_evaluation(
        self, 
        scenario: ConversationScenario,
        profile: Optional[UserProfile] = None
    ) -> ConversationResult:
        """Execute a complete conversational evaluation scenario."""
        
        self.logger.info(f"Starting evaluation: {scenario.eval_id}")
        
        # Initialize evaluation
        self.current_scenario = scenario
        self.current_profile = profile or self._get_profile_for_scenario(scenario)
        self.start_time = datetime.now()
        self.turn_count = 0
        self.conversation_history = []
        self.phase_results = []
        
        # Set up agent with user profile
        await self._initialize_agent_with_profile()
        
        try:
            # Execute conversation phases
            for phase in scenario.conversation_flow:
                phase_result = await self._execute_phase(phase)
                self.phase_results.append(phase_result)
                
                # Check if phase failed critically
                if not phase_result.completed and phase_result.success_score < 0.3:
                    self.logger.warning(f"Phase {phase.phase_name} failed critically")
                    break
                    
                # Brief pause between phases for realism
                await asyncio.sleep(0.5)
                
            # Generate final results
            result = await self._generate_conversation_result()
            
            if self.verbose:
                self._print_evaluation_summary(result)
                
            return result
            
        except Exception as e:
            self.logger.error(f"Evaluation failed: {str(e)}")
            return self._create_failed_result(str(e))
    
    async def _initialize_agent_with_profile(self):
        """Initialize ReAct agent with user profile and memory."""
        
        # Set up user memory with profile data
        self.user_memory = EvaluationMemory(user_id=self.current_profile.profile_id)
        
        # Load profile data into memory
        await self._load_profile_into_memory()
        
        # Initialize ReAct agent (manages its own memory internally)
        self.agent = EssayReActAgent(
            user_id=self.current_profile.profile_id
        )
        
        self.logger.info(f"Initialized agent for user: {self.current_profile.name}")
    
    async def _load_profile_into_memory(self):
        """Load user profile data into memory system."""
        
        profile = self.current_profile
        
        # Store basic profile information
        await self.user_memory.store_user_profile({
            "name": profile.name,
            "age": profile.age,
            "location": profile.location,
            "school_type": profile.school_type,
            "intended_major": profile.intended_major,
            "core_values": profile.core_values,
            "academic_interests": profile.academic_interests
        })
        
        # Store activities and experiences
        for activity in profile.activities:
            await self.user_memory.store_activity({
                "name": activity.name,
                "role": activity.role,
                "description": activity.description,
                "impact": activity.impact,
                "values_demonstrated": activity.values_demonstrated
            })
        
        # Store defining moments
        for moment in profile.defining_moments:
            await self.user_memory.store_defining_moment({
                "event": moment.event,
                "impact": moment.impact,
                "lessons_learned": moment.lessons_learned,
                "emotional_weight": moment.emotional_weight
            })
        
        # Store essay history for returning users
        for essay in profile.essay_history:
            await self.user_memory.store_essay_history({
                "topic": essay.topic,
                "theme": essay.theme,
                "word_count": essay.word_count,
                "school_type": essay.school_type,
                "strengths": essay.strengths,
                "reusability": essay.reusability
            })
        
        self.logger.info(f"Loaded profile data into memory: {len(profile.activities)} activities, {len(profile.defining_moments)} moments")
    
    async def _execute_phase(self, phase: ConversationPhase) -> PhaseResult:
        """Execute a single conversation phase."""
        
        phase_start_time = time.time()
        tools_used = []
        memory_accessed = []
        issues = []
        
        self.logger.info(f"Executing phase: {phase.phase_name}")
        
        try:
            # Simulate user input
            user_input = self._adapt_user_input_to_context(phase.user_input)
            
            # Get agent response
            response_start = time.time()
            agent_response, agent_tools, agent_memory = await self._get_agent_response(
                user_input, phase
            )
            response_time = time.time() - response_start
            
            # Track tools and memory usage
            tools_used.extend(agent_tools)
            memory_accessed.extend(agent_memory)
            
            # Evaluate response quality
            behavior_match = self._evaluate_expected_behavior_match(
                agent_response, phase, agent_tools
            )
            
            success_indicators_met = self._check_success_indicators(
                phase, agent_response, agent_tools
            )
            
            # Record conversation turn
            turn = ConversationTurn(
                turn_number=self.turn_count + 1,
                timestamp=datetime.now(),
                user_input=user_input,
                agent_response=agent_response,
                tools_used=agent_tools,
                memory_accessed=agent_memory,
                phase_name=phase.phase_name,
                success_indicators_met=success_indicators_met,
                expected_behavior_match=behavior_match,
                response_time_seconds=response_time,
                word_count=len(agent_response.split())
            )
            
            self.conversation_history.append(turn)
            self.turn_count += 1
            
            # Autonomy level checking removed for simplified evaluation
            
            # Calculate phase success score
            success_score = self._calculate_phase_success_score(
                phase, behavior_match, success_indicators_met
            )
            
            # Simulate user satisfaction based on response quality
            user_satisfaction = self._simulate_user_satisfaction(
                agent_response, behavior_match, success_score
            )
            
            # Handle multi-turn phases if needed
            if self._phase_needs_continuation(phase, success_score):
                follow_up_result = await self._handle_phase_continuation(phase)
                success_score = max(success_score, follow_up_result.success_score)
                tools_used.extend(follow_up_result.tools_used)
                
            phase_duration = time.time() - phase_start_time
            
            return PhaseResult(
                phase_name=phase.phase_name,
                completed=success_score >= 0.5,
                success_score=success_score,
                turns_taken=1,  # Could be more for multi-turn phases
                tools_used=tools_used,
                memory_utilized=memory_accessed,
                expected_behavior_match=behavior_match,
                user_satisfaction=user_satisfaction,
                issues_encountered=issues,
                duration_seconds=phase_duration
            )
            
        except Exception as e:
            self.logger.error(f"Phase {phase.phase_name} failed: {str(e)}")
            return PhaseResult(
                phase_name=phase.phase_name,
                completed=False,
                success_score=0.0,
                turns_taken=1,
                tools_used=[],
                memory_utilized=[],
                expected_behavior_match=0.0,
                user_satisfaction=0.0,
                issues_encountered=[f"Phase execution failed: {str(e)}"],
                duration_seconds=time.time() - phase_start_time
            )
    
    def _adapt_user_input_to_context(self, base_input: str) -> str:
        """Adapt user input based on profile and conversation context."""
        
        # Add personality-appropriate modifications
        if self.current_profile.writing_style.autonomy_preference == "full_agent":
            # User wants agent to do more work
            if "help me" in base_input.lower():
                base_input = base_input.replace("help me", "can you")
        
        elif self.current_profile.writing_style.autonomy_preference == "minimal_help":
            # User wants to do more work themselves
            if "can you write" in base_input.lower():
                base_input = base_input.replace("can you write", "can you give me feedback on")
        
        # Add profile-specific context for returning users
        if self.current_profile.previous_sessions > 0:
            context_additions = [
                "As we discussed before,",
                "Building on our previous work,",
                "Since you already know my background,",
                "Like last time,"
            ]
            if any(phrase in base_input for phrase in ["I want", "I need", "Help me"]):
                import random
                base_input = f"{random.choice(context_additions)} {base_input.lower()}"
        
        return base_input
    
    async def _get_agent_response(
        self, 
        user_input: str, 
        phase: ConversationPhase
    ) -> Tuple[str, List[str], List[str]]:
        """Get agent response and track tools/memory usage."""
        
        # Add scenario context to user input
        contextual_input = f"""
        Essay Prompt: {self.current_scenario.prompt}
        School: {self.current_scenario.school}
        Word Limit: {self.current_scenario.word_limit}
        
        User Request: {user_input}
        """
        
        # Get agent response with tool tracking
        tools_used = []
        memory_accessed = []
        
        try:
            # Execute agent reasoning and action
            response = await self.agent.handle_message(contextual_input)
            
            # Extract tool usage from agent execution
            if hasattr(self.agent, 'last_execution_tools'):
                tools_used = self.agent.last_execution_tools
            
            # Extract memory access from agent execution  
            if hasattr(self.agent, 'last_memory_access'):
                memory_accessed = self.agent.last_memory_access
                
            return response, tools_used, memory_accessed
            
        except Exception as e:
            self.logger.error(f"Agent response failed: {str(e)}")
            return f"I apologize, but I encountered an error: {str(e)}", [], []
    
    def _evaluate_expected_behavior_match(
        self, 
        agent_response: str, 
        phase: ConversationPhase,
        tools_used: List[str]
    ) -> float:
        """Evaluate how well agent response matches expected behavior."""
        
        score = 0.0
        max_score = 0.0
        
        # Check if expected tools were used
        if phase.expected_tool_use:
            max_score += 0.4
            expected_tools = set(phase.expected_tool_use)
            used_tools = set(tools_used)
            tool_overlap = len(expected_tools.intersection(used_tools))
            if tool_overlap > 0:
                score += 0.4 * (tool_overlap / len(expected_tools))
        
        # Check if response addresses expected behavior
        max_score += 0.6
        expected_behavior = phase.expected_agent_behavior.lower()
        response_lower = agent_response.lower()
        
        # Simple keyword matching for behavior assessment
        behavior_keywords = {
            "brainstorm": ["brainstorm", "ideas", "think about", "explore", "consider"],
            "analysis": ["analyze", "examine", "assess", "evaluate", "review"],
            "guidance": ["suggest", "recommend", "guide", "help", "advice"],
            "drafting": ["write", "draft", "create", "compose", "develop"],
            "feedback": ["feedback", "improve", "revise", "enhance", "strengthen"]
        }
        
        behavior_match_score = 0.0
        for behavior_type, keywords in behavior_keywords.items():
            if behavior_type in expected_behavior:
                keyword_matches = sum(1 for keyword in keywords if keyword in response_lower)
                if keyword_matches > 0:
                    behavior_match_score += 0.6
                    break
        
        score += behavior_match_score
        
        return score / max_score if max_score > 0 else 0.0
    
    def _check_success_indicators(
        self, 
        phase: ConversationPhase, 
        response: str, 
        tools_used: List[str]
    ) -> List[str]:
        """Check which success indicators were met."""
        
        if not phase.success_indicators:
            return []
        
        met_indicators = []
        response_lower = response.lower()
        
        for indicator in phase.success_indicators:
            indicator_lower = indicator.lower()
            
            # Simple keyword-based checking
            if any(word in response_lower for word in indicator_lower.split("_")):
                met_indicators.append(indicator)
            
            # Tool-based indicators
            if "tool" in indicator_lower and any(tool in indicator_lower for tool in tools_used):
                met_indicators.append(indicator)
        
        return met_indicators
    
    # _check_autonomy_adherence removed - autonomy system simplified out
    
    def _calculate_phase_success_score(
        self,
        phase: ConversationPhase,
        behavior_match: float,
        success_indicators_met: List[str]
    ) -> float:
        """Calculate overall success score for a phase (autonomy checking removed)."""
        
        score = 0.0
        
        # Behavior match (50% - increased from 40% since autonomy removed)
        score += behavior_match * 0.5
        
        # Success indicators (50% - increased from 40% since autonomy removed)
        if phase.success_indicators:
            indicators_score = len(success_indicators_met) / len(phase.success_indicators)
            score += indicators_score * 0.5
        else:
            score += 0.5  # Full points if no specific indicators
        
        # Autonomy adherence removed - redistributed to other criteria
        
        return min(score, 1.0)
    
    def _simulate_user_satisfaction(
        self, 
        response: str, 
        behavior_match: float, 
        success_score: float
    ) -> float:
        """Simulate user satisfaction based on response quality."""
        
        # Base satisfaction from success metrics
        satisfaction = (behavior_match + success_score) / 2
        
        # Adjust based on profile sensitivity
        sensitivity = self.current_profile.writing_style.feedback_sensitivity
        if sensitivity == "high":
            # High-sensitivity users are more critical
            satisfaction *= 0.9
        elif sensitivity == "low":
            # Low-sensitivity users are more accepting
            satisfaction = min(satisfaction * 1.1, 1.0)
        
        # Adjust based on response length and helpfulness
        word_count = len(response.split())
        if word_count < 20:
            satisfaction *= 0.8  # Too brief
        elif word_count > 300:
            satisfaction *= 0.9  # Too verbose
        
        return satisfaction
    
    def _phase_needs_continuation(self, phase: ConversationPhase, success_score: float) -> bool:
        """Determine if phase needs additional turns."""
        return success_score < 0.7 and phase.phase_name in ["brainstorming", "drafting", "revision"]
    
    async def _handle_phase_continuation(self, phase: ConversationPhase) -> PhaseResult:
        """Handle multi-turn phases that need continuation."""
        
        # Simulate follow-up user input
        follow_up_inputs = {
            "brainstorming": "Can you help me explore more ideas?",
            "drafting": "This is helpful, can you help me develop this further?",
            "revision": "What else should I improve?"
        }
        
        follow_up_input = follow_up_inputs.get(phase.phase_name, "Can you help me more with this?")
        
        # Get agent response
        response, tools, memory = await self._get_agent_response(follow_up_input, phase)
        
        # Quick evaluation
        behavior_match = self._evaluate_expected_behavior_match(response, phase, tools)
        
        return PhaseResult(
            phase_name=f"{phase.phase_name}_continuation",
            completed=True,
            success_score=behavior_match,
            turns_taken=1,
            tools_used=tools,
            memory_utilized=memory,
            expected_behavior_match=behavior_match,
            user_satisfaction=0.8,  # Generally satisfied with follow-up
            issues_encountered=[],
            duration_seconds=2.0
        )
    
    async def _generate_conversation_result(self) -> ConversationResult:
        """Generate comprehensive conversation result."""
        
        total_duration = (datetime.now() - self.start_time).total_seconds()
        
        # Calculate overall metrics
        overall_success = sum(p.success_score for p in self.phase_results) / len(self.phase_results)
        completion_status = "completed" if all(p.completed for p in self.phase_results) else "partial"
        
        # Tool usage summary
        all_tools = []
        for turn in self.conversation_history:
            all_tools.extend(turn.tools_used)
        
        tools_summary = {}
        for tool in all_tools:
            tools_summary[tool] = tools_summary.get(tool, 0) + 1
        
        # Memory utilization score
        memory_accesses = []
        for turn in self.conversation_history:
            memory_accesses.extend(turn.memory_accessed)
        
        memory_score = len(set(memory_accesses)) / max(len(self.current_profile.activities), 1)
        memory_score = min(memory_score, 1.0)
        
        # Quality metrics
        avg_behavior_match = sum(t.expected_behavior_match for t in self.conversation_history) / len(self.conversation_history)
        avg_satisfaction = sum(p.user_satisfaction for p in self.phase_results) / len(self.phase_results)
        
        # Check if final essay was produced
        final_essay_info = self._extract_final_essay_info()
        
        # Identify issues and successes
        all_issues = []
        for phase in self.phase_results:
            all_issues.extend(phase.issues_encountered)
        
        successes = [
            f"Phase '{p.phase_name}' completed successfully"
            for p in self.phase_results if p.success_score >= 0.8
        ]
        
        improvements = []
        if overall_success < 0.7:
            improvements.append("Improve agent response quality and tool selection")
        if memory_score < 0.5:
            improvements.append("Better utilization of user profile and memory")
        if avg_satisfaction < 0.7:
            improvements.append("More user-centric and satisfying responses")
        
        return ConversationResult(
            scenario_id=self.current_scenario.eval_id,
            user_profile_id=self.current_profile.profile_id,
            execution_timestamp=self.start_time,
            total_turns=len(self.conversation_history),
            total_duration_seconds=total_duration,
            completion_status=completion_status,
            overall_success_score=overall_success,
            phase_results=self.phase_results,
            conversation_turns=self.conversation_history,
            tools_used_summary=tools_summary,
            memory_utilization_score=memory_score,
            unique_tools_used=len(set(all_tools)),
            conversation_naturalness=avg_behavior_match,
            goal_achievement=overall_success,
            prompt_response_quality=final_essay_info.get("prompt_relevance", 0.0),
            final_essay_word_count=final_essay_info.get("word_count"),
            final_essay_quality_score=final_essay_info.get("quality_score"),
            prompt_relevance_score=final_essay_info.get("prompt_relevance"),
            issues_encountered=all_issues,
            improvement_suggestions=improvements,
            notable_successes=successes
        )
    
    def _extract_final_essay_info(self) -> Dict[str, Any]:
        """Extract information about final essay if one was produced."""
        
        # Look for drafting phases and essay content
        essay_info = {}
        
        for turn in self.conversation_history:
            if "draft_essay" in turn.tools_used or "write" in turn.agent_response.lower():
                # Estimate essay quality based on response length and content
                word_count = len(turn.agent_response.split())
                
                # Simple quality heuristics
                quality_score = 0.7  # Base score
                if word_count >= self.current_scenario.word_limit * 0.8:
                    quality_score += 0.1
                if self.current_scenario.prompt.lower() in turn.agent_response.lower():
                    quality_score += 0.1
                
                essay_info = {
                    "word_count": word_count,
                    "quality_score": min(quality_score, 1.0),
                    "prompt_relevance": quality_score
                }
                break
        
        return essay_info
    
    def _get_profile_for_scenario(self, scenario: ConversationScenario) -> UserProfile:
        """Get appropriate user profile for scenario if none provided."""
        
        from .real_profiles import get_profile_by_id, ALL_PROFILES
        
        # Try to get specified profile
        if hasattr(scenario, 'user_profile') and scenario.user_profile:
            profile = get_profile_by_id(scenario.user_profile)
            if profile:
                return profile
        
        # Fall back to first profile of appropriate type
        for profile in ALL_PROFILES:
            if profile.category.value in scenario.eval_id:
                return profile
        
        # Ultimate fallback
        return ALL_PROFILES[0]
    
    def _create_failed_result(self, error_message: str) -> ConversationResult:
        """Create result object for failed evaluation."""
        
        return ConversationResult(
            scenario_id=self.current_scenario.eval_id if self.current_scenario else "unknown",
            user_profile_id=self.current_profile.profile_id if self.current_profile else "unknown",
            execution_timestamp=self.start_time or datetime.now(),
            total_turns=self.turn_count,
            total_duration_seconds=0.0,
            completion_status="failed",
            overall_success_score=0.0,
            phase_results=[],
            conversation_turns=self.conversation_history,
            tools_used_summary={},
            memory_utilization_score=0.0,
            unique_tools_used=0,
            conversation_naturalness=0.0,
            goal_achievement=0.0,
            prompt_response_quality=0.0,
            final_essay_word_count=None,
            final_essay_quality_score=None,
            prompt_relevance_score=None,
            issues_encountered=[f"Evaluation failed: {error_message}"],
            improvement_suggestions=["Fix critical system error before retrying"],
            notable_successes=[]
        )
    
    def _print_evaluation_summary(self, result: ConversationResult):
        """Print detailed evaluation summary for verbose mode."""
        
        print(f"\n{'='*60}")
        print(f"CONVERSATION EVALUATION SUMMARY")
        print(f"{'='*60}")
        print(f"Scenario: {result.scenario_id}")
        print(f"Profile: {result.user_profile_id}")
        print(f"Duration: {result.total_duration_seconds:.1f}s")
        print(f"Turns: {result.total_turns}")
        print(f"Status: {result.completion_status}")
        print(f"Overall Success: {result.overall_success_score:.2f}")
        
        print(f"\n📊 QUALITY METRICS:")
        print(f"  Conversation Naturalness: {result.conversation_naturalness:.2f}")
        print(f"  Goal Achievement: {result.goal_achievement:.2f}")
        # Autonomy Respect removed from metrics
        print(f"  Memory Utilization: {result.memory_utilization_score:.2f}")
        
        print(f"\n🔧 TOOL USAGE:")
        print(f"  Unique Tools Used: {result.unique_tools_used}")
        for tool, count in sorted(result.tools_used_summary.items()):
            print(f"    {tool}: {count}")
        
        if result.final_essay_word_count:
            print(f"\n📝 ESSAY OUTPUT:")
            print(f"  Word Count: {result.final_essay_word_count}")
            print(f"  Quality Score: {result.final_essay_quality_score:.2f}")
            print(f"  Prompt Relevance: {result.prompt_relevance_score:.2f}")
        
        if result.issues_encountered:
            print(f"\n⚠️  ISSUES:")
            for issue in result.issues_encountered:
                print(f"  - {issue}")
        
        if result.notable_successes:
            print(f"\n✅ SUCCESSES:")
            for success in result.notable_successes:
                print(f"  - {success}")
        
        print(f"\n{'='*60}")


# Utility functions for batch evaluation
async def run_evaluation_batch(
    scenarios: List[ConversationScenario],
    profiles: Optional[List[UserProfile]] = None,
    verbose: bool = False,
    max_concurrent: int = 3
) -> List[ConversationResult]:
    """Run multiple evaluations concurrently."""
    
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def run_single_evaluation(scenario, profile=None):
        async with semaphore:
            runner = ConversationRunner(verbose=verbose)
            return await runner.execute_evaluation(scenario, profile)
    
    # Pair scenarios with profiles if provided
    evaluation_tasks = []
    for i, scenario in enumerate(scenarios):
        profile = profiles[i] if profiles and i < len(profiles) else None
        task = run_single_evaluation(scenario, profile)
        evaluation_tasks.append(task)
    
    # Execute all evaluations
    results = await asyncio.gather(*evaluation_tasks, return_exceptions=True)
    
    # Filter out exceptions and log them
    valid_results = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logging.error(f"Evaluation {i} failed: {str(result)}")
        else:
            valid_results.append(result)
    
    return valid_results


def save_evaluation_results(
    results: List[ConversationResult], 
    output_file: str = "evaluation_results.json"
):
    """Save evaluation results to JSON file."""
    
    serializable_results = [result.to_dict() for result in results]
    
    with open(output_file, 'w') as f:
        json.dump({
            "evaluation_timestamp": datetime.now().isoformat(),
            "total_evaluations": len(results),
            "results": serializable_results
        }, f, indent=2, default=str)
    
    print(f"Saved {len(results)} evaluation results to {output_file}")


# Export key components
__all__ = [
    "ConversationRunner",
    "ConversationResult",
    "ConversationTurn",
    "PhaseResult",
    "run_evaluation_batch",
    "save_evaluation_results"
] 


class EvaluationMemory:
    """Simple memory stub for evaluation purposes."""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        
    async def store_user_profile(self, profile_data: Dict[str, Any]) -> None:
        """Store user profile data (stub for evaluation)."""
        pass
        
    async def store_activity(self, activity_data: Dict[str, Any]) -> None:
        """Store activity data (stub for evaluation)."""
        pass
        
    async def store_defining_moment(self, moment_data: Dict[str, Any]) -> None:
        """Store defining moment data (stub for evaluation)."""
        pass
        
    async def store_essay_history(self, essay_data: Dict[str, Any]) -> None:
        """Store essay history data (stub for evaluation)."""
        pass 