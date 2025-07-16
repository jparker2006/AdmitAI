"""Performance-based prompt optimization and selection.

This module provides sophisticated prompt optimization capabilities that track
performance metrics, manage prompt variants, and continuously improve prompt
selection based on success patterns and user outcomes.
"""
from typing import Dict, List, Any, Optional, Tuple, Set
import logging
import asyncio
import json
import time
import random
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


@dataclass
class PromptPerformanceMetrics:
    """Performance metrics for a specific prompt."""
    prompt_id: str
    total_uses: int = 0
    successful_uses: int = 0
    average_response_time: float = 0.0
    average_confidence: float = 0.0
    user_satisfaction_scores: List[float] = None
    error_rate: float = 0.0
    last_used: Optional[datetime] = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.user_satisfaction_scores is None:
            self.user_satisfaction_scores = []
        if self.created_at is None:
            self.created_at = datetime.now()
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.total_uses == 0:
            return 0.0
        return self.successful_uses / self.total_uses
    
    @property
    def average_satisfaction(self) -> float:
        """Calculate average user satisfaction."""
        if not self.user_satisfaction_scores:
            return 0.0
        return sum(self.user_satisfaction_scores) / len(self.user_satisfaction_scores)
    
    @property
    def performance_score(self) -> float:
        """Calculate overall performance score (0-1)."""
        # Weighted combination of metrics
        weights = {
            'success_rate': 0.4,
            'satisfaction': 0.3,
            'response_time': 0.2,
            'confidence': 0.1
        }
        
        # Normalize response time (lower is better, cap at 10 seconds)
        normalized_time = max(0, 1 - (self.average_response_time / 10.0))
        
        score = (
            weights['success_rate'] * self.success_rate +
            weights['satisfaction'] * (self.average_satisfaction / 5.0) +  # Assume 5-point scale
            weights['response_time'] * normalized_time +
            weights['confidence'] * self.average_confidence
        )
        
        return min(1.0, max(0.0, score))


@dataclass
class PromptVariant:
    """A variant of a base prompt for A/B testing."""
    variant_id: str
    base_prompt_id: str
    template: str
    description: str
    created_at: datetime = None
    is_active: bool = True
    performance: Optional[PromptPerformanceMetrics] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.performance is None:
            self.performance = PromptPerformanceMetrics(self.variant_id)


