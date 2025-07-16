"""
Memory utilization testing system for evaluating agent use of stored user data.

This module tests how effectively the essay agent leverages user profile data,
previous essays, activities, defining moments, and other stored information
to provide personalized, contextually-aware essay assistance.
"""

import asyncio
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum
import logging

from .conversational_scenarios import ConversationScenario
from .real_profiles import UserProfile, Activity, EssayHistory, DefiningMoment
from .conversation_runner import ConversationRunner, ConversationResult


class MemoryType(Enum):
    """Types of memory that can be utilized."""
    ACTIVITIES = "activities"
    ESSAY_HISTORY = "essay_history"
    DEFINING_MOMENTS = "defining_moments"
    CORE_VALUES = "core_values"
    ACADEMIC_INTERESTS = "academic_interests"
    FAMILY_BACKGROUND = "family_background"
    PERSONAL_CHALLENGES = "personal_challenges"
    WRITING_STYLE = "writing_style"
    LEADERSHIP_ROLES = "leadership_roles"
    VOLUNTEER_WORK = "volunteer_work"


class MemoryUtilizationPattern(Enum):
    """Patterns of memory utilization to test."""
    ACTIVITY_LEVERAGE = "activity_leverage"              # Using activities for essay content
    ESSAY_ADAPTATION = "essay_adaptation"                # Adapting previous essays
    CROSS_PROMPT_REUSE = "cross_prompt_reuse"           # Managing story diversity
    PROFILE_INTEGRATION = "profile_integration"          # Using core profile data
    THEME_CONSISTENCY = "theme_consistency"              # Consistent value themes
    STORY_DIFFERENTIATION = "story_differentiation"      # Avoiding repetition
    CONTEXTUAL_RECALL = "contextual_recall"             # Relevant memory retrieval
    PROGRESSIVE_BUILDING = "progressive_building"        # Building on previous work


@dataclass
class MemoryTestScenario:
    """Test scenario for memory utilization."""
    test_id: str
    pattern: MemoryUtilizationPattern
    test_description: str
    required_memory_types: List[MemoryType]
    user_input: str
    expected_memory_usage: List[str]  # Specific memory items expected to be used
    memory_integration_indicators: List[str]  # Signs memory was used effectively
    success_criteria: Dict[str, float]  # Evaluation weights
    difficulty_level: str  # "easy", "medium", "hard"


@dataclass
class MemoryUtilizationResult:
    """Results from memory utilization testing."""
    test_id: str
    pattern: MemoryUtilizationPattern
    agent_response: str
    
    # Memory usage analysis
    memory_types_accessed: List[MemoryType]
    specific_memories_used: List[str]
    memory_integration_score: float  # 0.0 to 1.0
    relevance_score: float           # How relevant was memory usage
    accuracy_score: float            # How accurate was memory recall
    
    # Pattern-specific scores
    pattern_adherence_score: float   # How well pattern was followed
    personalization_score: float    # How personalized the response was
    context_awareness_score: float  # Understanding of user context
    
    # Quality measures
    memory_seamlessness: float       # How naturally memory was integrated
    story_uniqueness: float          # How unique story selection was
    value_consistency: float         # Consistency with user values
    
    # Issues and recommendations
    memory_gaps: List[str]           # Missing expected memory usage
    memory_errors: List[str]         # Incorrect memory usage
    improvement_suggestions: List[str]
    effective_integrations: List[str]


