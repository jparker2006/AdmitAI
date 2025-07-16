"""
DEPRECATED: Autonomy testing system for evaluating agent behavior across different user involvement levels.

WARNING: This module is deprecated as of the autonomy system removal.
The autonomy level testing has been simplified out of the evaluation system.
This file is kept for compatibility but should not be used for new evaluations.

This module tests how well the essay agent respects and adapts to different
user autonomy preferences, from full agent control to minimal assistance.
The tests ensure the agent provides appropriate levels of support while
respecting user preferences for involvement in the essay writing process.
"""

import asyncio
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

from .conversational_scenarios import ConversationScenario, AutonomyLevel
from .real_profiles import UserProfile
from .conversation_runner import ConversationRunner, ConversationResult


class AutonomyBehavior(Enum):
    """Types of agent behaviors that indicate autonomy level."""
    TAKES_INITIATIVE = "takes_initiative"          # Agent proactively does work
    OFFERS_TO_DO_WORK = "offers_to_do_work"       # Agent offers to handle tasks
    ASKS_FOR_PERMISSION = "asks_for_permission"   # Agent asks before acting
    PROVIDES_GUIDANCE = "provides_guidance"       # Agent gives instructions/advice
    GIVES_FEEDBACK = "gives_feedback"             # Agent reviews user work
    SUGGESTS_IMPROVEMENTS = "suggests_improvements" # Agent recommends changes
    WAITS_FOR_DIRECTION = "waits_for_direction"   # Agent waits for user input


@dataclass
class AutonomyTestScenario:
    """Test scenario for specific autonomy level."""
    test_id: str
    autonomy_level: AutonomyLevel
    test_description: str
    user_input: str
    expected_behaviors: List[AutonomyBehavior]
    prohibited_behaviors: List[AutonomyBehavior]
    success_indicators: List[str]
    evaluation_criteria: Dict[str, float]  # weights for different aspects


@dataclass
class AutonomyTestResult:
    """Results from autonomy testing."""
    test_id: str
    autonomy_level: AutonomyLevel
    agent_response: str
    detected_behaviors: List[AutonomyBehavior]
    
    # Compliance scores
    autonomy_adherence_score: float  # 0.0 to 1.0
    user_satisfaction_score: float   # 0.0 to 1.0
    appropriateness_score: float     # 0.0 to 1.0
    
    # Behavioral analysis
    inappropriate_behaviors: List[str]
    missing_behaviors: List[str]
    autonomy_violations: List[str]
    
    # Recommendations
    improvement_suggestions: List[str]
    positive_behaviors: List[str]