class PromptOptimizer:
    """Performance-based prompt optimization and selection.
    
    This class tracks prompt performance, analyzes patterns, and provides
    recommendations for optimal prompt selection based on context and
    historical success patterns.
    """
    
    def __init__(self, memory: Optional[Any] = None):
        """Initialize the prompt optimizer.
        
        Args:
            memory: AgentMemory instance for persistence
        """
        self.memory = memory
        self.performance_metrics: Dict[str, PromptPerformanceMetrics] = {}
        self.context_patterns: Dict[str, Dict[str, float]] = defaultdict(dict)
        self.recent_performances: deque = deque(maxlen=100)  # Last 100 executions
        self.optimization_history: List[Dict] = []
        
        # Load persisted data
        self._load_performance_data()
        
        logger.info("PromptOptimizer initialized with %d tracked prompts", 
                   len(self.performance_metrics))
    
    async def select_optimal_prompt(
        self, 
        task_type: str, 
        context: Dict[str, Any],
        available_prompts: Optional[List[str]] = None
    ) -> Tuple[str, float]:
        """Select the optimal prompt for the given task type and context.
        
        Args:
            task_type: Type of task (e.g., 'reasoning', 'conversation', 'recovery')
            context: Context dictionary for decision making
            available_prompts: Optional list of available prompt IDs
            
        Returns:
            Tuple of (prompt_id, confidence_score)
        """
        try:
            # Get context signature for pattern matching
            context_signature = self._get_context_signature(context)
            
            # Get candidate prompts
            candidates = available_prompts or self._get_default_prompts(task_type)
            
            if not candidates:
                logger.warning("No candidate prompts for task_type: %s", task_type)
                return "default_reasoning", 0.5
            
            # Score each candidate
            scored_candidates = []
            for prompt_id in candidates:
                score = await self._score_prompt_for_context(prompt_id, context_signature, task_type)
                scored_candidates.append((prompt_id, score))
            
            # Select best candidate
            scored_candidates.sort(key=lambda x: x[1], reverse=True)
            best_prompt, best_score = scored_candidates[0]
            
            logger.debug("Selected prompt %s with score %.3f for task %s", 
                        best_prompt, best_score, task_type)
            
            return best_prompt, best_score
            
        except Exception as e:
            logger.error("Error selecting optimal prompt: %s", e)
            return "default_reasoning", 0.3
    
    async def analyze_prompt_performance(self, prompt_id: str) -> Dict[str, Any]:
        """Analyze performance of a specific prompt.
        
        Args:
            prompt_id: ID of the prompt to analyze
            
        Returns:
            Dictionary containing performance analysis
        """
        try:
            metrics = self.performance_metrics.get(prompt_id)
            if not metrics:
                return {"error": f"No performance data for prompt {prompt_id}"}
            
            # Recent performance trend
            recent_data = [p for p in self.recent_performances 
                          if p.get('prompt_id') == prompt_id][-20:]  # Last 20 uses
            
            trend_analysis = self._analyze_trend(recent_data)
            
            # Context effectiveness
            context_effectiveness = self._analyze_context_effectiveness(prompt_id)
            
            # Comparison with similar prompts
            comparison = await self._compare_with_similar_prompts(prompt_id)
            
            analysis = {
                "prompt_id": prompt_id,
                "overall_performance": {
                    "score": metrics.performance_score,
                    "success_rate": metrics.success_rate,
                    "total_uses": metrics.total_uses,
                    "average_satisfaction": metrics.average_satisfaction,
                    "response_time": metrics.average_response_time
                },
                "trend_analysis": trend_analysis,
                "context_effectiveness": context_effectiveness,
                "comparison": comparison,
                "recommendations": self._generate_recommendations(metrics, trend_analysis)
            }
            
            logger.debug("Analyzed performance for prompt %s", prompt_id)
            return analysis
            
        except Exception as e:
            logger.error("Error analyzing prompt performance: %s", e)
            return {"error": str(e)}
    
    def update_performance_metrics(
        self, 
        prompt_id: str, 
        success: bool, 
        execution_time: float,
        confidence: float = 0.0,
        user_satisfaction: Optional[float] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """Update performance metrics for a prompt.
        
        Args:
            prompt_id: ID of the prompt
            success: Whether the execution was successful
            execution_time: Time taken for execution in seconds
            confidence: Confidence score (0-1)
            user_satisfaction: User satisfaction score (1-5)
            context: Context dictionary for pattern analysis
        """
        try:
            # Get or create metrics
            if prompt_id not in self.performance_metrics:
                self.performance_metrics[prompt_id] = PromptPerformanceMetrics(prompt_id)
            
            metrics = self.performance_metrics[prompt_id]
            
            # Update metrics
            metrics.total_uses += 1
            if success:
                metrics.successful_uses += 1
            
            # Update running averages
            alpha = 0.1  # Learning rate for exponential moving average
            if metrics.total_uses == 1:
                metrics.average_response_time = execution_time
                metrics.average_confidence = confidence
            else:
                metrics.average_response_time = (
                    (1 - alpha) * metrics.average_response_time + alpha * execution_time
                )
                metrics.average_confidence = (
                    (1 - alpha) * metrics.average_confidence + alpha * confidence
                )
            
            # Update satisfaction scores
            if user_satisfaction is not None:
                metrics.user_satisfaction_scores.append(user_satisfaction)
                # Keep only recent scores
                if len(metrics.user_satisfaction_scores) > 50:
                    metrics.user_satisfaction_scores = metrics.user_satisfaction_scores[-50:]
            
            # Update error rate
            metrics.error_rate = 1.0 - metrics.success_rate
            metrics.last_used = datetime.now()
            
            # Record for trend analysis
            self.recent_performances.append({
                'prompt_id': prompt_id,
                'success': success,
                'execution_time': execution_time,
                'confidence': confidence,
                'timestamp': datetime.now(),
                'context_signature': self._get_context_signature(context or {})
            })
            
            # Update context patterns
            if context:
                context_signature = self._get_context_signature(context)
                self.context_patterns[prompt_id][context_signature] = metrics.performance_score
            
            # Persist data periodically
            if metrics.total_uses % 10 == 0:  # Every 10 uses
                self._save_performance_data()
            
            logger.debug("Updated metrics for %s: success=%s, time=%.2fs, confidence=%.2f", 
                        prompt_id, success, execution_time, confidence)
            
        except Exception as e:
            logger.error("Error updating performance metrics: %s", e)
    
    async def track_performance(
        self,
        prompt_version: str,
        success: bool,
        response_time: float,
        confidence: float,
        context_size: Optional[int] = None,
        **kwargs
    ) -> None:
        """Track performance for ReAct agent compatibility.
        
        This is an async wrapper around update_performance_metrics that provides
        the interface expected by the ReasoningEngine.
        
        Args:
            prompt_version: Version/ID of the prompt used
            success: Whether the reasoning was successful
            response_time: Time taken for the reasoning operation
            confidence: Confidence score of the result (0-1)
            context_size: Size of context used (optional)
            **kwargs: Additional parameters passed through
        """
        try:
            # Map to existing update_performance_metrics interface
            self.update_performance_metrics(
                prompt_id=prompt_version,
                success=success,
                execution_time=response_time,
                confidence=confidence,
                context=kwargs.get('context', None)
            )
            
            logger.debug("Tracked performance for prompt %s: success=%s, time=%.2fs", 
                        prompt_version, success, response_time)
            
        except Exception as e:
            logger.error("Error tracking performance: %s", e)
    
    def get_performance_recommendations(self) -> Dict[str, Any]:
        """Get recommendations for improving prompt performance.
        
        Returns:
            Dictionary containing performance improvement recommendations
        """
        try:
            recommendations = {
                "timestamp": datetime.now().isoformat(),
                "overall_health": self._assess_overall_health(),
                "underperforming_prompts": self._identify_underperforming_prompts(),
                "optimization_opportunities": self._identify_optimization_opportunities(),
                "suggested_experiments": self._suggest_experiments(),
                "context_insights": self._analyze_context_patterns()
            }
            
            logger.debug("Generated performance recommendations")
            return recommendations
            
        except Exception as e:
            logger.error("Error generating recommendations: %s", e)
            return {"error": str(e)}
    
    async def _score_prompt_for_context(
        self, 
        prompt_id: str, 
        context_signature: str,
        task_type: str
    ) -> float:
        """Score a prompt for the given context and task type.
        
        Args:
            prompt_id: Prompt to score
            context_signature: Context fingerprint
            task_type: Type of task
            
        Returns:
            Score from 0-1
        """
        try:
            # Base performance score
            metrics = self.performance_metrics.get(prompt_id)
            if not metrics:
                return 0.5  # Default score for unknown prompts
            
            base_score = metrics.performance_score
            
            # Context-specific adjustment
            context_scores = self.context_patterns.get(prompt_id, {})
            context_score = context_scores.get(context_signature, base_score)
            
            # Task type adjustment (simple heuristic)
            task_adjustment = self._get_task_type_adjustment(prompt_id, task_type)
            
            # Recency adjustment (favor recently successful prompts)
            recency_adjustment = self._get_recency_adjustment(prompt_id)
            
            # Combine scores
            final_score = (
                0.5 * base_score +
                0.3 * context_score +
                0.1 * task_adjustment +
                0.1 * recency_adjustment
            )
            
            return min(1.0, max(0.0, final_score))
            
        except Exception as e:
            logger.error("Error scoring prompt %s: %s", prompt_id, e)
            return 0.3
    
    def _get_context_signature(self, context: Dict[str, Any]) -> str:
        """Generate a signature for context pattern matching.
        
        Args:
            context: Context dictionary
            
        Returns:
            Context signature string
        """
        try:
            # Extract key contextual features
            features = []
            
            if context.get('user_experience'):
                features.append(f"exp:{context['user_experience']}")
            
            if context.get('essay_phase'):
                features.append(f"phase:{context['essay_phase']}")
            
            if context.get('conversation_length'):
                length_bucket = min(5, context['conversation_length'] // 5)  # Bucket by 5s
                features.append(f"conv:{length_bucket}")
            
            if context.get('has_errors'):
                features.append("errors:true")
            
            if context.get('user_mood'):
                features.append(f"mood:{context['user_mood']}")
            
            return "|".join(sorted(features)) if features else "default"
            
        except Exception as e:
            logger.error("Error generating context signature: %s", e)
            return "error"
    
    def _get_default_prompts(self, task_type: str) -> List[str]:
        """Get default prompt candidates for a task type."""
        prompt_mapping = {
            'reasoning': ['advanced_reasoning', 'high_confidence_reasoning', 'support_focused'],
            'conversation': ['enhanced_conversation', 'support_focused'],
            'recovery': ['tool_failure_recovery', 'context_missing_recovery'],
            'brainstorming': ['brainstorm_specific', 'exploratory_reasoning'],
            'outlining': ['outline_specific', 'high_confidence_reasoning'],
            'drafting': ['draft_specific', 'support_focused'],
            'revision': ['revise_specific', 'high_confidence_reasoning'],
            'polishing': ['polish_specific', 'high_confidence_reasoning']
        }
        
        return prompt_mapping.get(task_type, ['advanced_reasoning'])
    
    def _get_task_type_adjustment(self, prompt_id: str, task_type: str) -> float:
        """Get task type specific adjustment for prompt scoring."""
        # Simple heuristic based on prompt ID and task type matching
        if task_type.lower() in prompt_id.lower():
            return 1.0
        elif 'support' in prompt_id and task_type in ['conversation', 'recovery']:
            return 0.8
        elif 'confidence' in prompt_id and task_type in ['drafting', 'revision', 'polishing']:
            return 0.8
        else:
            return 0.6
    
    def _get_recency_adjustment(self, prompt_id: str) -> float:
        """Get recency adjustment based on recent performance."""
        recent_data = [p for p in list(self.recent_performances)[-20:] 
                      if p.get('prompt_id') == prompt_id]
        
        if not recent_data:
            return 0.5
        
        # Calculate recent success rate
        recent_successes = sum(1 for p in recent_data if p.get('success'))
        recent_success_rate = recent_successes / len(recent_data)
        
        return recent_success_rate
    
    def _analyze_trend(self, recent_data: List[Dict]) -> Dict[str, Any]:
        """Analyze performance trend from recent data."""
        if len(recent_data) < 5:
            return {"trend": "insufficient_data", "confidence": 0.0}
        
        # Simple trend analysis
        first_half = recent_data[:len(recent_data)//2]
        second_half = recent_data[len(recent_data)//2:]
        
        first_success_rate = sum(1 for p in first_half if p.get('success')) / len(first_half)
        second_success_rate = sum(1 for p in second_half if p.get('success')) / len(second_half)
        
        trend_direction = second_success_rate - first_success_rate
        
        if trend_direction > 0.1:
            trend = "improving"
        elif trend_direction < -0.1:
            trend = "declining"
        else:
            trend = "stable"
        
        return {
            "trend": trend,
            "trend_magnitude": abs(trend_direction),
            "recent_success_rate": second_success_rate,
            "confidence": min(1.0, len(recent_data) / 20.0)
        }
    
    def _analyze_context_effectiveness(self, prompt_id: str) -> Dict[str, Any]:
        """Analyze how effective a prompt is in different contexts."""
        context_patterns = self.context_patterns.get(prompt_id, {})
        
        if not context_patterns:
            return {"analysis": "no_context_data"}
        
        # Find best and worst contexts
        sorted_contexts = sorted(context_patterns.items(), key=lambda x: x[1], reverse=True)
        
        return {
            "best_contexts": sorted_contexts[:3],
            "worst_contexts": sorted_contexts[-3:],
            "context_variance": max(context_patterns.values()) - min(context_patterns.values()),
            "total_contexts": len(context_patterns)
        }
    
    async def _compare_with_similar_prompts(self, prompt_id: str) -> Dict[str, Any]:
        """Compare prompt performance with similar prompts."""
        try:
            current_metrics = self.performance_metrics.get(prompt_id)
            if not current_metrics:
                return {"comparison": "no_data"}
            
            # Find similar prompts (simple heuristic based on name similarity)
            similar_prompts = []
            for other_id, other_metrics in self.performance_metrics.items():
                if other_id != prompt_id and other_metrics.total_uses >= 5:
                    # Simple similarity check
                    similarity = self._calculate_prompt_similarity(prompt_id, other_id)
                    if similarity > 0.3:
                        similar_prompts.append((other_id, other_metrics, similarity))
            
            if not similar_prompts:
                return {"comparison": "no_similar_prompts"}
            
            # Calculate relative performance
            avg_performance = sum(m.performance_score for _, m, _ in similar_prompts) / len(similar_prompts)
            relative_performance = current_metrics.performance_score - avg_performance
            
            return {
                "similar_prompts_count": len(similar_prompts),
                "average_similar_performance": avg_performance,
                "relative_performance": relative_performance,
                "rank": self._calculate_rank(current_metrics.performance_score, 
                                           [m.performance_score for _, m, _ in similar_prompts])
            }
            
        except Exception as e:
            logger.error("Error comparing with similar prompts: %s", e)
            return {"comparison": "error", "error": str(e)}
    
    def _calculate_prompt_similarity(self, prompt1: str, prompt2: str) -> float:
        """Calculate similarity between two prompt IDs."""
        # Simple word-based similarity
        words1 = set(prompt1.lower().split('_'))
        words2 = set(prompt2.lower().split('_'))
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def _calculate_rank(self, score: float, comparison_scores: List[float]) -> int:
        """Calculate rank of score among comparison scores."""
        better_scores = sum(1 for s in comparison_scores if s > score)
        return better_scores + 1
    
    def _generate_recommendations(self, metrics: PromptPerformanceMetrics, trend: Dict) -> List[str]:
        """Generate recommendations based on metrics and trends."""
        recommendations = []
        
        if metrics.performance_score < 0.6:
            recommendations.append("Consider replacing or optimizing this prompt - low overall performance")
        
        if metrics.success_rate < 0.7:
            recommendations.append("Investigate common failure patterns - low success rate")
        
        if metrics.average_response_time > 5.0:
            recommendations.append("Optimize for faster response times - currently too slow")
        
        if trend.get('trend') == 'declining':
            recommendations.append("Performance is declining - investigate recent changes")
        
        if metrics.total_uses < 10:
            recommendations.append("Gather more usage data before making optimization decisions")
        
        if not recommendations:
            recommendations.append("Performance is satisfactory - monitor for changes")
        
        return recommendations
    
    def _assess_overall_health(self) -> Dict[str, Any]:
        """Assess overall health of the prompt system."""
        if not self.performance_metrics:
            return {"status": "no_data", "score": 0.0}
        
        # Calculate aggregate metrics
        total_prompts = len(self.performance_metrics)
        active_prompts = sum(1 for m in self.performance_metrics.values() if m.total_uses > 0)
        avg_performance = sum(m.performance_score for m in self.performance_metrics.values()) / total_prompts
        
        # Health score
        health_score = min(1.0, avg_performance * (active_prompts / total_prompts))
        
        return {
            "status": "healthy" if health_score > 0.7 else "needs_attention" if health_score > 0.5 else "poor",
            "score": health_score,
            "total_prompts": total_prompts,
            "active_prompts": active_prompts,
            "average_performance": avg_performance
        }
    
    def _identify_underperforming_prompts(self) -> List[Dict[str, Any]]:
        """Identify prompts that are underperforming."""
        underperforming = []
        
        for prompt_id, metrics in self.performance_metrics.items():
            if metrics.total_uses >= 5 and metrics.performance_score < 0.6:
                underperforming.append({
                    "prompt_id": prompt_id,
                    "performance_score": metrics.performance_score,
                    "success_rate": metrics.success_rate,
                    "total_uses": metrics.total_uses
                })
        
        return sorted(underperforming, key=lambda x: x['performance_score'])
    
    def _identify_optimization_opportunities(self) -> List[Dict[str, Any]]:
        """Identify opportunities for optimization."""
        opportunities = []
        
        # Look for prompts with high variance in context performance
        for prompt_id, context_patterns in self.context_patterns.items():
            if len(context_patterns) >= 3:
                variance = max(context_patterns.values()) - min(context_patterns.values())
                if variance > 0.3:
                    opportunities.append({
                        "type": "context_specialization",
                        "prompt_id": prompt_id,
                        "variance": variance,
                        "description": f"High context variance - consider context-specific variants"
                    })
        
        # Look for gaps in task coverage
        task_coverage = defaultdict(list)
        for prompt_id in self.performance_metrics:
            for task in ['reasoning', 'conversation', 'recovery', 'brainstorming']:
                if task in prompt_id:
                    task_coverage[task].append(prompt_id)
        
        for task, prompts in task_coverage.items():
            if len(prompts) < 2:
                opportunities.append({
                    "type": "task_coverage",
                    "task": task,
                    "current_prompts": len(prompts),
                    "description": f"Limited prompt options for {task} tasks"
                })
        
        return opportunities
    
    def _suggest_experiments(self) -> List[Dict[str, Any]]:
        """Suggest A/B testing experiments."""
        experiments = []
        
        # Find high-performing prompts that could be templates for new variants
        high_performers = [
            (prompt_id, metrics) for prompt_id, metrics in self.performance_metrics.items()
            if metrics.performance_score > 0.8 and metrics.total_uses >= 10
        ]
        
        for prompt_id, metrics in high_performers[:3]:  # Top 3
            experiments.append({
                "type": "variant_creation",
                "base_prompt": prompt_id,
                "performance_score": metrics.performance_score,
                "suggestion": f"Create variants of {prompt_id} to explore optimization potential"
            })
        
        return experiments
    
    def _analyze_context_patterns(self) -> Dict[str, Any]:
        """Analyze patterns across contexts."""
        context_frequency = defaultdict(int)
        context_performance = defaultdict(list)
        
        for prompt_patterns in self.context_patterns.values():
            for context, performance in prompt_patterns.items():
                context_frequency[context] += 1
                context_performance[context].append(performance)
        
        # Find best and worst performing contexts
        context_avg_performance = {
            context: sum(scores) / len(scores)
            for context, scores in context_performance.items()
            if len(scores) >= 3
        }
        
        if not context_avg_performance:
            return {"analysis": "insufficient_context_data"}
        
        sorted_contexts = sorted(context_avg_performance.items(), key=lambda x: x[1], reverse=True)
        
        return {
            "total_contexts": len(context_frequency),
            "best_contexts": sorted_contexts[:3],
            "worst_contexts": sorted_contexts[-3:],
            "most_common_contexts": sorted(context_frequency.items(), key=lambda x: x[1], reverse=True)[:5]
        }
    
    def _load_performance_data(self):
        """Load performance data from persistent storage."""
        try:
            if self.memory and hasattr(self.memory, 'load_prompt_performance'):
                data = self.memory.load_prompt_performance()
                if data:
                    self.performance_metrics = {
                        k: PromptPerformanceMetrics(**v) if isinstance(v, dict) else v
                        for k, v in data.get('metrics', {}).items()
                    }
                    self.context_patterns = data.get('context_patterns', {})
                    self.optimization_history = data.get('optimization_history', [])
                    logger.info("Loaded performance data for %d prompts", len(self.performance_metrics))
        except Exception as e:
            logger.warning("Could not load performance data: %s", e)
    
    def _save_performance_data(self):
        """Save performance data to persistent storage."""
        try:
            if self.memory and hasattr(self.memory, 'save_prompt_performance'):
                data = {
                    'metrics': {k: asdict(v) for k, v in self.performance_metrics.items()},
                    'context_patterns': dict(self.context_patterns),
                    'optimization_history': self.optimization_history,
                    'last_saved': datetime.now().isoformat()
                }
                self.memory.save_prompt_performance(data)
                logger.debug("Saved performance data")
        except Exception as e:
            logger.warning("Could not save performance data: %s", e)


class PromptVariantManager:
    """Manage and test different prompt variations.
    
    This class handles A/B testing of prompt variants, tracks their performance,
    and provides recommendations for which variants to keep, modify, or remove.
    """
    
    def __init__(self, optimizer: PromptOptimizer):
        """Initialize the variant manager.
        
        Args:
            optimizer: PromptOptimizer instance for performance tracking
        """
        self.optimizer = optimizer
        self.variants: Dict[str, PromptVariant] = {}
        self.base_prompts: Dict[str, List[str]] = defaultdict(list)  # base_id -> variant_ids
        self.active_experiments: Dict[str, Dict[str, Any]] = {}
        
        logger.info("PromptVariantManager initialized")
    
    def register_variant(
        self, 
        base_prompt: str, 
        variant_template: str, 
        description: str,
        variant_id: Optional[str] = None
    ) -> str:
        """Register a new prompt variant for testing.
        
        Args:
            base_prompt: ID of the base prompt
            variant_template: Template string for the variant
            description: Description of the variant
            variant_id: Optional custom variant ID
            
        Returns:
            Generated variant ID
        """
        try:
            # Generate variant ID if not provided
            if not variant_id:
                variant_count = len(self.base_prompts[base_prompt])
                variant_id = f"{base_prompt}_variant_{variant_count + 1}"
            
            # Create variant
            variant = PromptVariant(
                variant_id=variant_id,
                base_prompt_id=base_prompt,
                template=variant_template,
                description=description
            )
            
            # Register variant
            self.variants[variant_id] = variant
            self.base_prompts[base_prompt].append(variant_id)
            
            logger.info("Registered variant %s for base prompt %s", variant_id, base_prompt)
            return variant_id
            
        except Exception as e:
            logger.error("Error registering variant: %s", e)
            raise
    
    async def a_b_test_variants(
        self, 
        base_prompt: str, 
        context: Dict[str, Any],
        test_duration_days: int = 7
    ) -> str:
        """Run A/B test for variants of a base prompt.
        
        Args:
            base_prompt: Base prompt ID to test variants for
            context: Context for the current request
            test_duration_days: Duration of the test in days
            
        Returns:
            Selected variant ID for this request
        """
        try:
            # Get active variants for base prompt
            variant_ids = self.base_prompts.get(base_prompt, [])
            active_variants = [
                vid for vid in variant_ids 
                if self.variants[vid].is_active
            ]
            
            if not active_variants:
                logger.debug("No active variants for %s, using base prompt", base_prompt)
                return base_prompt
            
            # Check if we have an active experiment
            experiment_key = f"{base_prompt}_{self.optimizer._get_context_signature(context)}"
            
            if experiment_key not in self.active_experiments:
                # Start new experiment
                self.active_experiments[experiment_key] = {
                    'start_date': datetime.now(),
                    'end_date': datetime.now() + timedelta(days=test_duration_days),
                    'variants': active_variants + [base_prompt],
                    'allocation': {vid: 0 for vid in active_variants + [base_prompt]},
                    'results': {vid: {'uses': 0, 'successes': 0} for vid in active_variants + [base_prompt]}
                }
            
            experiment = self.active_experiments[experiment_key]
            
            # Check if experiment is still active
            if datetime.now() > experiment['end_date']:
                winner = self._analyze_experiment_results(experiment)
                logger.info("Experiment completed for %s, winner: %s", base_prompt, winner)
                del self.active_experiments[experiment_key]
                return winner
            
            # Select variant using traffic allocation
            selected_variant = self._select_variant_for_test(experiment)
            experiment['allocation'][selected_variant] += 1
            
            logger.debug("A/B test selected variant %s for %s", selected_variant, base_prompt)
            return selected_variant
            
        except Exception as e:
            logger.error("Error in A/B test: %s", e)
            return base_prompt
    
    def get_winning_variant(self, base_prompt: str) -> Optional[str]:
        """Get the current winning variant for a base prompt.
        
        Args:
            base_prompt: Base prompt ID
            
        Returns:
            Winning variant ID or None if no clear winner
        """
        try:
            variant_ids = self.base_prompts.get(base_prompt, [])
            if not variant_ids:
                return None
            
            # Get performance metrics for all variants
            variant_performances = []
            for variant_id in variant_ids:
                if variant_id in self.optimizer.performance_metrics:
                    metrics = self.optimizer.performance_metrics[variant_id]
                    if metrics.total_uses >= 5:  # Minimum usage threshold
                        variant_performances.append((variant_id, metrics.performance_score))
            
            if not variant_performances:
                return None
            
            # Return best performing variant
            variant_performances.sort(key=lambda x: x[1], reverse=True)
            winner, best_score = variant_performances[0]
            
            # Check if winner is significantly better than base
            base_metrics = self.optimizer.performance_metrics.get(base_prompt)
            if base_metrics and base_metrics.total_uses >= 5:
                if best_score > base_metrics.performance_score + 0.05:  # 5% improvement threshold
                    return winner
            
            return None
            
        except Exception as e:
            logger.error("Error getting winning variant: %s", e)
            return None
    
    def archive_underperforming_variants(self, threshold: float = 0.5):
        """Archive variants that are underperforming.
        
        Args:
            threshold: Performance score threshold below which variants are archived
        """
        try:
            archived_count = 0
            
            for variant_id, variant in self.variants.items():
                if not variant.is_active:
                    continue
                
                # Check if variant has enough data
                if variant_id in self.optimizer.performance_metrics:
                    metrics = self.optimizer.performance_metrics[variant_id]
                    
                    if metrics.total_uses >= 10 and metrics.performance_score < threshold:
                        variant.is_active = False
                        archived_count += 1
                        logger.info("Archived underperforming variant %s (score: %.3f)", 
                                   variant_id, metrics.performance_score)
            
            logger.info("Archived %d underperforming variants", archived_count)
            
        except Exception as e:
            logger.error("Error archiving variants: %s", e)
    
    def get_variant_analysis(self, base_prompt: str) -> Dict[str, Any]:
        """Get analysis of all variants for a base prompt.
        
        Args:
            base_prompt: Base prompt ID
            
        Returns:
            Analysis dictionary
        """
        try:
            variant_ids = self.base_prompts.get(base_prompt, [])
            
            analysis = {
                "base_prompt": base_prompt,
                "total_variants": len(variant_ids),
                "active_variants": sum(1 for vid in variant_ids if self.variants[vid].is_active),
                "variants": []
            }
            
            for variant_id in variant_ids:
                variant = self.variants[variant_id]
                metrics = self.optimizer.performance_metrics.get(variant_id)
                
                variant_analysis = {
                    "variant_id": variant_id,
                    "description": variant.description,
                    "is_active": variant.is_active,
                    "created_at": variant.created_at.isoformat(),
                    "performance": {
                        "score": metrics.performance_score if metrics else 0.0,
                        "total_uses": metrics.total_uses if metrics else 0,
                        "success_rate": metrics.success_rate if metrics else 0.0
                    } if metrics else None
                }
                
                analysis["variants"].append(variant_analysis)
            
            # Sort by performance
            analysis["variants"].sort(
                key=lambda x: x["performance"]["score"] if x["performance"] else 0.0,
                reverse=True
            )
            
            return analysis
            
        except Exception as e:
            logger.error("Error analyzing variants: %s", e)
            return {"error": str(e)}
    
    def _select_variant_for_test(self, experiment: Dict[str, Any]) -> str:
        """Select a variant for A/B testing based on allocation strategy."""
        variants = experiment['variants']
        allocation = experiment['allocation']
        
        # Simple round-robin allocation for now
        # In production, could use more sophisticated strategies like Thompson sampling
        min_allocated = min(allocation.values())
        candidates = [v for v in variants if allocation[v] == min_allocated]
        
        return random.choice(candidates)
    
    def _analyze_experiment_results(self, experiment: Dict[str, Any]) -> str:
        """Analyze experiment results and determine winner."""
        results = experiment['results']
        
        # Calculate success rates
        success_rates = {}
        for variant_id, data in results.items():
            if data['uses'] > 0:
                success_rates[variant_id] = data['successes'] / data['uses']
            else:
                success_rates[variant_id] = 0.0
        
        # Return variant with highest success rate (simple approach)
        if success_rates:
            return max(success_rates, key=success_rates.get)
        else:
            return experiment['variants'][0]  # Fallback to first variant 