class MemoryScenarioTester:
    """Tests agent memory utilization across different patterns."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.test_scenarios = self._create_memory_test_scenarios()
        self.memory_indicators = self._define_memory_indicators()
        
    async def test_memory_utilization(
        self,
        user_profile: UserProfile,
        test_patterns: Optional[List[MemoryUtilizationPattern]] = None
    ) -> Dict[MemoryUtilizationPattern, List[MemoryUtilizationResult]]:
        """Test memory utilization across specified patterns."""
        
        patterns_to_test = test_patterns or list(MemoryUtilizationPattern)
        results = {}
        
        for pattern in patterns_to_test:
            self.logger.info(f"Testing memory pattern: {pattern.value}")
            
            pattern_scenarios = [s for s in self.test_scenarios if s.pattern == pattern]
            pattern_results = []
            
            for scenario in pattern_scenarios:
                # Only test scenarios that user profile supports
                if self._profile_supports_scenario(user_profile, scenario):
                    result = await self._test_memory_scenario(scenario, user_profile)
                    pattern_results.append(result)
                else:
                    self.logger.info(f"Skipping scenario {scenario.test_id} - insufficient profile data")
            
            results[pattern] = pattern_results
        
        return results
    
    def _create_memory_test_scenarios(self) -> List[MemoryTestScenario]:
        """Create comprehensive memory test scenarios."""
        
        scenarios = []
        
        # ACTIVITY LEVERAGE scenarios
        scenarios.extend([
            MemoryTestScenario(
                test_id="ACTIVITY-001-leadership-story",
                pattern=MemoryUtilizationPattern.ACTIVITY_LEVERAGE,
                test_description="User wants essay about leadership, agent should leverage leadership activities",
                required_memory_types=[MemoryType.ACTIVITIES, MemoryType.LEADERSHIP_ROLES],
                user_input="I want to write about a time I showed leadership for my college essay.",
                expected_memory_usage=["leadership activities", "team captain role", "organizing events"],
                memory_integration_indicators=[
                    "mentions specific leadership role",
                    "references leadership activities",
                    "connects to leadership impact"
                ],
                success_criteria={
                    "activity_usage": 0.4,
                    "relevance": 0.3,
                    "integration": 0.3
                },
                difficulty_level="easy"
            ),
            
            MemoryTestScenario(
                test_id="ACTIVITY-002-passion-exploration",
                pattern=MemoryUtilizationPattern.ACTIVITY_LEVERAGE,
                test_description="User asks about passion essay, agent should use passion-related activities",
                required_memory_types=[MemoryType.ACTIVITIES, MemoryType.ACADEMIC_INTERESTS],
                user_input="Help me write about something I'm passionate about for my Stanford essay.",
                expected_memory_usage=["passionate activities", "academic interests", "time investment"],
                memory_integration_indicators=[
                    "references specific passionate activity",
                    "mentions time dedication",
                    "connects to personal motivation"
                ],
                success_criteria={
                    "passion_identification": 0.4,
                    "activity_connection": 0.3,
                    "authenticity": 0.3
                },
                difficulty_level="medium"
            ),
            
            MemoryTestScenario(
                test_id="ACTIVITY-003-service-impact",
                pattern=MemoryUtilizationPattern.ACTIVITY_LEVERAGE,
                test_description="User wants community service essay, agent should leverage volunteer work",
                required_memory_types=[MemoryType.VOLUNTEER_WORK, MemoryType.ACTIVITIES],
                user_input="I need to write about my community service impact for the UC application.",
                expected_memory_usage=["volunteer activities", "service impact", "community involvement"],
                memory_integration_indicators=[
                    "mentions specific volunteer work",
                    "quantifies service impact",
                    "connects to community values"
                ],
                success_criteria={
                    "service_specificity": 0.4,
                    "impact_demonstration": 0.3,
                    "value_alignment": 0.3
                },
                difficulty_level="medium"
            )
        ])
        
        # ESSAY ADAPTATION scenarios
        scenarios.extend([
            MemoryTestScenario(
                test_id="ADAPT-001-prompt-reframe",
                pattern=MemoryUtilizationPattern.ESSAY_ADAPTATION,
                test_description="User wants to adapt previous essay for new prompt",
                required_memory_types=[MemoryType.ESSAY_HISTORY],
                user_input="I wrote about my robotics project before. Can I use that story for this new diversity prompt?",
                expected_memory_usage=["previous robotics essay", "essay themes", "story elements"],
                memory_integration_indicators=[
                    "references previous essay",
                    "identifies adaptable elements",
                    "suggests new angle for prompt"
                ],
                success_criteria={
                    "essay_recall": 0.4,
                    "adaptation_strategy": 0.3,
                    "prompt_alignment": 0.3
                },
                difficulty_level="medium"
            ),
            
            MemoryTestScenario(
                test_id="ADAPT-002-theme-evolution",
                pattern=MemoryUtilizationPattern.ESSAY_ADAPTATION,
                test_description="User wants to evolve theme from previous essay",
                required_memory_types=[MemoryType.ESSAY_HISTORY, MemoryType.CORE_VALUES],
                user_input="My last essay was about overcoming challenges. How can I write about growth without repeating myself?",
                expected_memory_usage=["previous challenge essay", "growth themes", "different examples"],
                memory_integration_indicators=[
                    "acknowledges previous essay theme",
                    "suggests complementary angle",
                    "offers different examples"
                ],
                success_criteria={
                    "theme_awareness": 0.4,
                    "differentiation": 0.3,
                    "growth_focus": 0.3
                },
                difficulty_level="hard"
            ),
            
            MemoryTestScenario(
                test_id="ADAPT-003-school-specificity",
                pattern=MemoryUtilizationPattern.ESSAY_ADAPTATION,
                test_description="User wants to adapt essay for different school requirements",
                required_memory_types=[MemoryType.ESSAY_HISTORY],
                user_input="I have a good Common App essay about innovation. How do I adapt it for MIT's 'pleasure' prompt?",
                expected_memory_usage=["innovation essay content", "core story elements", "adaptable themes"],
                memory_integration_indicators=[
                    "references innovation essay",
                    "identifies pleasure aspect",
                    "suggests content adaptation"
                ],
                success_criteria={
                    "content_recall": 0.4,
                    "prompt_understanding": 0.3,
                    "adaptation_feasibility": 0.3
                },
                difficulty_level="hard"
            )
        ])
        
        # CROSS-PROMPT REUSE scenarios
        scenarios.extend([
            MemoryTestScenario(
                test_id="REUSE-001-story-diversity",
                pattern=MemoryUtilizationPattern.CROSS_PROMPT_REUSE,
                test_description="User applying to multiple schools, needs story diversity",
                required_memory_types=[MemoryType.ESSAY_HISTORY, MemoryType.ACTIVITIES],
                user_input="I've written about my debate experience for two essays already. What other stories could I tell?",
                expected_memory_usage=["previous essay topics", "unused activities", "alternative stories"],
                memory_integration_indicators=[
                    "acknowledges previous story use",
                    "suggests different activities",
                    "ensures story diversity"
                ],
                success_criteria={
                    "story_tracking": 0.4,
                    "diversity_awareness": 0.3,
                    "alternative_identification": 0.3
                },
                difficulty_level="medium"
            ),
            
            MemoryTestScenario(
                test_id="REUSE-002-portfolio-coherence",
                pattern=MemoryUtilizationPattern.CROSS_PROMPT_REUSE,
                test_description="User wants cohesive application portfolio",
                required_memory_types=[MemoryType.ESSAY_HISTORY, MemoryType.CORE_VALUES],
                user_input="I want my essays to tell a cohesive story about who I am. How do my current essays work together?",
                expected_memory_usage=["all previous essays", "core value themes", "narrative coherence"],
                memory_integration_indicators=[
                    "analyzes essay portfolio",
                    "identifies value themes",
                    "suggests coherence improvements"
                ],
                success_criteria={
                    "portfolio_analysis": 0.4,
                    "theme_identification": 0.3,
                    "coherence_planning": 0.3
                },
                difficulty_level="hard"
            ),
            
            MemoryTestScenario(
                test_id="REUSE-003-angle-variation",
                pattern=MemoryUtilizationPattern.CROSS_PROMPT_REUSE,
                test_description="User wants different angles on same experience",
                required_memory_types=[MemoryType.ESSAY_HISTORY, MemoryType.DEFINING_MOMENTS],
                user_input="I wrote about my family immigration story for one essay. Can I write about it again but focus on a different aspect?",
                expected_memory_usage=["immigration essay", "defining moments", "alternative angles"],
                memory_integration_indicators=[
                    "recalls previous immigration essay",
                    "identifies different angle",
                    "suggests unique focus"
                ],
                success_criteria={
                    "story_recall": 0.4,
                    "angle_differentiation": 0.3,
                    "uniqueness": 0.3
                },
                difficulty_level="medium"
            )
        ])
        
        # PROFILE INTEGRATION scenarios
        scenarios.extend([
            MemoryTestScenario(
                test_id="PROFILE-001-value-alignment",
                pattern=MemoryUtilizationPattern.PROFILE_INTEGRATION,
                test_description="Agent uses core values in essay suggestions",
                required_memory_types=[MemoryType.CORE_VALUES, MemoryType.DEFINING_MOMENTS],
                user_input="What should I write about for the 'what matters most' prompt?",
                expected_memory_usage=["core values", "value-aligned experiences", "defining moments"],
                memory_integration_indicators=[
                    "references user's core values",
                    "suggests value-aligned stories",
                    "connects to defining moments"
                ],
                success_criteria={
                    "value_integration": 0.4,
                    "story_alignment": 0.3,
                    "authenticity": 0.3
                },
                difficulty_level="easy"
            ),
            
            MemoryTestScenario(
                test_id="PROFILE-002-background-leverage",
                pattern=MemoryUtilizationPattern.PROFILE_INTEGRATION,
                test_description="Agent leverages family/personal background appropriately",
                required_memory_types=[MemoryType.FAMILY_BACKGROUND, MemoryType.PERSONAL_CHALLENGES],
                user_input="I want to write about how my background shaped me, but I'm not sure what's worth sharing.",
                expected_memory_usage=["family background", "personal challenges", "formative experiences"],
                memory_integration_indicators=[
                    "references family background",
                    "mentions relevant challenges",
                    "suggests appropriate sharing level"
                ],
                success_criteria={
                    "background_usage": 0.4,
                    "appropriate_disclosure": 0.3,
                    "impact_connection": 0.3
                },
                difficulty_level="medium"
            ),
            
            MemoryTestScenario(
                test_id="PROFILE-003-interest-connection",
                pattern=MemoryUtilizationPattern.PROFILE_INTEGRATION,
                test_description="Agent connects academic interests to essay content",
                required_memory_types=[MemoryType.ACADEMIC_INTERESTS, MemoryType.ACTIVITIES],
                user_input="Help me write about why I want to study engineering.",
                expected_memory_usage=["academic interests", "STEM activities", "engineering passion"],
                memory_integration_indicators=[
                    "references academic interests",
                    "connects to relevant activities",
                    "demonstrates genuine passion"
                ],
                success_criteria={
                    "interest_integration": 0.4,
                    "activity_connection": 0.3,
                    "passion_authenticity": 0.3
                },
                difficulty_level="easy"
            )
        ])
        
        # CONTEXTUAL RECALL scenarios
        scenarios.extend([
            MemoryTestScenario(
                test_id="RECALL-001-specific-retrieval",
                pattern=MemoryUtilizationPattern.CONTEXTUAL_RECALL,
                test_description="Agent recalls specific relevant information when prompted",
                required_memory_types=[MemoryType.ACTIVITIES, MemoryType.DEFINING_MOMENTS],
                user_input="What experiences do I have that show resilience?",
                expected_memory_usage=["resilience-related activities", "overcoming challenges", "growth moments"],
                memory_integration_indicators=[
                    "identifies resilience experiences",
                    "provides specific examples",
                    "explains resilience demonstration"
                ],
                success_criteria={
                    "retrieval_accuracy": 0.4,
                    "relevance": 0.3,
                    "specificity": 0.3
                },
                difficulty_level="medium"
            ),
            
            MemoryTestScenario(
                test_id="RECALL-002-thematic-search",
                pattern=MemoryUtilizationPattern.CONTEXTUAL_RECALL,
                test_description="Agent finds thematically related memories across categories",
                required_memory_types=[MemoryType.ACTIVITIES, MemoryType.VOLUNTEER_WORK, MemoryType.CORE_VALUES],
                user_input="I want to write about social justice. What experiences do I have in this area?",
                expected_memory_usage=["social justice activities", "relevant volunteer work", "justice values"],
                memory_integration_indicators=[
                    "identifies social justice theme",
                    "finds cross-category examples",
                    "connects diverse experiences"
                ],
                success_criteria={
                    "thematic_coherence": 0.4,
                    "cross_category_search": 0.3,
                    "relevance": 0.3
                },
                difficulty_level="hard"
            )
        ])
        
        return scenarios
    
    def _define_memory_indicators(self) -> Dict[MemoryType, List[str]]:
        """Define language patterns that indicate memory usage."""
        
        return {
            MemoryType.ACTIVITIES: [
                "your experience with", "your work in", "your involvement in",
                "your role as", "when you", "your project", "your team"
            ],
            
            MemoryType.ESSAY_HISTORY: [
                "your previous essay", "you wrote about", "your earlier work",
                "in your other essay", "you already covered", "building on"
            ],
            
            MemoryType.DEFINING_MOMENTS: [
                "when you experienced", "that time you", "your journey with",
                "how you overcame", "your growth from", "that experience where"
            ],
            
            MemoryType.CORE_VALUES: [
                "what matters to you", "your values", "what you care about",
                "your principles", "what drives you", "your priorities"
            ],
            
            MemoryType.FAMILY_BACKGROUND: [
                "your family", "your background", "where you come from",
                "your heritage", "your upbringing", "your cultural"
            ],
            
            MemoryType.ACADEMIC_INTERESTS: [
                "your interest in", "your passion for", "your study of",
                "your academic focus", "your major", "your field"
            ]
        }
    
    def _profile_supports_scenario(
        self,
        user_profile: UserProfile,
        scenario: MemoryTestScenario
    ) -> bool:
        """Check if user profile has required data for scenario."""
        
        for memory_type in scenario.required_memory_types:
            if not self._profile_has_memory_type(user_profile, memory_type):
                return False
        
        return True
    
    def _profile_has_memory_type(
        self,
        user_profile: UserProfile,
        memory_type: MemoryType
    ) -> bool:
        """Check if profile has specific memory type data."""
        
        if memory_type == MemoryType.ACTIVITIES:
            return len(user_profile.activities) > 0
        elif memory_type == MemoryType.ESSAY_HISTORY:
            return len(user_profile.essay_history) > 0
        elif memory_type == MemoryType.DEFINING_MOMENTS:
            return len(user_profile.defining_moments) > 0
        elif memory_type == MemoryType.CORE_VALUES:
            return len(user_profile.core_values) > 0
        elif memory_type == MemoryType.ACADEMIC_INTERESTS:
            return len(user_profile.academic_interests) > 0
        elif memory_type == MemoryType.FAMILY_BACKGROUND:
            return bool(user_profile.family_background)
        elif memory_type == MemoryType.LEADERSHIP_ROLES:
            return len(user_profile.leadership_roles) > 0
        elif memory_type == MemoryType.VOLUNTEER_WORK:
            return len(user_profile.volunteer_work) > 0
        
        return True  # Default to true for other types
    
    async def _test_memory_scenario(
        self,
        scenario: MemoryTestScenario,
        user_profile: UserProfile
    ) -> MemoryUtilizationResult:
        """Test a single memory utilization scenario."""
        
        # Create conversation scenario
        conversation_scenario = self._create_memory_conversation_scenario(scenario, user_profile)
        
        # Execute conversation
        runner = ConversationRunner(verbose=False)
        conversation_result = await runner.execute_evaluation(conversation_scenario, user_profile)
        
        # Extract agent response
        agent_response = self._extract_agent_response(conversation_result)
        
        # Analyze memory usage
        memory_types_used = self._identify_memory_types_used(agent_response, user_profile)
        specific_memories = self._identify_specific_memories_used(agent_response, user_profile)
        
        # Calculate scores
        integration_score = self._calculate_memory_integration_score(
            agent_response, scenario, specific_memories
        )
        
        relevance_score = self._calculate_memory_relevance_score(
            agent_response, scenario, memory_types_used
        )
        
        accuracy_score = self._calculate_memory_accuracy_score(
            agent_response, user_profile, specific_memories
        )
        
        pattern_score = self._calculate_pattern_adherence_score(
            agent_response, scenario, memory_types_used
        )
        
        personalization_score = self._calculate_personalization_score(
            agent_response, user_profile
        )
        
        context_score = self._calculate_context_awareness_score(
            agent_response, scenario, user_profile
        )
        
        # Quality measures
        seamlessness = self._calculate_memory_seamlessness(agent_response)
        uniqueness = self._calculate_story_uniqueness(agent_response, user_profile)
        consistency = self._calculate_value_consistency(agent_response, user_profile)
        
        # Identify issues
        memory_gaps = self._identify_memory_gaps(scenario, memory_types_used, specific_memories)
        memory_errors = self._identify_memory_errors(agent_response, user_profile)
        
        # Generate recommendations
        improvements = self._generate_memory_improvements(scenario, memory_gaps, memory_errors)
        effective_uses = self._identify_effective_integrations(agent_response, specific_memories)
        
        return MemoryUtilizationResult(
            test_id=scenario.test_id,
            pattern=scenario.pattern,
            agent_response=agent_response,
            memory_types_accessed=memory_types_used,
            specific_memories_used=specific_memories,
            memory_integration_score=integration_score,
            relevance_score=relevance_score,
            accuracy_score=accuracy_score,
            pattern_adherence_score=pattern_score,
            personalization_score=personalization_score,
            context_awareness_score=context_score,
            memory_seamlessness=seamlessness,
            story_uniqueness=uniqueness,
            value_consistency=consistency,
            memory_gaps=memory_gaps,
            memory_errors=memory_errors,
            improvement_suggestions=improvements,
            effective_integrations=effective_uses
        )
    
    def _create_memory_conversation_scenario(
        self,
        memory_scenario: MemoryTestScenario,
        user_profile: UserProfile
    ) -> ConversationScenario:
        """Create conversation scenario for memory testing."""
        
        from .conversational_scenarios import ConversationPhase, SuccessCriteria
        
        # Create test phase
        test_phase = ConversationPhase(
            phase_name="memory_test",
            user_input=memory_scenario.user_input,
            expected_agent_behavior=f"memory_pattern_{memory_scenario.pattern.value}",
            expected_memory_use=[mt.value for mt in memory_scenario.required_memory_types],
            success_indicators=memory_scenario.memory_integration_indicators
        )
        
        # Mock conversation scenario
        return ConversationScenario(
            eval_id=memory_scenario.test_id,
            name=f"Memory Test: {memory_scenario.pattern.value}",
            category="memory_test",
            description=memory_scenario.test_description,
            school="Test University",
            prompt="Test prompt for memory evaluation",
            word_limit=500,
            user_profile=user_profile.profile_id,
            autonomy_level="collaborative",  # Standard for memory tests
            conversation_flow=[test_phase],
            success_criteria=SuccessCriteria(
                conversation_turns={"min": 1, "max": 3},
                tools_used={"min": 1, "expected": ["brainstorm", "story_development"]},
                final_word_count={"min": 100, "max": 600},
                prompt_relevance={"min": 3.5},
                conversation_quality={"naturalness": 3.5}
            ),
            difficulty="medium",
            estimated_duration_minutes=5,
            tags=["memory_test", memory_scenario.pattern.value]
        )
    
    def _extract_agent_response(self, conversation_result: ConversationResult) -> str:
        """Extract agent response from conversation result."""
        
        if conversation_result.conversation_turns:
            return conversation_result.conversation_turns[0].agent_response
        return ""
    
    def _identify_memory_types_used(
        self,
        agent_response: str,
        user_profile: UserProfile
    ) -> List[MemoryType]:
        """Identify which memory types were used in the response."""
        
        memory_types_used = []
        response_lower = agent_response.lower()
        
        for memory_type, indicators in self.memory_indicators.items():
            for indicator in indicators:
                if indicator in response_lower:
                    memory_types_used.append(memory_type)
                    break
        
        return list(set(memory_types_used))  # Remove duplicates
    
    def _identify_specific_memories_used(
        self,
        agent_response: str,
        user_profile: UserProfile
    ) -> List[str]:
        """Identify specific memories referenced in the response."""
        
        specific_memories = []
        response_lower = agent_response.lower()
        
        # Check for activity names
        for activity in user_profile.activities:
            if activity.name.lower() in response_lower:
                specific_memories.append(f"Activity: {activity.name}")
        
        # Check for essay topics
        for essay in user_profile.essay_history:
            key_words = essay.topic.lower().split()
            if any(word in response_lower for word in key_words if len(word) > 3):
                specific_memories.append(f"Essay: {essay.topic}")
        
        # Check for values
        for value in user_profile.core_values:
            if value.lower() in response_lower:
                specific_memories.append(f"Value: {value}")
        
        # Check for defining moments (by keywords)
        for moment in user_profile.defining_moments:
            key_words = moment.event.lower().split()
            if any(word in response_lower for word in key_words if len(word) > 4):
                specific_memories.append(f"Moment: {moment.event}")
        
        return specific_memories
    
    def _calculate_memory_integration_score(
        self,
        agent_response: str,
        scenario: MemoryTestScenario,
        specific_memories: List[str]
    ) -> float:
        """Calculate how well memory was integrated into response."""
        
        score = 0.0
        
        # Points for using expected memory types
        response_lower = agent_response.lower()
        integration_indicators_met = sum(
            1 for indicator in scenario.memory_integration_indicators
            if any(word in response_lower for word in indicator.lower().split())
        )
        
        if scenario.memory_integration_indicators:
            score += (integration_indicators_met / len(scenario.memory_integration_indicators)) * 0.6
        
        # Points for specific memory usage
        if specific_memories:
            score += min(len(specific_memories) / 3, 1.0) * 0.4
        
        return min(score, 1.0)
    
    def _calculate_memory_relevance_score(
        self,
        agent_response: str,
        scenario: MemoryTestScenario,
        memory_types_used: List[MemoryType]
    ) -> float:
        """Calculate relevance of memory usage to the scenario."""
        
        # Check if required memory types were accessed
        required_accessed = sum(
            1 for memory_type in scenario.required_memory_types
            if memory_type in memory_types_used
        )
        
        if scenario.required_memory_types:
            return required_accessed / len(scenario.required_memory_types)
        
        return 1.0 if memory_types_used else 0.0
    
    def _calculate_memory_accuracy_score(
        self,
        agent_response: str,
        user_profile: UserProfile,
        specific_memories: List[str]
    ) -> float:
        """Calculate accuracy of memory recall and usage."""
        
        # For now, assume memory is accurate if specific memories are mentioned
        # In a real implementation, this would check for factual accuracy
        return 1.0 if specific_memories else 0.5
    
    def _calculate_pattern_adherence_score(
        self,
        agent_response: str,
        scenario: MemoryTestScenario,
        memory_types_used: List[MemoryType]
    ) -> float:
        """Calculate adherence to the specific memory utilization pattern."""
        
        response_lower = agent_response.lower()
        
        if scenario.pattern == MemoryUtilizationPattern.ACTIVITY_LEVERAGE:
            # Should reference specific activities
            return 1.0 if MemoryType.ACTIVITIES in memory_types_used else 0.3
        
        elif scenario.pattern == MemoryUtilizationPattern.ESSAY_ADAPTATION:
            # Should reference previous essays
            return 1.0 if MemoryType.ESSAY_HISTORY in memory_types_used else 0.2
        
        elif scenario.pattern == MemoryUtilizationPattern.CROSS_PROMPT_REUSE:
            # Should show awareness of multiple essays
            portfolio_awareness = any(phrase in response_lower for phrase in [
                "other essays", "portfolio", "different story", "avoid repetition"
            ])
            return 1.0 if portfolio_awareness else 0.4
        
        elif scenario.pattern == MemoryUtilizationPattern.PROFILE_INTEGRATION:
            # Should use core profile elements
            return 1.0 if MemoryType.CORE_VALUES in memory_types_used else 0.5
        
        return 0.7  # Default moderate score
    
    def _calculate_personalization_score(
        self,
        agent_response: str,
        user_profile: UserProfile
    ) -> float:
        """Calculate how personalized the response is to the user."""
        
        personalization_indicators = [
            user_profile.name.lower() if user_profile.name else "",
            user_profile.intended_major.lower() if user_profile.intended_major else "",
            user_profile.location.lower() if user_profile.location else ""
        ]
        
        response_lower = agent_response.lower()
        personal_references = sum(
            1 for indicator in personalization_indicators
            if indicator and indicator in response_lower
        )
        
        # Also check for "your" language indicating personalization
        personal_language = sum(
            1 for phrase in ["your", "you", "you've", "you're"]
            if phrase in response_lower
        )
        
        base_score = min(personal_references / 2, 0.5) + min(personal_language / 10, 0.5)
        return min(base_score, 1.0)
    
    def _calculate_context_awareness_score(
        self,
        agent_response: str,
        scenario: MemoryTestScenario,
        user_profile: UserProfile
    ) -> float:
        """Calculate agent's awareness of user context."""
        
        context_indicators = 0
        total_indicators = 0
        
        # Check for awareness of user's stage (high school, etc.)
        if user_profile.age < 18:
            total_indicators += 1
            if any(phrase in agent_response.lower() for phrase in ["high school", "student", "college application"]):
                context_indicators += 1
        
        # Check for awareness of user's background
        if user_profile.first_generation:
            total_indicators += 1
            if any(phrase in agent_response.lower() for phrase in ["first generation", "college process", "family"]):
                context_indicators += 1
        
        # Check for awareness of user's interests
        if user_profile.academic_interests:
            total_indicators += 1
            interest_mentioned = any(
                interest.lower() in agent_response.lower()
                for interest in user_profile.academic_interests
            )
            if interest_mentioned:
                context_indicators += 1
        
        return context_indicators / total_indicators if total_indicators > 0 else 0.7
    
    def _calculate_memory_seamlessness(self, agent_response: str) -> float:
        """Calculate how naturally memory was woven into response."""
        
        # Look for natural integration vs. awkward insertion
        seamlessness_indicators = [
            "remember", "as you", "your experience", "building on",
            "given that", "since you", "considering your"
        ]
        
        response_lower = agent_response.lower()
        natural_transitions = sum(
            1 for indicator in seamlessness_indicators
            if indicator in response_lower
        )
        
        # Penalize awkward memory insertion
        awkward_patterns = [
            "according to your profile", "your data shows", "in your file"
        ]
        
        awkward_count = sum(
            1 for pattern in awkward_patterns
            if pattern in response_lower
        )
        
        base_score = min(natural_transitions / 3, 1.0)
        penalty = min(awkward_count * 0.3, 0.5)
        
        return max(base_score - penalty, 0.0)
    
    def _calculate_story_uniqueness(
        self,
        agent_response: str,
        user_profile: UserProfile
    ) -> float:
        """Calculate uniqueness of story suggestions."""
        
        # Check if response suggests diverse stories
        uniqueness_indicators = [
            "different", "another", "alternative", "various", "range of"
        ]
        
        response_lower = agent_response.lower()
        uniqueness_score = sum(
            1 for indicator in uniqueness_indicators
            if indicator in response_lower
        )
        
        return min(uniqueness_score / 2, 1.0)
    
    def _calculate_value_consistency(
        self,
        agent_response: str,
        user_profile: UserProfile
    ) -> float:
        """Calculate consistency with user's stated values."""
        
        if not user_profile.core_values:
            return 0.7  # Default score if no values stored
        
        response_lower = agent_response.lower()
        value_alignment = sum(
            1 for value in user_profile.core_values
            if any(word in response_lower for word in value.lower().split())
        )
        
        return min(value_alignment / len(user_profile.core_values), 1.0)
    
    def _identify_memory_gaps(
        self,
        scenario: MemoryTestScenario,
        memory_types_used: List[MemoryType],
        specific_memories: List[str]
    ) -> List[str]:
        """Identify gaps in expected memory usage."""
        
        gaps = []
        
        # Check for missing required memory types
        for memory_type in scenario.required_memory_types:
            if memory_type not in memory_types_used:
                gaps.append(f"Missing memory type: {memory_type.value}")
        
        # Check for missing expected memories
        for expected in scenario.expected_memory_usage:
            if not any(expected.lower() in memory.lower() for memory in specific_memories):
                gaps.append(f"Missing expected memory: {expected}")
        
        return gaps
    
    def _identify_memory_errors(
        self,
        agent_response: str,
        user_profile: UserProfile
    ) -> List[str]:
        """Identify errors in memory usage."""
        
        errors = []
        
        # Check for factual inconsistencies
        # This would be more sophisticated in a real implementation
        response_lower = agent_response.lower()
        
        # Simple check for contradictions
        if "math" in response_lower and "English" in user_profile.academic_interests:
            if "math" not in [interest.lower() for interest in user_profile.academic_interests]:
                errors.append("Mentioned math interest not in user profile")
        
        return errors
    
    def _generate_memory_improvements(
        self,
        scenario: MemoryTestScenario,
        memory_gaps: List[str],
        memory_errors: List[str]
    ) -> List[str]:
        """Generate improvement suggestions for memory usage."""
        
        improvements = []
        
        if memory_gaps:
            improvements.append("Improve memory retrieval to access all relevant information")
        
        if memory_errors:
            improvements.append("Verify memory accuracy before including in responses")
        
        if scenario.pattern == MemoryUtilizationPattern.ACTIVITY_LEVERAGE:
            improvements.append("Better integration of specific activity details")
        
        elif scenario.pattern == MemoryUtilizationPattern.ESSAY_ADAPTATION:
            improvements.append("More sophisticated essay adaptation strategies")
        
        return improvements
    
    def _identify_effective_integrations(
        self,
        agent_response: str,
        specific_memories: List[str]
    ) -> List[str]:
        """Identify effective memory integrations."""
        
        effective = []
        
        if specific_memories:
            effective.append("Successfully referenced specific user experiences")
        
        if "your" in agent_response.lower():
            effective.append("Used personalized language effectively")
        
        return effective
    
    def generate_memory_report(
        self,
        test_results: Dict[MemoryUtilizationPattern, List[MemoryUtilizationResult]]
    ) -> Dict[str, Any]:
        """Generate comprehensive memory utilization report."""
        
        report = {
            "overall_memory_score": 0.0,
            "pattern_scores": {},
            "memory_strengths": [],
            "memory_weaknesses": [],
            "recommendations": [],
            "detailed_results": {}
        }
        
        total_score = 0.0
        total_tests = 0
        
        for pattern, results in test_results.items():
            if results:
                pattern_score = sum(r.memory_integration_score for r in results) / len(results)
                report["pattern_scores"][pattern.value] = pattern_score
                total_score += pattern_score
                total_tests += 1
                
                # Collect insights
                for result in results:
                    report["memory_strengths"].extend(result.effective_integrations)
                    report["memory_weaknesses"].extend(result.memory_gaps)
                    report["recommendations"].extend(result.improvement_suggestions)
        
        report["overall_memory_score"] = total_score / total_tests if total_tests > 0 else 0.0
        
        # Remove duplicates
        report["memory_strengths"] = list(set(report["memory_strengths"]))
        report["memory_weaknesses"] = list(set(report["memory_weaknesses"]))
        report["recommendations"] = list(set(report["recommendations"]))
        
        # Add detailed results
        for pattern, results in test_results.items():
            report["detailed_results"][pattern.value] = [
                {
                    "test_id": r.test_id,
                    "integration_score": r.memory_integration_score,
                    "relevance_score": r.relevance_score,
                    "personalization_score": r.personalization_score,
                    "memories_used": r.specific_memories_used,
                    "gaps": r.memory_gaps
                }
                for r in results
            ]
        
        return report


# Utility function for comprehensive memory testing
async def run_comprehensive_memory_test(
    user_profile: UserProfile,
    output_file: Optional[str] = None
) -> Dict[str, Any]:
    """Run comprehensive memory utilization testing."""
    
    tester = MemoryScenarioTester()
    
    # Test all memory patterns
    results = await tester.test_memory_utilization(user_profile)
    
    # Generate report
    report = tester.generate_memory_report(results)
    
    # Save results if requested
    if output_file:
        import json
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
    
    return report


# Export key components
__all__ = [
    "MemoryScenarioTester",
    "MemoryUtilizationResult",
    "MemoryUtilizationPattern",
    "MemoryType",
    "run_comprehensive_memory_test"
] 