class AutonomyTester:
    """Tests agent behavior across different autonomy levels."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.test_scenarios = self._create_autonomy_test_scenarios()
        self.behavior_patterns = self._define_behavior_patterns()
        
    async def test_autonomy_levels(
        self, 
        user_profile: UserProfile,
        test_all_levels: bool = True,
        specific_level: Optional[AutonomyLevel] = None
    ) -> Dict[AutonomyLevel, List[AutonomyTestResult]]:
        """Test agent behavior across all or specific autonomy levels."""
        
        results = {}
        
        levels_to_test = [specific_level] if specific_level else list(AutonomyLevel)
        if not test_all_levels and specific_level:
            levels_to_test = [specific_level]
        
        for autonomy_level in levels_to_test:
            self.logger.info(f"Testing autonomy level: {autonomy_level.value}")
            
            level_scenarios = [s for s in self.test_scenarios if s.autonomy_level == autonomy_level]
            level_results = []
            
            for scenario in level_scenarios:
                result = await self._test_single_autonomy_scenario(scenario, user_profile)
                level_results.append(result)
            
            results[autonomy_level] = level_results
        
        return results
    
    async def _test_single_autonomy_scenario(
        self,
        test_scenario: AutonomyTestScenario,
        user_profile: UserProfile
    ) -> AutonomyTestResult:
        """Test a single autonomy scenario."""
        
        # Create conversation scenario for testing
        conversation_scenario = self._create_test_conversation_scenario(test_scenario, user_profile)
        
        # Execute conversation
        runner = ConversationRunner(verbose=False)
        conversation_result = await runner.execute_evaluation(conversation_scenario, user_profile)
        
        # Analyze agent response for autonomy behaviors
        agent_response = self._extract_agent_response(conversation_result)
        detected_behaviors = self._analyze_autonomy_behaviors(agent_response, test_scenario.autonomy_level)
        
        # Evaluate autonomy compliance
        adherence_score = self._calculate_autonomy_adherence(
            detected_behaviors, test_scenario.expected_behaviors, test_scenario.prohibited_behaviors
        )
        
        satisfaction_score = self._calculate_user_satisfaction(
            agent_response, test_scenario.autonomy_level, detected_behaviors
        )
        
        appropriateness_score = self._calculate_response_appropriateness(
            agent_response, test_scenario
        )
        
        # Identify issues and improvements
        inappropriate_behaviors = self._identify_inappropriate_behaviors(
            detected_behaviors, test_scenario.prohibited_behaviors
        )
        
        missing_behaviors = self._identify_missing_behaviors(
            detected_behaviors, test_scenario.expected_behaviors
        )
        
        violations = self._identify_autonomy_violations(
            agent_response, test_scenario.autonomy_level
        )
        
        # Generate recommendations
        improvements = self._generate_improvement_suggestions(
            test_scenario, detected_behaviors, violations
        )
        
        positives = self._identify_positive_behaviors(
            detected_behaviors, test_scenario.expected_behaviors
        )
        
        return AutonomyTestResult(
            test_id=test_scenario.test_id,
            autonomy_level=test_scenario.autonomy_level,
            agent_response=agent_response,
            detected_behaviors=detected_behaviors,
            autonomy_adherence_score=adherence_score,
            user_satisfaction_score=satisfaction_score,
            appropriateness_score=appropriateness_score,
            inappropriate_behaviors=inappropriate_behaviors,
            missing_behaviors=missing_behaviors,
            autonomy_violations=violations,
            improvement_suggestions=improvements,
            positive_behaviors=positives
        )
    
    def _create_autonomy_test_scenarios(self) -> List[AutonomyTestScenario]:
        """Create comprehensive autonomy test scenarios."""
        
        scenarios = []
        
        # FULL AGENT scenarios - user wants agent to do most work
        scenarios.extend([
            AutonomyTestScenario(
                test_id="FULL-001-initial-request",
                autonomy_level=AutonomyLevel.FULL_AGENT,
                test_description="User requests help and expects agent to take initiative",
                user_input="I need help with my Stanford essay about what matters most to me. I'm really busy with other applications.",
                expected_behaviors=[
                    AutonomyBehavior.TAKES_INITIATIVE,
                    AutonomyBehavior.OFFERS_TO_DO_WORK
                ],
                prohibited_behaviors=[
                    AutonomyBehavior.WAITS_FOR_DIRECTION,
                    AutonomyBehavior.ASKS_FOR_PERMISSION
                ],
                success_indicators=[
                    "agent offers to brainstorm for user",
                    "agent proposes to write draft",
                    "agent takes proactive approach"
                ],
                evaluation_criteria={
                    "initiative_taking": 0.4,
                    "work_completion": 0.3,
                    "efficiency": 0.3
                }
            ),
            
            AutonomyTestScenario(
                test_id="FULL-002-drafting-request",
                autonomy_level=AutonomyLevel.FULL_AGENT,
                test_description="User wants agent to write essay draft",
                user_input="Can you write a draft of my essay? I trust your judgment on structure and content.",
                expected_behaviors=[
                    AutonomyBehavior.TAKES_INITIATIVE,
                    AutonomyBehavior.OFFERS_TO_DO_WORK
                ],
                prohibited_behaviors=[
                    AutonomyBehavior.WAITS_FOR_DIRECTION,
                    AutonomyBehavior.PROVIDES_GUIDANCE
                ],
                success_indicators=[
                    "agent writes complete draft",
                    "agent handles structure decisions",
                    "agent completes task independently"
                ],
                evaluation_criteria={
                    "completeness": 0.5,
                    "autonomy": 0.3,
                    "quality": 0.2
                }
            ),
            
            AutonomyTestScenario(
                test_id="FULL-003-revision-request",
                autonomy_level=AutonomyLevel.FULL_AGENT,
                test_description="User wants agent to revise essay independently",
                user_input="This essay needs improvement but I don't have time to work on it. Can you fix it?",
                expected_behaviors=[
                    AutonomyBehavior.TAKES_INITIATIVE,
                    AutonomyBehavior.OFFERS_TO_DO_WORK
                ],
                prohibited_behaviors=[
                    AutonomyBehavior.ASKS_FOR_PERMISSION,
                    AutonomyBehavior.WAITS_FOR_DIRECTION
                ],
                success_indicators=[
                    "agent revises independently",
                    "agent makes decisions without asking",
                    "agent provides completed revision"
                ],
                evaluation_criteria={
                    "independence": 0.4,
                    "decision_making": 0.3,
                    "completion": 0.3
                }
            )
        ])
        
        # COLLABORATIVE scenarios - user wants to work together
        scenarios.extend([
            AutonomyTestScenario(
                test_id="COLLAB-001-brainstorming",
                autonomy_level=AutonomyLevel.COLLABORATIVE,
                test_description="User wants to brainstorm together with agent",
                user_input="Let's work together to brainstorm ideas for my diversity essay. I want to be involved in the process.",
                expected_behaviors=[
                    AutonomyBehavior.PROVIDES_GUIDANCE,
                    AutonomyBehavior.ASKS_FOR_PERMISSION
                ],
                prohibited_behaviors=[
                    AutonomyBehavior.TAKES_INITIATIVE,
                    AutonomyBehavior.WAITS_FOR_DIRECTION
                ],
                success_indicators=[
                    "agent involves user in brainstorming",
                    "agent asks for user input",
                    "agent builds on user ideas"
                ],
                evaluation_criteria={
                    "collaboration": 0.4,
                    "user_involvement": 0.3,
                    "partnership": 0.3
                }
            ),
            
            AutonomyTestScenario(
                test_id="COLLAB-002-drafting",
                autonomy_level=AutonomyLevel.COLLABORATIVE,
                test_description="User wants to work together on draft",
                user_input="I'd like us to write this essay together. I have some ideas but want your help developing them.",
                expected_behaviors=[
                    AutonomyBehavior.PROVIDES_GUIDANCE,
                    AutonomyBehavior.ASKS_FOR_PERMISSION
                ],
                prohibited_behaviors=[
                    AutonomyBehavior.TAKES_INITIATIVE,
                    AutonomyBehavior.OFFERS_TO_DO_WORK
                ],
                success_indicators=[
                    "agent works with user step by step",
                    "agent asks for user preferences",
                    "agent builds on user input"
                ],
                evaluation_criteria={
                    "co_creation": 0.4,
                    "responsiveness": 0.3,
                    "balance": 0.3
                }
            ),
            
            AutonomyTestScenario(
                test_id="COLLAB-003-revision",
                autonomy_level=AutonomyLevel.COLLABORATIVE,
                test_description="User wants collaborative revision process",
                user_input="Can we review this essay together and improve it? I want to be part of the revision process.",
                expected_behaviors=[
                    AutonomyBehavior.PROVIDES_GUIDANCE,
                    AutonomyBehavior.GIVES_FEEDBACK,
                    AutonomyBehavior.SUGGESTS_IMPROVEMENTS
                ],
                prohibited_behaviors=[
                    AutonomyBehavior.TAKES_INITIATIVE,
                    AutonomyBehavior.OFFERS_TO_DO_WORK
                ],
                success_indicators=[
                    "agent reviews together with user",
                    "agent explains suggestions",
                    "agent seeks user agreement"
                ],
                evaluation_criteria={
                    "joint_review": 0.4,
                    "explanation": 0.3,
                    "consensus_building": 0.3
                }
            )
        ])
        
        # GUIDED SELF-WRITE scenarios - user wants guidance but to do writing
        scenarios.extend([
            AutonomyTestScenario(
                test_id="GUIDED-001-structure-help",
                autonomy_level=AutonomyLevel.GUIDED_SELF_WRITE,
                test_description="User wants structural guidance to write themselves",
                user_input="I want to write this essay myself but need help with organization and structure.",
                expected_behaviors=[
                    AutonomyBehavior.PROVIDES_GUIDANCE,
                    AutonomyBehavior.SUGGESTS_IMPROVEMENTS
                ],
                prohibited_behaviors=[
                    AutonomyBehavior.TAKES_INITIATIVE,
                    AutonomyBehavior.OFFERS_TO_DO_WORK
                ],
                success_indicators=[
                    "agent provides outline or structure",
                    "agent gives writing guidance",
                    "agent encourages user to write"
                ],
                evaluation_criteria={
                    "guidance_quality": 0.4,
                    "user_empowerment": 0.3,
                    "structural_help": 0.3
                }
            ),
            
            AutonomyTestScenario(
                test_id="GUIDED-002-feedback-request",
                autonomy_level=AutonomyLevel.GUIDED_SELF_WRITE,
                test_description="User wrote draft and wants feedback for self-revision",
                user_input="I wrote a draft of my essay. Can you give me feedback so I can improve it myself?",
                expected_behaviors=[
                    AutonomyBehavior.GIVES_FEEDBACK,
                    AutonomyBehavior.SUGGESTS_IMPROVEMENTS,
                    AutonomyBehavior.PROVIDES_GUIDANCE
                ],
                prohibited_behaviors=[
                    AutonomyBehavior.TAKES_INITIATIVE,
                    AutonomyBehavior.OFFERS_TO_DO_WORK
                ],
                success_indicators=[
                    "agent provides constructive feedback",
                    "agent gives specific suggestions",
                    "agent encourages user revision"
                ],
                evaluation_criteria={
                    "feedback_quality": 0.4,
                    "actionable_advice": 0.3,
                    "user_empowerment": 0.3
                }
            ),
            
            AutonomyTestScenario(
                test_id="GUIDED-003-writing-process",
                autonomy_level=AutonomyLevel.GUIDED_SELF_WRITE,
                test_description="User wants process guidance for essay writing",
                user_input="I've never written a college essay before. Can you teach me the process so I can write it myself?",
                expected_behaviors=[
                    AutonomyBehavior.PROVIDES_GUIDANCE,
                    AutonomyBehavior.SUGGESTS_IMPROVEMENTS
                ],
                prohibited_behaviors=[
                    AutonomyBehavior.TAKES_INITIATIVE,
                    AutonomyBehavior.OFFERS_TO_DO_WORK
                ],
                success_indicators=[
                    "agent explains essay writing process",
                    "agent provides step-by-step guidance",
                    "agent teaches writing skills"
                ],
                evaluation_criteria={
                    "educational_value": 0.4,
                    "process_clarity": 0.3,
                    "skill_building": 0.3
                }
            )
        ])
        
        # MINIMAL HELP scenarios - user wants to write independently
        scenarios.extend([
            AutonomyTestScenario(
                test_id="MINIMAL-001-specific-question",
                autonomy_level=AutonomyLevel.MINIMAL_HELP,
                test_description="User has specific question while writing independently",
                user_input="I'm writing my essay but stuck on how to transition between paragraphs. Any quick tips?",
                expected_behaviors=[
                    AutonomyBehavior.PROVIDES_GUIDANCE,
                    AutonomyBehavior.WAITS_FOR_DIRECTION
                ],
                prohibited_behaviors=[
                    AutonomyBehavior.TAKES_INITIATIVE,
                    AutonomyBehavior.OFFERS_TO_DO_WORK,
                    AutonomyBehavior.ASKS_FOR_PERMISSION
                ],
                success_indicators=[
                    "agent answers specific question",
                    "agent provides targeted advice",
                    "agent doesn't overhelp"
                ],
                evaluation_criteria={
                    "targeted_assistance": 0.4,
                    "restraint": 0.3,
                    "usefulness": 0.3
                }
            ),
            
            AutonomyTestScenario(
                test_id="MINIMAL-002-final-polish",
                autonomy_level=AutonomyLevel.MINIMAL_HELP,
                test_description="User wants minimal help polishing finished essay",
                user_input="I finished my essay and just want someone to check for any obvious errors or improvements.",
                expected_behaviors=[
                    AutonomyBehavior.GIVES_FEEDBACK,
                    AutonomyBehavior.SUGGESTS_IMPROVEMENTS
                ],
                prohibited_behaviors=[
                    AutonomyBehavior.TAKES_INITIATIVE,
                    AutonomyBehavior.OFFERS_TO_DO_WORK
                ],
                success_indicators=[
                    "agent provides light feedback",
                    "agent suggests minor improvements",
                    "agent respects user independence"
                ],
                evaluation_criteria={
                    "light_touch": 0.4,
                    "respect_for_work": 0.3,
                    "targeted_feedback": 0.3
                }
            ),
            
            AutonomyTestScenario(
                test_id="MINIMAL-003-validation",
                autonomy_level=AutonomyLevel.MINIMAL_HELP,
                test_description="User wants validation of their independent work",
                user_input="I wrote this essay myself and think it's good. Can you just confirm it meets the requirements?",
                expected_behaviors=[
                    AutonomyBehavior.GIVES_FEEDBACK,
                    AutonomyBehavior.WAITS_FOR_DIRECTION
                ],
                prohibited_behaviors=[
                    AutonomyBehavior.TAKES_INITIATIVE,
                    AutonomyBehavior.OFFERS_TO_DO_WORK,
                    AutonomyBehavior.PROVIDES_GUIDANCE
                ],
                success_indicators=[
                    "agent validates user work",
                    "agent checks requirements",
                    "agent respects user confidence"
                ],
                evaluation_criteria={
                    "validation": 0.4,
                    "requirements_check": 0.3,
                    "confidence_respect": 0.3
                }
            )
        ])
        
        return scenarios
    
    def _define_behavior_patterns(self) -> Dict[AutonomyBehavior, List[str]]:
        """Define language patterns that indicate specific autonomy behaviors."""
        
        return {
            AutonomyBehavior.TAKES_INITIATIVE: [
                "i'll", "let me", "i can", "i will", "i'm going to",
                "here's what i'll do", "i'll start by", "let me write"
            ],
            
            AutonomyBehavior.OFFERS_TO_DO_WORK: [
                "i can write", "i'll draft", "i can create", "i'll handle",
                "would you like me to", "i can take care of", "i'll complete"
            ],
            
            AutonomyBehavior.ASKS_FOR_PERMISSION: [
                "would you like", "should i", "can i", "do you want me to",
                "would it help if", "shall we", "is it okay if"
            ],
            
            AutonomyBehavior.PROVIDES_GUIDANCE: [
                "you should", "consider", "try", "you might want to",
                "i suggest", "it would be helpful to", "think about"
            ],
            
            AutonomyBehavior.GIVES_FEEDBACK: [
                "this is good", "you could improve", "i notice",
                "strength", "weakness", "consider revising", "well done"
            ],
            
            AutonomyBehavior.SUGGESTS_IMPROVEMENTS: [
                "you could", "might be better", "consider adding",
                "perhaps", "maybe try", "another option", "alternative"
            ],
            
            AutonomyBehavior.WAITS_FOR_DIRECTION: [
                "what would you like", "how can i help", "what's your preference",
                "what should we focus on", "where would you like to start"
            ]
        }
    
    def _create_test_conversation_scenario(
        self,
        test_scenario: AutonomyTestScenario,
        user_profile: UserProfile
    ) -> ConversationScenario:
        """Create conversation scenario for autonomy testing."""
        
        from .conversational_scenarios import ConversationPhase
        
        # Create single-phase conversation for focused testing
        test_phase = ConversationPhase(
            phase_name="autonomy_test",
            user_input=test_scenario.user_input,
            expected_agent_behavior=f"autonomy_level_{test_scenario.autonomy_level.value}",
            success_indicators=test_scenario.success_indicators
        )
        
        # Mock conversation scenario
        return ConversationScenario(
            eval_id=test_scenario.test_id,
            name=f"Autonomy Test: {test_scenario.autonomy_level.value}",
            category="autonomy_test",
            description=test_scenario.test_description,
            school="Test University",
            prompt="Test prompt for autonomy evaluation",
            word_limit=500,
            user_profile=user_profile.profile_id,
            autonomy_level=test_scenario.autonomy_level,
            conversation_flow=[test_phase],
            success_criteria=None,  # We'll evaluate differently
            difficulty="medium",
            estimated_duration_minutes=3,
            tags=["autonomy_test"]
        )
    
    def _extract_agent_response(self, conversation_result: ConversationResult) -> str:
        """Extract agent response from conversation result."""
        
        if conversation_result.conversation_turns:
            return conversation_result.conversation_turns[0].agent_response
        return ""
    
    def _analyze_autonomy_behaviors(
        self,
        agent_response: str,
        autonomy_level: AutonomyLevel
    ) -> List[AutonomyBehavior]:
        """Analyze agent response to identify autonomy behaviors."""
        
        detected_behaviors = []
        response_lower = agent_response.lower()
        
        for behavior, patterns in self.behavior_patterns.items():
            for pattern in patterns:
                if pattern in response_lower:
                    detected_behaviors.append(behavior)
                    break
        
        return list(set(detected_behaviors))  # Remove duplicates
    
    def _calculate_autonomy_adherence(
        self,
        detected_behaviors: List[AutonomyBehavior],
        expected_behaviors: List[AutonomyBehavior],
        prohibited_behaviors: List[AutonomyBehavior]
    ) -> float:
        """Calculate autonomy adherence score."""
        
        score = 0.0
        total_possible = 0.0
        
        # Points for expected behaviors present
        if expected_behaviors:
            expected_present = len(set(detected_behaviors).intersection(set(expected_behaviors)))
            score += (expected_present / len(expected_behaviors)) * 0.6
            total_possible += 0.6
        
        # Points for prohibited behaviors absent
        if prohibited_behaviors:
            prohibited_present = len(set(detected_behaviors).intersection(set(prohibited_behaviors)))
            score += max(0, (len(prohibited_behaviors) - prohibited_present) / len(prohibited_behaviors)) * 0.4
            total_possible += 0.4
        
        # Default full score if no specific requirements
        if not expected_behaviors and not prohibited_behaviors:
            return 1.0
        
        return score / total_possible if total_possible > 0 else 0.0
    
    def _calculate_user_satisfaction(
        self,
        agent_response: str,
        autonomy_level: AutonomyLevel,
        detected_behaviors: List[AutonomyBehavior]
    ) -> float:
        """Calculate estimated user satisfaction based on autonomy match."""
        
        satisfaction = 0.7  # Base satisfaction
        
        # Adjust based on autonomy level expectations
        if autonomy_level == AutonomyLevel.FULL_AGENT:
            if AutonomyBehavior.TAKES_INITIATIVE in detected_behaviors:
                satisfaction += 0.2
            if AutonomyBehavior.WAITS_FOR_DIRECTION in detected_behaviors:
                satisfaction -= 0.3
        
        elif autonomy_level == AutonomyLevel.COLLABORATIVE:
            if AutonomyBehavior.ASKS_FOR_PERMISSION in detected_behaviors:
                satisfaction += 0.15
            if AutonomyBehavior.TAKES_INITIATIVE in detected_behaviors:
                satisfaction -= 0.2
        
        elif autonomy_level == AutonomyLevel.GUIDED_SELF_WRITE:
            if AutonomyBehavior.PROVIDES_GUIDANCE in detected_behaviors:
                satisfaction += 0.2
            if AutonomyBehavior.OFFERS_TO_DO_WORK in detected_behaviors:
                satisfaction -= 0.25
        
        elif autonomy_level == AutonomyLevel.MINIMAL_HELP:
            if AutonomyBehavior.WAITS_FOR_DIRECTION in detected_behaviors:
                satisfaction += 0.15
            if AutonomyBehavior.TAKES_INITIATIVE in detected_behaviors:
                satisfaction -= 0.3
        
        return max(0.0, min(1.0, satisfaction))
    
    def _calculate_response_appropriateness(
        self,
        agent_response: str,
        test_scenario: AutonomyTestScenario
    ) -> float:
        """Calculate how appropriate the response is for the scenario."""
        
        appropriateness = 0.5  # Base score
        
        # Check response length appropriateness
        word_count = len(agent_response.split())
        if test_scenario.autonomy_level == AutonomyLevel.MINIMAL_HELP:
            # Should be concise
            if word_count < 50:
                appropriateness += 0.2
            elif word_count > 150:
                appropriateness -= 0.2
        
        elif test_scenario.autonomy_level == AutonomyLevel.FULL_AGENT:
            # Can be more detailed
            if word_count > 100:
                appropriateness += 0.2
        
        # Check for success indicators
        response_lower = agent_response.lower()
        indicator_matches = sum(
            1 for indicator in test_scenario.success_indicators
            if any(word in response_lower for word in indicator.lower().split())
        )
        
        if test_scenario.success_indicators:
            appropriateness += (indicator_matches / len(test_scenario.success_indicators)) * 0.3
        
        return max(0.0, min(1.0, appropriateness))
    
    def _identify_inappropriate_behaviors(
        self,
        detected_behaviors: List[AutonomyBehavior],
        prohibited_behaviors: List[AutonomyBehavior]
    ) -> List[str]:
        """Identify inappropriate behaviors for autonomy level."""
        
        inappropriate = []
        for behavior in detected_behaviors:
            if behavior in prohibited_behaviors:
                inappropriate.append(f"Exhibited prohibited behavior: {behavior.value}")
        
        return inappropriate
    
    def _identify_missing_behaviors(
        self,
        detected_behaviors: List[AutonomyBehavior],
        expected_behaviors: List[AutonomyBehavior]
    ) -> List[str]:
        """Identify missing expected behaviors."""
        
        missing = []
        for behavior in expected_behaviors:
            if behavior not in detected_behaviors:
                missing.append(f"Missing expected behavior: {behavior.value}")
        
        return missing
    
    def _identify_autonomy_violations(
        self,
        agent_response: str,
        autonomy_level: AutonomyLevel
    ) -> List[str]:
        """Identify specific autonomy violations."""
        
        violations = []
        response_lower = agent_response.lower()
        
        # Common violation patterns
        if autonomy_level in [AutonomyLevel.GUIDED_SELF_WRITE, AutonomyLevel.MINIMAL_HELP]:
            if any(phrase in response_lower for phrase in ["i'll write", "let me write", "i'll create"]):
                violations.append("Agent offered to write when user wants to write themselves")
        
        if autonomy_level == AutonomyLevel.FULL_AGENT:
            if any(phrase in response_lower for phrase in ["you should write", "try writing", "you can write"]):
                violations.append("Agent suggested user write when they want agent to handle it")
        
        if autonomy_level == AutonomyLevel.MINIMAL_HELP:
            if any(phrase in response_lower for phrase in ["let's brainstorm", "we should", "let's work together"]):
                violations.append("Agent suggested collaboration when user wants independence")
        
        return violations
    
    def _generate_improvement_suggestions(
        self,
        test_scenario: AutonomyTestScenario,
        detected_behaviors: List[AutonomyBehavior],
        violations: List[str]
    ) -> List[str]:
        """Generate suggestions for improving autonomy adherence."""
        
        suggestions = []
        
        if violations:
            suggestions.append("Review autonomy level detection and response adaptation")
        
        missing_expected = [b for b in test_scenario.expected_behaviors if b not in detected_behaviors]
        if missing_expected:
            suggestions.append(f"Incorporate missing behaviors: {[b.value for b in missing_expected]}")
        
        inappropriate_found = [b for b in detected_behaviors if b in test_scenario.prohibited_behaviors]
        if inappropriate_found:
            suggestions.append(f"Avoid inappropriate behaviors: {[b.value for b in inappropriate_found]}")
        
        # Autonomy-specific suggestions
        if test_scenario.autonomy_level == AutonomyLevel.FULL_AGENT:
            if AutonomyBehavior.TAKES_INITIATIVE not in detected_behaviors:
                suggestions.append("Be more proactive and take initiative for full-agent users")
        
        elif test_scenario.autonomy_level == AutonomyLevel.COLLABORATIVE:
            if AutonomyBehavior.ASKS_FOR_PERMISSION not in detected_behaviors:
                suggestions.append("Ask for user input and permission more in collaborative mode")
        
        return suggestions
    
    def _identify_positive_behaviors(
        self,
        detected_behaviors: List[AutonomyBehavior],
        expected_behaviors: List[AutonomyBehavior]
    ) -> List[str]:
        """Identify positive behaviors that matched expectations."""
        
        positives = []
        for behavior in detected_behaviors:
            if behavior in expected_behaviors:
                positives.append(f"Correctly exhibited: {behavior.value}")
        
        return positives
    
    def generate_autonomy_report(
        self,
        test_results: Dict[AutonomyLevel, List[AutonomyTestResult]]
    ) -> Dict[str, Any]:
        """Generate comprehensive autonomy testing report."""
        
        report = {
            "overall_autonomy_score": 0.0,
            "level_scores": {},
            "strengths": [],
            "weaknesses": [],
            "recommendations": [],
            "detailed_results": {}
        }
        
        total_score = 0.0
        total_tests = 0
        
        for level, results in test_results.items():
            level_score = sum(r.autonomy_adherence_score for r in results) / len(results)
            report["level_scores"][level.value] = level_score
            total_score += level_score
            total_tests += 1
            
            # Collect strengths and weaknesses
            for result in results:
                report["strengths"].extend(result.positive_behaviors)
                report["weaknesses"].extend(result.inappropriate_behaviors)
                report["recommendations"].extend(result.improvement_suggestions)
        
        report["overall_autonomy_score"] = total_score / total_tests if total_tests > 0 else 0.0
        
        # Remove duplicates
        report["strengths"] = list(set(report["strengths"]))
        report["weaknesses"] = list(set(report["weaknesses"]))
        report["recommendations"] = list(set(report["recommendations"]))
        
        # Add detailed results
        for level, results in test_results.items():
            report["detailed_results"][level.value] = [
                {
                    "test_id": r.test_id,
                    "adherence_score": r.autonomy_adherence_score,
                    "satisfaction_score": r.user_satisfaction_score,
                    "violations": r.autonomy_violations,
                    "positive_behaviors": r.positive_behaviors
                }
                for r in results
            ]
        
        return report


# Utility function for running autonomy tests
async def run_comprehensive_autonomy_test(
    user_profile: UserProfile,
    output_file: Optional[str] = None
) -> Dict[str, Any]:
    """Run comprehensive autonomy testing for a user profile."""
    
    tester = AutonomyTester()
    
    # Test all autonomy levels
    results = await tester.test_autonomy_levels(user_profile, test_all_levels=True)
    
    # Generate report
    report = tester.generate_autonomy_report(results)
    
    # Save results if requested
    if output_file:
        import json
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
    
    return report


# Export key components
__all__ = [
    "AutonomyTester",
    "AutonomyTestResult",
    "AutonomyBehavior",
    "AutonomyTestScenario",
    "run_comprehensive_autonomy_test"
] 