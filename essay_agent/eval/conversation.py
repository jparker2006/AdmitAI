"""essay_agent.eval.conversation

Comprehensive conversation quality evaluation system for testing conversation intelligence,
intent recognition accuracy, context tracking, and integration with essay workflow.
"""

import json
import time
import warnings
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path
import re
import statistics

from essay_agent.conversation import (
    ConversationManager, ConversationState, ConversationTurn, 
    ConversationFlowManager, ToolExecutionResult, ExecutionStatus,
    EssayContext, UserPreferences, ProactiveSuggestion
)
from essay_agent.memory.user_profile_schema import UserProfile
from essay_agent.llm_client import get_chat_llm
from essay_agent.utils.logging import debug_print


class ConversationEvaluationError(Exception):
    """Base exception for conversation evaluation failures"""
    pass


class IntentRecognitionError(ConversationEvaluationError):
    """Exception raised when intent recognition evaluation fails"""
    pass


class ContextTrackingError(ConversationEvaluationError):
    """Exception raised when context tracking evaluation fails"""
    pass


class QualityMetricsError(ConversationEvaluationError):
    """Exception raised when quality metrics calculation fails"""
    pass


@dataclass
class ConversationQualityMetrics:
    """Metrics for evaluating conversation quality"""
    relevance_score: float = 0.0
    helpfulness_score: float = 0.0
    coherence_score: float = 0.0
    suggestion_quality: float = 0.0
    overall_quality: float = 0.0
    turn_count: int = 0
    tool_success_rate: float = 0.0
    clarification_appropriateness: float = 0.0
    
    def calculate_overall_quality(self) -> float:
        """Calculate overall quality score as weighted average"""
        weights = {
            'relevance_score': 0.25,
            'helpfulness_score': 0.25,
            'coherence_score': 0.20,
            'suggestion_quality': 0.15,
            'tool_success_rate': 0.10,
            'clarification_appropriateness': 0.05
        }
        
        self.overall_quality = sum(
            getattr(self, metric) * weight 
            for metric, weight in weights.items()
        )
        return self.overall_quality


@dataclass
class IntentTestCase:
    """Test case for intent recognition evaluation"""
    user_input: str
    expected_intent: str
    context: Optional[str] = None
    confidence_threshold: float = 0.8
    category: str = "general"


@dataclass
class ConversationScenario:
    """Test scenario for context tracking evaluation"""
    scenario_name: str
    turns: List[Tuple[str, str]]  # (user_input, expected_response_type)
    expected_context: Dict[str, Any]
    success_criteria: Dict[str, float]
    description: str = ""


@dataclass
class ConversationEvaluationReport:
    """Comprehensive evaluation report for conversation system"""
    quality_metrics: ConversationQualityMetrics
    intent_recognition_accuracy: float
    context_tracking_success: float
    integration_test_results: Dict[str, bool]
    overall_score: float
    recommendations: List[str] = field(default_factory=list)
    execution_time: float = 0.0
    test_timestamp: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary for JSON serialization"""
        return {
            "quality_metrics": {
                "relevance_score": self.quality_metrics.relevance_score,
                "helpfulness_score": self.quality_metrics.helpfulness_score,
                "coherence_score": self.quality_metrics.coherence_score,
                "suggestion_quality": self.quality_metrics.suggestion_quality,
                "overall_quality": self.quality_metrics.overall_quality,
                "turn_count": self.quality_metrics.turn_count,
                "tool_success_rate": self.quality_metrics.tool_success_rate,
                "clarification_appropriateness": self.quality_metrics.clarification_appropriateness
            },
            "intent_recognition_accuracy": self.intent_recognition_accuracy,
            "context_tracking_success": self.context_tracking_success,
            "integration_test_results": self.integration_test_results,
            "overall_score": self.overall_score,
            "recommendations": self.recommendations,
            "execution_time": self.execution_time,
            "test_timestamp": self.test_timestamp
        }
    
    def save_to_file(self, filepath: str) -> None:
        """Save evaluation report to JSON file"""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)


class ConversationQualityEvaluator:
    """Evaluates conversation quality across multiple dimensions
    
    .. deprecated:: 1.0
        ConversationQualityEvaluator is deprecated. Use LLMEvaluator from 
        essay_agent.eval.llm_evaluator for sophisticated conversation evaluation.
        This class will be removed in a future version.
    """
    
    def __init__(self, llm_evaluator=None):
        warnings.warn(
            "ConversationQualityEvaluator is deprecated and will be removed in a future version. "
            "Use LLMEvaluator from essay_agent.eval.llm_evaluator instead for more sophisticated "
            "conversation evaluation with better accuracy and context understanding.",
            DeprecationWarning,
            stacklevel=2
        )
        self.llm_evaluator = llm_evaluator or get_chat_llm()
        self.relevance_threshold = 0.7
        self.helpfulness_threshold = 0.8
        self.coherence_threshold = 0.7
    
    def evaluate_conversation_quality(self, conversation_state: ConversationState) -> ConversationQualityMetrics:
        """Evaluate overall conversation quality"""
        try:
            metrics = ConversationQualityMetrics()
            
            if not conversation_state.history:
                return metrics
            
            metrics.turn_count = len(conversation_state.history)
            
            # Calculate individual metrics
            metrics.relevance_score = self._calculate_relevance_score(conversation_state.history)
            metrics.helpfulness_score = self._calculate_helpfulness_score(conversation_state.history)
            metrics.coherence_score = self._calculate_coherence_score(conversation_state.history)
            metrics.suggestion_quality = self._calculate_suggestion_quality(conversation_state.history)
            metrics.tool_success_rate = self._calculate_tool_success_rate(conversation_state.history)
            metrics.clarification_appropriateness = self._calculate_clarification_appropriateness(conversation_state.history)
            
            # Calculate overall quality
            metrics.calculate_overall_quality()
            
            return metrics
            
        except Exception as e:
            raise QualityMetricsError(f"Failed to evaluate conversation quality: {e}")
    
    def _calculate_relevance_score(self, conversation_turns: List[ConversationTurn]) -> float:
        """Calculate how relevant agent responses are to user inputs"""
        if not conversation_turns:
            return 0.0
        
        relevance_scores = []
        
        for turn in conversation_turns:
            # Simple relevance scoring based on keyword overlap and response length
            user_words = set(turn.user_input.lower().split())
            agent_words = set(turn.agent_response.lower().split())
            
            # Calculate keyword overlap
            overlap = len(user_words & agent_words)
            total_keywords = len(user_words | agent_words)
            
            if total_keywords > 0:
                keyword_score = overlap / total_keywords
            else:
                keyword_score = 0.0
            
            # Factor in response length (not too short, not too long)
            response_length = len(turn.agent_response)
            length_score = min(1.0, max(0.1, response_length / 200))  # Optimal around 200 chars
            
            # Combine scores
            relevance = (keyword_score * 0.6) + (length_score * 0.4)
            relevance_scores.append(relevance)
        
        return statistics.mean(relevance_scores) if relevance_scores else 0.0
    
    def _calculate_helpfulness_score(self, conversation_turns: List[ConversationTurn]) -> float:
        """Calculate how helpful agent responses are based on tool execution success"""
        if not conversation_turns:
            return 0.0
        
        helpfulness_scores = []
        
        for turn in conversation_turns:
            if turn.tool_results:
                # Score based on tool execution success
                successful_tools = [r for r in turn.tool_results if r.is_successful()]
                tool_success_rate = len(successful_tools) / len(turn.tool_results)
                
                # Factor in tool diversity (using different tools is more helpful)
                tool_types = set(r.tool_name for r in successful_tools)
                diversity_bonus = min(0.2, len(tool_types) * 0.1)
                
                # Cap helpfulness at 1.0
                helpfulness = min(1.0, tool_success_rate + diversity_bonus)
            else:
                # For non-tool turns, score based on response characteristics
                response = turn.agent_response.lower()
                
                # Check for helpful patterns
                helpful_indicators = [
                    "suggestions:", "next steps:", "try saying:",
                    "would you like", "i can help", "let me"
                ]
                
                helpful_score = sum(1 for indicator in helpful_indicators if indicator in response)
                helpfulness = min(1.0, helpful_score * 0.2)
            
            helpfulness_scores.append(helpfulness)
        
        return statistics.mean(helpfulness_scores) if helpfulness_scores else 0.0
    
    def _calculate_coherence_score(self, conversation_turns: List[ConversationTurn]) -> float:
        """Calculate conversation coherence across turns"""
        if len(conversation_turns) < 2:
            return 1.0  # Single turn is trivially coherent
        
        coherence_scores = []
        
        for i in range(1, len(conversation_turns)):
            prev_turn = conversation_turns[i-1]
            curr_turn = conversation_turns[i]
            
            # Check for topic consistency
            prev_topics = self._extract_topics(prev_turn.user_input + " " + prev_turn.agent_response)
            curr_topics = self._extract_topics(curr_turn.user_input + " " + curr_turn.agent_response)
            
            topic_overlap = len(prev_topics & curr_topics)
            topic_total = len(prev_topics | curr_topics)
            
            if topic_total > 0:
                topic_coherence = topic_overlap / topic_total
            else:
                topic_coherence = 0.5  # Neutral score
            
            # Check for logical flow
            flow_indicators = [
                "based on", "following up", "as you mentioned", 
                "continuing", "next", "now that"
            ]
            
            curr_response = curr_turn.agent_response.lower()
            flow_score = sum(1 for indicator in flow_indicators if indicator in curr_response)
            flow_coherence = min(1.0, flow_score * 0.3)
            
            # Combine scores
            coherence = (topic_coherence * 0.7) + (flow_coherence * 0.3)
            coherence_scores.append(coherence)
        
        return statistics.mean(coherence_scores) if coherence_scores else 0.0
    
    def _calculate_suggestion_quality(self, conversation_turns: List[ConversationTurn]) -> float:
        """Calculate quality of proactive suggestions"""
        suggestion_turns = [
            turn for turn in conversation_turns 
            if "suggestions:" in turn.agent_response.lower() or "🔮" in turn.agent_response
        ]
        
        if not suggestion_turns:
            return 0.7  # Neutral score for no suggestions
        
        quality_scores = []
        
        for turn in suggestion_turns:
            response = turn.agent_response.lower()
            
            # Check for suggestion quality indicators
            quality_indicators = [
                "specific", "actionable", "next step", 
                "recommend", "try", "consider"
            ]
            
            quality_score = sum(1 for indicator in quality_indicators if indicator in response)
            
            # Check for suggestion structure (numbered lists, etc.)
            structure_score = 0.2 if re.search(r'\d+\.', turn.agent_response) else 0.0
            
            # Check for variety in suggestions
            variety_score = 0.1 if len(turn.agent_response.split('\n')) > 3 else 0.0
            
            total_score = min(1.0, (quality_score * 0.2) + structure_score + variety_score + 0.5)
            quality_scores.append(total_score)
        
        return statistics.mean(quality_scores) if quality_scores else 0.0
    
    def _calculate_tool_success_rate(self, conversation_turns: List[ConversationTurn]) -> float:
        """Calculate overall tool execution success rate"""
        all_tool_results = []
        
        for turn in conversation_turns:
            all_tool_results.extend(turn.tool_results)
        
        if not all_tool_results:
            return 0.8  # Neutral score for no tool usage
        
        successful_tools = [r for r in all_tool_results if r.is_successful()]
        return len(successful_tools) / len(all_tool_results)
    
    def _calculate_clarification_appropriateness(self, conversation_turns: List[ConversationTurn]) -> float:
        """Calculate appropriateness of clarification questions"""
        clarification_turns = [
            turn for turn in conversation_turns 
            if "🤔" in turn.agent_response or "could you" in turn.agent_response.lower()
        ]
        
        if not clarification_turns:
            return 0.9  # High score for no inappropriate clarifications
        
        appropriate_scores = []
        
        for turn in clarification_turns:
            user_input = turn.user_input.lower()
            
            # Check if clarification was appropriate
            vague_indicators = ["help", "this", "that", "it"]
            short_input = len(user_input.split()) <= 3
            
            vague_score = sum(1 for indicator in vague_indicators if indicator in user_input)
            
            # Appropriate if input was vague or short
            appropriate = (vague_score > 0) or short_input
            appropriate_scores.append(1.0 if appropriate else 0.3)
        
        return statistics.mean(appropriate_scores) if appropriate_scores else 0.0
    
    def _extract_topics(self, text: str) -> set:
        """Extract topics from text for coherence analysis"""
        # Simple topic extraction based on common essay-related terms
        essay_topics = {
            "essay", "draft", "outline", "brainstorm", "story", "college", 
            "personal", "statement", "leadership", "challenge", "community",
            "stanford", "harvard", "mit", "yale", "writing", "revision"
        }
        
        words = set(text.lower().split())
        return words & essay_topics


class IntentRecognitionEvaluator:
    """Evaluates intent recognition accuracy"""
    
    def __init__(self, flow_manager: ConversationFlowManager):
        self.flow_manager = flow_manager
        self.test_cases = self._load_intent_test_cases()
    
    def evaluate_intent_accuracy(self) -> Dict[str, float]:
        """Evaluate intent recognition accuracy against ground truth"""
        try:
            results = {
                'predictions': [],
                'ground_truth': [],
                'accuracy_by_intent': {},
                'overall_accuracy': 0.0,
                'precision_by_intent': {},
                'recall_by_intent': {},
                'f1_by_intent': {}
            }
            
            # Run predictions on all test cases
            for test_case in self.test_cases:
                predicted_intent = self.flow_manager._analyze_user_intent(test_case.user_input)
                results['predictions'].append(predicted_intent)
                results['ground_truth'].append(test_case.expected_intent)
            
            # Calculate overall accuracy
            correct_predictions = sum(
                1 for pred, truth in zip(results['predictions'], results['ground_truth'])
                if pred == truth
            )
            results['overall_accuracy'] = correct_predictions / len(self.test_cases)
            
            # Calculate per-intent metrics
            intent_counts = Counter(results['ground_truth'])
            
            for intent in intent_counts:
                # Calculate accuracy for this intent
                intent_indices = [i for i, truth in enumerate(results['ground_truth']) if truth == intent]
                intent_correct = sum(
                    1 for i in intent_indices 
                    if results['predictions'][i] == intent
                )
                results['accuracy_by_intent'][intent] = intent_correct / len(intent_indices)
                
                # Calculate precision and recall
                predicted_as_intent = [i for i, pred in enumerate(results['predictions']) if pred == intent]
                
                if predicted_as_intent:
                    precision = sum(
                        1 for i in predicted_as_intent 
                        if results['ground_truth'][i] == intent
                    ) / len(predicted_as_intent)
                    results['precision_by_intent'][intent] = precision
                else:
                    results['precision_by_intent'][intent] = 0.0
                
                results['recall_by_intent'][intent] = intent_correct / len(intent_indices)
                
                # Calculate F1 score
                p = results['precision_by_intent'][intent]
                r = results['recall_by_intent'][intent]
                if p + r > 0:
                    results['f1_by_intent'][intent] = 2 * p * r / (p + r)
                else:
                    results['f1_by_intent'][intent] = 0.0
            
            return results
            
        except Exception as e:
            raise IntentRecognitionError(f"Failed to evaluate intent recognition: {e}")
    
    def _load_intent_test_cases(self) -> List[IntentTestCase]:
        """Load ground truth intent test cases"""
        return [
            # Help Intent
            IntentTestCase("I need help with my essay", "help", category="help"),
            IntentTestCase("Can you assist me?", "help", category="help"),
            IntentTestCase("Guide me through this", "help", category="help"),
            IntentTestCase("What should I do?", "help", category="help"),
            IntentTestCase("I'm stuck", "help", category="help"),
            
            # Brainstorm Intent
            IntentTestCase("Help me brainstorm ideas", "brainstorm", category="brainstorm"),
            IntentTestCase("I need story ideas", "brainstorm", category="brainstorm"),
            IntentTestCase("Let me think of topics", "brainstorm", category="brainstorm"),
            IntentTestCase("Generate ideas for my essay", "brainstorm", category="brainstorm"),
            IntentTestCase("What stories should I use?", "brainstorm", category="brainstorm"),
            
            # Outline Intent
            IntentTestCase("Create an outline", "outline", category="outline"),
            IntentTestCase("Help me structure my essay", "outline", category="outline"),
            IntentTestCase("Organize my thoughts", "outline", category="outline"),
            IntentTestCase("Plan my essay structure", "outline", category="outline"),
            IntentTestCase("Make an outline for me", "outline", category="outline"),
            
            # Write Intent
            IntentTestCase("Write a draft", "write", category="write"),
            IntentTestCase("Create my essay", "write", category="write"),
            IntentTestCase("Draft my introduction", "write", category="write"),
            IntentTestCase("Generate a draft", "write", category="write"),
            IntentTestCase("Create the essay content", "write", category="write"),
            
            # Revise Intent
            IntentTestCase("Revise my essay", "revise", category="revise"),
            IntentTestCase("Make this better", "revise", category="revise"),
            IntentTestCase("Improve my writing", "revise", category="revise"),
            IntentTestCase("Enhance my essay", "revise", category="revise"),
            IntentTestCase("Make it stronger", "revise", category="revise"),
            
            # Polish Intent
            IntentTestCase("Polish my essay", "polish", category="polish"),
            IntentTestCase("Final review", "polish", category="polish"),
            IntentTestCase("Finish my essay", "polish", category="polish"),
            IntentTestCase("Final touches", "polish", category="polish"),
            IntentTestCase("Finalize my essay", "polish", category="polish"),
            
            # Review Intent
            IntentTestCase("Check my essay", "review", category="review"),
            IntentTestCase("Look at this", "review", category="review"),
            IntentTestCase("Review my work", "review", category="review"),
            IntentTestCase("Evaluate my essay", "review", category="review"),
            IntentTestCase("Assess my writing", "review", category="review"),
            
            # General Intent
            IntentTestCase("Tell me about essays", "general", category="general"),
            IntentTestCase("What is a good essay?", "general", category="general"),
            IntentTestCase("Explain the process", "general", category="general"),
            IntentTestCase("How does this work?", "general", category="general"),
            IntentTestCase("What are the requirements?", "general", category="general"),
        ]
    
    def generate_intent_report(self) -> Dict[str, Any]:
        """Generate comprehensive intent recognition report"""
        results = self.evaluate_intent_accuracy()
        
        # Calculate summary statistics
        avg_precision = statistics.mean(results['precision_by_intent'].values())
        avg_recall = statistics.mean(results['recall_by_intent'].values())
        avg_f1 = statistics.mean(results['f1_by_intent'].values())
        
        return {
            'overall_accuracy': results['overall_accuracy'],
            'average_precision': avg_precision,
            'average_recall': avg_recall,
            'average_f1': avg_f1,
            'accuracy_by_intent': results['accuracy_by_intent'],
            'precision_by_intent': results['precision_by_intent'],
            'recall_by_intent': results['recall_by_intent'],
            'f1_by_intent': results['f1_by_intent'],
            'total_test_cases': len(self.test_cases),
            'intents_tested': list(results['accuracy_by_intent'].keys())
        }


class ContextTrackingEvaluator:
    """Evaluates context tracking across multi-turn conversations"""
    
    def __init__(self, user_profile: UserProfile):
        self.user_profile = user_profile
        self.scenarios = self._load_context_scenarios()
    
    def evaluate_context_tracking(self) -> Dict[str, float]:
        """Evaluate context tracking across conversation scenarios"""
        try:
            results = {
                'scenario_success_rates': {},
                'overall_success_rate': 0.0,
                'context_preservation_rate': 0.0,
                'long_conversation_success': 0.0,
                'preference_learning_accuracy': 0.0
            }
            
            successful_scenarios = 0
            total_scenarios = len(self.scenarios)
            
            for scenario in self.scenarios:
                success_rate = self._evaluate_scenario(scenario)
                results['scenario_success_rates'][scenario.scenario_name] = success_rate
                
                if success_rate >= scenario.success_criteria.get('context_preservation', 0.8):
                    successful_scenarios += 1
            
            results['overall_success_rate'] = successful_scenarios / total_scenarios
            
            # Calculate specific metrics
            results['context_preservation_rate'] = self._calculate_context_preservation_rate()
            results['long_conversation_success'] = self._calculate_long_conversation_success()
            results['preference_learning_accuracy'] = self._calculate_preference_learning_accuracy()
            
            return results
            
        except Exception as e:
            raise ContextTrackingError(f"Failed to evaluate context tracking: {e}")
    
    def _evaluate_scenario(self, scenario: ConversationScenario) -> float:
        """Evaluate a single conversation scenario"""
        try:
            # Create fresh conversation manager for each scenario
            conversation_manager = ConversationManager(
                user_id=f"test_{scenario.scenario_name.replace(' ', '_').lower()}", 
                profile=self.user_profile
            )
            
            # Execute conversation turns
            for user_input, expected_response_type in scenario.turns:
                response = conversation_manager.handle_message(user_input)
                
                # Validate response type if specified
                if expected_response_type == "clarification":
                    if "🤔" not in response and "could you" not in response.lower():
                        debug_print(True, f"Expected clarification but got: {response[:100]}...")
                
                elif expected_response_type == "tool_execution":
                    if not conversation_manager.state.history[-1].tool_results:
                        debug_print(True, f"Expected tool execution but got: {response[:100]}...")
            
            # Validate final context
            final_context = conversation_manager.state.current_essay_context
            success_score = self._validate_context(final_context, scenario.expected_context)
            
            return success_score
            
        except Exception as e:
            debug_print(True, f"Error evaluating scenario {scenario.scenario_name}: {e}")
            return 0.0
    
    def _validate_context(self, actual_context: Optional[EssayContext], expected_context: Dict[str, Any]) -> float:
        """Validate context against expected values"""
        if not actual_context:
            return 0.0
        
        matches = 0
        total_checks = len(expected_context)
        
        for key, expected_value in expected_context.items():
            if key == "essay_type":
                actual_value = actual_context.essay_type
            elif key == "college_target":
                actual_value = actual_context.college_target
            elif key == "progress_stage":
                actual_value = actual_context.progress_stage
            else:
                continue
            
            if actual_value and expected_value.lower() in actual_value.lower():
                matches += 1
        
        return matches / total_checks if total_checks > 0 else 0.0
    
    def _calculate_context_preservation_rate(self) -> float:
        """Calculate how well context is preserved across turns"""
        preservation_scores = []
        
        for scenario in self.scenarios:
            if len(scenario.turns) >= 5:  # Only test multi-turn scenarios
                try:
                    conversation_manager = ConversationManager(
                        user_id=f"preservation_test_{scenario.scenario_name.replace(' ', '_').lower()}", 
                        profile=self.user_profile
                    )
                    
                    contexts = []
                    for user_input, _ in scenario.turns:
                        conversation_manager.handle_message(user_input)
                        if conversation_manager.state.current_essay_context:
                            contexts.append(conversation_manager.state.current_essay_context)
                    
                    # Check context consistency
                    if len(contexts) >= 2:
                        consistency_score = self._calculate_context_consistency(contexts)
                        preservation_scores.append(consistency_score)
                
                except Exception as e:
                    debug_print(True, f"Error calculating preservation for {scenario.scenario_name}: {e}")
                    preservation_scores.append(0.0)
        
        return statistics.mean(preservation_scores) if preservation_scores else 0.0
    
    def _calculate_context_consistency(self, contexts: List[EssayContext]) -> float:
        """Calculate consistency of context across turns"""
        consistency_scores = []
        
        for i in range(1, len(contexts)):
            prev_context = contexts[i-1]
            curr_context = contexts[i]
            
            # Check if key fields remain consistent
            consistency = 0.0
            checks = 0
            
            if prev_context.essay_type and curr_context.essay_type:
                consistency += 1.0 if prev_context.essay_type == curr_context.essay_type else 0.0
                checks += 1
            
            if prev_context.college_target and curr_context.college_target:
                consistency += 1.0 if prev_context.college_target == curr_context.college_target else 0.0
                checks += 1
            
            if checks > 0:
                consistency_scores.append(consistency / checks)
        
        return statistics.mean(consistency_scores) if consistency_scores else 0.0
    
    def _calculate_long_conversation_success(self) -> float:
        """Calculate success rate for conversations with 10+ turns"""
        long_scenarios = [s for s in self.scenarios if len(s.turns) >= 10]
        
        if not long_scenarios:
            return 1.0  # No long conversations to test
        
        successful_long = 0
        
        for scenario in long_scenarios:
            success_rate = self._evaluate_scenario(scenario)
            if success_rate >= 0.9:  # High threshold for long conversations
                successful_long += 1
        
        return successful_long / len(long_scenarios)
    
    def _calculate_preference_learning_accuracy(self) -> float:
        """Calculate accuracy of preference learning"""
        # This is a simplified version - in a real implementation, 
        # you'd test specific preference learning scenarios
        return 0.8  # Placeholder - implement based on specific preference tests
    
    def _load_context_scenarios(self) -> List[ConversationScenario]:
        """Load context tracking test scenarios"""
        return [
            ConversationScenario(
                scenario_name="Essay Type and College Context",
                turns=[
                    ("I need help with my essay", "clarification"),
                    ("It's a personal statement", "context_update"),
                    ("For Stanford", "context_update"),
                    ("Help me brainstorm", "tool_execution"),
                ],
                expected_context={
                    "essay_type": "personal statement",
                    "college_target": "Stanford",
                    "progress_stage": "planning"
                },
                success_criteria={"context_preservation": 1.0},
                description="Tests basic context establishment and preservation"
            ),
            
            ConversationScenario(
                scenario_name="Multi-Turn Context Evolution",
                turns=[
                    ("I'm working on my leadership essay", "context_update"),
                    ("It's for MIT", "context_update"),
                    ("Help me brainstorm ideas", "tool_execution"),
                    ("I want to use my debate team story", "preference_update"),
                    ("Create an outline with that story", "tool_execution"),
                    ("Make it more compelling", "tool_execution"),
                    ("Write the introduction", "tool_execution"),
                ],
                expected_context={
                    "essay_type": "leadership",
                    "college_target": "MIT",
                    "progress_stage": "drafting"
                },
                success_criteria={"context_preservation": 0.95},
                description="Tests context evolution through multiple phases"
            ),
            
            ConversationScenario(
                scenario_name="10+ Turn Context Persistence",
                turns=[
                    ("I'm working on my challenge essay", "context_update"),
                    ("It's for Harvard", "context_update"),
                    ("Help me brainstorm ideas", "tool_execution"),
                    ("I like the coding challenge story", "preference_update"),
                    ("Create an outline with that story", "tool_execution"),
                    ("Make it more structured", "tool_execution"),
                    ("Write the introduction", "tool_execution"),
                    ("Revise to be more compelling", "tool_execution"),
                    ("Add more personal reflection", "tool_execution"),
                    ("Polish the language", "tool_execution"),
                    ("Check the word count", "tool_execution"),
                    ("Is it ready for submission?", "evaluation"),
                ],
                expected_context={
                    "essay_type": "challenge",
                    "college_target": "Harvard",
                    "progress_stage": "polishing"
                },
                success_criteria={"context_preservation": 0.95},
                description="Tests context preservation across long conversations"
            ),
            
            ConversationScenario(
                scenario_name="Context Recovery After Clarification",
                turns=[
                    ("Help me with my essay", "clarification"),
                    ("It's about my community service", "context_update"),
                    ("For Yale", "context_update"),
                    ("Help me", "clarification"),
                    ("Create an outline", "tool_execution"),
                    ("Write a draft", "tool_execution"),
                ],
                expected_context={
                    "essay_type": "community",
                    "college_target": "Yale",
                    "progress_stage": "drafting"
                },
                success_criteria={"context_preservation": 0.90},
                description="Tests context recovery after clarification requests"
            ),
            
            ConversationScenario(
                scenario_name="Progressive Context Building",
                turns=[
                    ("I need essay help", "clarification"),
                    ("Personal statement", "context_update"),
                    ("For Princeton", "context_update"),
                    ("About leadership", "context_update"),
                    ("Help me brainstorm", "tool_execution"),
                    ("Create an outline", "tool_execution"),
                    ("Write a draft", "tool_execution"),
                    ("Revise it", "tool_execution"),
                ],
                expected_context={
                    "essay_type": "personal statement",
                    "college_target": "Princeton",
                    "progress_stage": "revising"
                },
                success_criteria={"context_preservation": 0.95},
                description="Tests progressive context building through conversation"
            )
        ]
    
    def generate_context_report(self) -> Dict[str, Any]:
        """Generate comprehensive context tracking report"""
        results = self.evaluate_context_tracking()
        
        return {
            'overall_success_rate': results['overall_success_rate'],
            'context_preservation_rate': results['context_preservation_rate'],
            'long_conversation_success': results['long_conversation_success'],
            'preference_learning_accuracy': results['preference_learning_accuracy'],
            'scenario_results': results['scenario_success_rates'],
            'total_scenarios': len(self.scenarios),
            'scenarios_tested': [s.scenario_name for s in self.scenarios]
        }


class ConversationTestRunner:
    """Orchestrates comprehensive conversation evaluation"""
    
    def __init__(self, user_profile: UserProfile):
        self.user_profile = user_profile
        self.quality_evaluator = ConversationQualityEvaluator()
        self.intent_evaluator = IntentRecognitionEvaluator(ConversationFlowManager())
        self.context_evaluator = ContextTrackingEvaluator(user_profile)
    
    def run_comprehensive_evaluation(self) -> ConversationEvaluationReport:
        """Run comprehensive conversation evaluation"""
        start_time = time.time()
        
        try:
            # Run quality evaluation
            quality_metrics = self.run_quality_evaluation()
            
            # Run intent recognition evaluation
            intent_results = self.run_intent_evaluation()
            
            # Run context tracking evaluation
            context_results = self.run_context_evaluation()
            
            # Run integration tests
            integration_results = self.run_integration_tests()
            
            # Calculate overall score
            overall_score = self._calculate_overall_score(
                quality_metrics, intent_results, context_results, integration_results
            )
            
            # Generate recommendations
            recommendations = self._generate_recommendations(
                quality_metrics, intent_results, context_results, integration_results
            )
            
            execution_time = time.time() - start_time
            
            return ConversationEvaluationReport(
                quality_metrics=quality_metrics,
                intent_recognition_accuracy=intent_results['overall_accuracy'],
                context_tracking_success=context_results['overall_success_rate'],
                integration_test_results=integration_results,
                overall_score=overall_score,
                recommendations=recommendations,
                execution_time=execution_time,
                test_timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
            )
            
        except Exception as e:
            raise ConversationEvaluationError(f"Failed to run comprehensive evaluation: {e}")
    
    def run_quality_evaluation(self) -> ConversationQualityMetrics:
        """Run conversation quality evaluation"""
        # Create test conversation
        conversation_manager = ConversationManager(user_id="quality_test_user", profile=self.user_profile)
        
        # Execute sample conversation
        test_inputs = [
            "I need help with my essay",
            "It's a personal statement for Stanford",
            "Help me brainstorm ideas",
            "Create an outline using my leadership story",
            "Write a draft of the introduction"
        ]
        
        for user_input in test_inputs:
            conversation_manager.handle_message(user_input)
        
        return self.quality_evaluator.evaluate_conversation_quality(conversation_manager.state)
    
    def run_intent_evaluation(self) -> Dict[str, float]:
        """Run intent recognition evaluation"""
        return self.intent_evaluator.evaluate_intent_accuracy()
    
    def run_context_evaluation(self) -> Dict[str, float]:
        """Run context tracking evaluation"""
        return self.context_evaluator.evaluate_context_tracking()
    
    def run_integration_tests(self) -> Dict[str, bool]:
        """Run integration tests with existing workflow"""
        integration_results = {}
        
        try:
            # Test conversation with essay workflow
            conversation_manager = ConversationManager(user_id="integration_test_user", profile=self.user_profile)
            
            # Test basic workflow integration
            response = conversation_manager.handle_message("Help me write a Stanford personal statement")
            integration_results['basic_workflow'] = len(response) > 0
            
            # Test tool execution integration
            response = conversation_manager.handle_message("Help me brainstorm ideas")
            last_turn = conversation_manager.state.history[-1]
            integration_results['tool_execution'] = len(last_turn.tool_results) > 0
            
            # Test context persistence
            response = conversation_manager.handle_message("Create an outline")
            integration_results['context_persistence'] = (
                conversation_manager.state.current_essay_context is not None
            )
            
            # Test conversation flow
            response = conversation_manager.handle_message("Write a draft")
            integration_results['conversation_flow'] = len(response) > 0
            
        except Exception as e:
            debug_print(True, f"Integration test error: {e}")
            integration_results = {
                'basic_workflow': False,
                'tool_execution': False,
                'context_persistence': False,
                'conversation_flow': False
            }
        
        return integration_results
    
    def _calculate_overall_score(self, quality_metrics: ConversationQualityMetrics, 
                                intent_results: Dict[str, float], 
                                context_results: Dict[str, float],
                                integration_results: Dict[str, bool]) -> float:
        """Calculate overall conversation evaluation score"""
        weights = {
            'quality': 0.35,
            'intent': 0.25,
            'context': 0.25,
            'integration': 0.15
        }
        
        quality_score = quality_metrics.overall_quality
        intent_score = intent_results['overall_accuracy']
        context_score = context_results['overall_success_rate']
        integration_score = sum(integration_results.values()) / len(integration_results)
        
        overall_score = (
            (quality_score * weights['quality']) +
            (intent_score * weights['intent']) +
            (context_score * weights['context']) +
            (integration_score * weights['integration'])
        )
        
        return overall_score
    
    def _generate_recommendations(self, quality_metrics: ConversationQualityMetrics,
                                 intent_results: Dict[str, float],
                                 context_results: Dict[str, float],
                                 integration_results: Dict[str, bool]) -> List[str]:
        """Generate improvement recommendations"""
        recommendations = []
        
        # Quality recommendations
        if quality_metrics.relevance_score < 0.7:
            recommendations.append("Improve response relevance by better matching user intent")
        
        if quality_metrics.helpfulness_score < 0.8:
            recommendations.append("Enhance helpfulness by increasing tool execution success rate")
        
        if quality_metrics.coherence_score < 0.7:
            recommendations.append("Improve conversation coherence by better topic tracking")
        
        # Intent recommendations
        if intent_results['overall_accuracy'] < 0.9:
            recommendations.append("Improve intent recognition accuracy with better training data")
        
        # Context recommendations
        if context_results['context_preservation_rate'] < 0.9:
            recommendations.append("Enhance context preservation across conversation turns")
        
        if context_results['long_conversation_success'] < 0.9:
            recommendations.append("Improve handling of long conversations (10+ turns)")
        
        # Integration recommendations
        if not all(integration_results.values()):
            failed_tests = [k for k, v in integration_results.items() if not v]
            recommendations.append(f"Fix integration issues: {', '.join(failed_tests)}")
        
        return recommendations if recommendations else ["Conversation system performing well - no major improvements needed"]


# Export main classes
__all__ = [
    'ConversationQualityEvaluator',
    'IntentRecognitionEvaluator', 
    'ContextTrackingEvaluator',
    'ConversationTestRunner',
    'ConversationEvaluationReport',
    'ConversationQualityMetrics',
    'IntentTestCase',
    'ConversationScenario',
    'ConversationEvaluationError',
    'IntentRecognitionError',
    'ContextTrackingError',
    'QualityMetricsError'
] 