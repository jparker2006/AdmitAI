"""essay_agent.eval.pattern_analyzer

Intelligent pattern analysis system for extracting insights from evaluation results.

This module analyzes conversation evaluation data to identify performance trends,
user behavior patterns, bottlenecks, and generate actionable improvement recommendations.
Provides both automated insights and detailed analytical reports.
"""

import json
import statistics
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict, Counter
import math

from .llm_evaluator import ConversationEvaluation, TurnEvaluation
from .batch_processor import BatchResult, EvaluationTask
from .conversation_runner import ConversationResult, ConversationTurn
from .conversational_scenarios import ConversationScenario, ScenarioCategory
from ..memory.user_profile_schema import UserProfile
from ..utils.logging import debug_print


class PatternType(Enum):
    """Types of patterns that can be identified."""
    PERFORMANCE_TREND = "performance_trend"
    USER_TYPE_PATTERN = "user_type_pattern"
    TOOL_EFFECTIVENESS = "tool_effectiveness"
    FAILURE_MODE = "failure_mode"
    CONVERSATION_FLOW = "conversation_flow"
    AUTONOMY_ADHERENCE = "autonomy_adherence"
    QUALITY_CORRELATION = "quality_correlation"


class TrendDirection(Enum):
    """Direction of performance trends."""
    IMPROVING = "improving"
    DECLINING = "declining"
    STABLE = "stable"
    VOLATILE = "volatile"


@dataclass
class Pattern:
    """Identified pattern in evaluation data."""
    pattern_type: PatternType
    pattern_id: str
    title: str
    description: str
    confidence_score: float  # 0.0 to 1.0
    impact_severity: str  # "low", "medium", "high", "critical"
    
    # Supporting data
    evidence: List[str] = field(default_factory=list)
    affected_scenarios: List[str] = field(default_factory=list)
    related_metrics: Dict[str, float] = field(default_factory=dict)
    
    # Recommendations
    recommendations: List[str] = field(default_factory=list)
    priority_score: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert pattern to dictionary."""
        return {
            'pattern_type': self.pattern_type.value,
            'pattern_id': self.pattern_id,
            'title': self.title,
            'description': self.description,
            'confidence_score': self.confidence_score,
            'impact_severity': self.impact_severity,
            'evidence': self.evidence,
            'affected_scenarios': self.affected_scenarios,
            'related_metrics': self.related_metrics,
            'recommendations': self.recommendations,
            'priority_score': self.priority_score
        }


@dataclass
class PerformanceTrend:
    """Performance trend analysis results."""
    metric_name: str
    trend_direction: TrendDirection
    change_magnitude: float  # Percentage change
    confidence: float
    time_period: str
    
    # Trend data
    data_points: List[Tuple[datetime, float]] = field(default_factory=list)
    trend_line_slope: float = 0.0
    r_squared: float = 0.0
    
    # Insights
    significant_changes: List[str] = field(default_factory=list)
    potential_causes: List[str] = field(default_factory=list)


@dataclass
class BottleneckReport:
    """Performance bottleneck analysis."""
    bottleneck_type: str
    affected_component: str
    severity_score: float  # 0.0 to 1.0
    frequency: int
    average_impact_duration: float
    
    # Analysis
    root_causes: List[str] = field(default_factory=list)
    performance_impact: Dict[str, float] = field(default_factory=dict)
    affected_user_types: List[str] = field(default_factory=list)
    
    # Solutions
    immediate_fixes: List[str] = field(default_factory=list)
    long_term_improvements: List[str] = field(default_factory=list)
    estimated_improvement: float = 0.0


@dataclass
class ImprovementRecommendation:
    """Actionable improvement recommendation."""
    recommendation_id: str
    title: str
    description: str
    category: str  # "performance", "quality", "user_experience", "reliability"
    
    # Implementation details
    implementation_effort: str  # "low", "medium", "high"
    expected_impact: str  # "low", "medium", "high"
    time_to_implement: str  # "hours", "days", "weeks"
    
    # Supporting data
    supporting_patterns: List[str] = field(default_factory=list)
    affected_metrics: List[str] = field(default_factory=list)
    success_indicators: List[str] = field(default_factory=list)
    
    # Prioritization
    priority_score: float = 0.0
    business_value: str = ""


@dataclass
class PatternAnalysis:
    """Complete pattern analysis results."""
    analysis_id: str
    analysis_timestamp: datetime
    data_period: Tuple[datetime, datetime]
    
    # Core analysis
    identified_patterns: List[Pattern]
    performance_trends: List[PerformanceTrend]
    bottleneck_reports: List[BottleneckReport]
    improvement_recommendations: List[ImprovementRecommendation]
    
    # Summary statistics
    total_evaluations_analyzed: int
    unique_scenarios_analyzed: int
    unique_user_types_analyzed: int
    
    # Key insights
    overall_system_health: str  # "excellent", "good", "fair", "poor"
    critical_issues: List[str]
    quick_wins: List[str]
    long_term_priorities: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert analysis to dictionary."""
        return {
            'analysis_id': self.analysis_id,
            'analysis_timestamp': self.analysis_timestamp.isoformat(),
            'data_period': [self.data_period[0].isoformat(), self.data_period[1].isoformat()],
            'identified_patterns': [p.to_dict() for p in self.identified_patterns],
            'performance_trends': [
                {
                    'metric_name': t.metric_name,
                    'trend_direction': t.trend_direction.value,
                    'change_magnitude': t.change_magnitude,
                    'confidence': t.confidence,
                    'significant_changes': t.significant_changes,
                    'potential_causes': t.potential_causes
                }
                for t in self.performance_trends
            ],
            'bottleneck_reports': [
                {
                    'bottleneck_type': b.bottleneck_type,
                    'affected_component': b.affected_component,
                    'severity_score': b.severity_score,
                    'root_causes': b.root_causes,
                    'immediate_fixes': b.immediate_fixes,
                    'long_term_improvements': b.long_term_improvements
                }
                for b in self.bottleneck_reports
            ],
            'improvement_recommendations': [
                {
                    'recommendation_id': r.recommendation_id,
                    'title': r.title,
                    'description': r.description,
                    'category': r.category,
                    'implementation_effort': r.implementation_effort,
                    'expected_impact': r.expected_impact,
                    'priority_score': r.priority_score
                }
                for r in self.improvement_recommendations
            ],
            'summary': {
                'total_evaluations_analyzed': self.total_evaluations_analyzed,
                'unique_scenarios_analyzed': self.unique_scenarios_analyzed,
                'unique_user_types_analyzed': self.unique_user_types_analyzed,
                'overall_system_health': self.overall_system_health,
                'critical_issues': self.critical_issues,
                'quick_wins': self.quick_wins,
                'long_term_priorities': self.long_term_priorities
            }
        }
    
    def save_to_file(self, filepath: str):
        """Save analysis to JSON file."""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)


class PatternAnalyzer:
    """Intelligent pattern analysis for conversation evaluation data."""
    
    def __init__(self, min_confidence_threshold: float = 0.6):
        """
        Initialize pattern analyzer.
        
        Args:
            min_confidence_threshold: Minimum confidence for pattern detection
        """
        self.min_confidence_threshold = min_confidence_threshold
        self.analysis_count = 0
    
    def analyze_conversation_patterns(
        self,
        evaluations: List[ConversationEvaluation],
        batch_results: Optional[List[BatchResult]] = None,
        time_window_days: int = 30
    ) -> PatternAnalysis:
        """
        Perform comprehensive pattern analysis on conversation evaluations.
        
        Args:
            evaluations: List of conversation evaluations
            batch_results: Optional batch results for additional context
            time_window_days: Time window for trend analysis
            
        Returns:
            Complete pattern analysis
        """
        
        analysis_id = f"analysis_{int(datetime.now().timestamp())}"
        debug_print(True, f"Starting pattern analysis: {analysis_id}")
        debug_print(True, f"Analyzing {len(evaluations)} evaluations")
        
        # Determine analysis period
        if evaluations:
            timestamps = [e.evaluation_timestamp for e in evaluations]
            data_period = (min(timestamps), max(timestamps))
        else:
            now = datetime.now()
            data_period = (now - timedelta(days=time_window_days), now)
        
        # Identify patterns
        patterns = self._identify_all_patterns(evaluations, batch_results)
        
        # Analyze performance trends
        trends = self._analyze_performance_trends(evaluations, time_window_days)
        
        # Identify bottlenecks
        bottlenecks = self._identify_performance_bottlenecks(evaluations, batch_results)
        
        # Generate recommendations
        recommendations = self._generate_improvement_recommendations(
            patterns, trends, bottlenecks
        )
        
        # Calculate summary statistics
        summary_stats = self._calculate_summary_statistics(evaluations)
        
        # Assess overall system health
        system_health = self._assess_system_health(patterns, trends, bottlenecks)
        
        # Generate key insights
        critical_issues, quick_wins, long_term_priorities = self._generate_key_insights(
            patterns, recommendations
        )
        
        analysis = PatternAnalysis(
            analysis_id=analysis_id,
            analysis_timestamp=datetime.now(),
            data_period=data_period,
            identified_patterns=patterns,
            performance_trends=trends,
            bottleneck_reports=bottlenecks,
            improvement_recommendations=recommendations,
            total_evaluations_analyzed=len(evaluations),
            unique_scenarios_analyzed=summary_stats['unique_scenarios'],
            unique_user_types_analyzed=summary_stats['unique_user_types'],
            overall_system_health=system_health,
            critical_issues=critical_issues,
            quick_wins=quick_wins,
            long_term_priorities=long_term_priorities
        )
        
        self.analysis_count += 1
        debug_print(True, f"Pattern analysis completed: {len(patterns)} patterns identified")
        
        return analysis
    
    def _identify_all_patterns(
        self,
        evaluations: List[ConversationEvaluation],
        batch_results: Optional[List[BatchResult]]
    ) -> List[Pattern]:
        """Identify all types of patterns in the evaluation data."""
        
        patterns = []
        
        # Performance trend patterns
        patterns.extend(self._identify_performance_patterns(evaluations))
        
        # User type patterns
        patterns.extend(self._identify_user_type_patterns(evaluations))
        
        # Tool effectiveness patterns
        patterns.extend(self._identify_tool_effectiveness_patterns(evaluations))
        
        # Failure mode patterns
        if batch_results:
            patterns.extend(self._identify_failure_patterns(batch_results))
        
        # Conversation flow patterns
        patterns.extend(self._identify_conversation_flow_patterns(evaluations))
        
        # Quality correlation patterns
        patterns.extend(self._identify_quality_correlation_patterns(evaluations))
        
        # Filter by confidence threshold
        high_confidence_patterns = [
            p for p in patterns 
            if p.confidence_score >= self.min_confidence_threshold
        ]
        
        # Prioritize patterns
        self._calculate_pattern_priorities(high_confidence_patterns)
        
        return sorted(high_confidence_patterns, key=lambda p: p.priority_score, reverse=True)
    
    def _identify_performance_patterns(
        self, 
        evaluations: List[ConversationEvaluation]
    ) -> List[Pattern]:
        """Identify performance-related patterns."""
        patterns = []
        
        if len(evaluations) < 5:
            return patterns
        
        # Analyze overall quality scores
        quality_scores = [e.overall_quality_score for e in evaluations]
        avg_quality = statistics.mean(quality_scores)
        quality_std = statistics.stdev(quality_scores) if len(quality_scores) > 1 else 0
        
        # Low quality pattern
        if avg_quality < 0.6:
            patterns.append(Pattern(
                pattern_type=PatternType.PERFORMANCE_TREND,
                pattern_id="low_overall_quality",
                title="Low Overall Quality Scores",
                description=f"Average conversation quality ({avg_quality:.2f}) is below acceptable threshold (0.6)",
                confidence_score=0.9,
                impact_severity="high",
                evidence=[
                    f"Average quality score: {avg_quality:.2f}",
                    f"Standard deviation: {quality_std:.2f}",
                    f"{sum(1 for s in quality_scores if s < 0.5)} conversations below 50% quality"
                ],
                related_metrics={"average_quality": avg_quality, "quality_std": quality_std},
                recommendations=[
                    "Review conversation prompt templates for clarity",
                    "Improve agent response quality guidelines",
                    "Implement additional quality checkpoints"
                ]
            ))
        
        # High variability pattern
        if quality_std > 0.3:
            patterns.append(Pattern(
                pattern_type=PatternType.PERFORMANCE_TREND,
                pattern_id="high_quality_variability",
                title="Inconsistent Quality Performance",
                description=f"Quality scores show high variability (std: {quality_std:.2f})",
                confidence_score=0.8,
                impact_severity="medium",
                evidence=[
                    f"Quality standard deviation: {quality_std:.2f}",
                    f"Quality range: {min(quality_scores):.2f} - {max(quality_scores):.2f}"
                ],
                related_metrics={"quality_variability": quality_std},
                recommendations=[
                    "Standardize agent response patterns",
                    "Implement consistent evaluation criteria",
                    "Review edge cases causing quality drops"
                ]
            ))
        
        return patterns
    
    def _identify_user_type_patterns(
        self, 
        evaluations: List[ConversationEvaluation]
    ) -> List[Pattern]:
        """Identify patterns related to different user types."""
        patterns = []
        
        # This would require user profile information linked to evaluations
        # For now, return placeholder pattern analysis
        
        # Example: If we had user type data, we could identify:
        # - Which user types have lower satisfaction
        # - Which autonomy levels work best
        # - User experience level correlation with quality
        
        return patterns
    
    def _identify_tool_effectiveness_patterns(
        self, 
        evaluations: List[ConversationEvaluation]
    ) -> List[Pattern]:
        """Identify patterns in tool usage effectiveness."""
        patterns = []
        
        # Analyze tool usage appropriateness scores
        tool_scores = [e.tool_usage_appropriateness for e in evaluations]
        avg_tool_score = statistics.mean(tool_scores)
        
        if avg_tool_score < 0.7:
            patterns.append(Pattern(
                pattern_type=PatternType.TOOL_EFFECTIVENESS,
                pattern_id="poor_tool_selection",
                title="Suboptimal Tool Selection",
                description=f"Tool usage appropriateness ({avg_tool_score:.2f}) indicates poor tool selection",
                confidence_score=0.8,
                impact_severity="medium",
                evidence=[
                    f"Average tool appropriateness: {avg_tool_score:.2f}",
                    f"{sum(1 for s in tool_scores if s < 0.5)} evaluations with poor tool usage"
                ],
                related_metrics={"tool_appropriateness": avg_tool_score},
                recommendations=[
                    "Review tool selection algorithms",
                    "Improve context-awareness in tool selection",
                    "Add tool usage guidelines for specific scenarios"
                ]
            ))
        
        return patterns
    
    def _identify_failure_patterns(
        self, 
        batch_results: List[BatchResult]
    ) -> List[Pattern]:
        """Identify patterns in evaluation failures."""
        patterns = []
        
        # Aggregate failure data
        all_failures = []
        for batch in batch_results:
            all_failures.extend(batch.common_failure_reasons)
        
        if not all_failures:
            return patterns
        
        # Count failure types
        failure_counter = Counter(all_failures)
        total_failures = sum(failure_counter.values())
        
        for failure_type, count in failure_counter.most_common(3):
            if count / total_failures > 0.2:  # More than 20% of failures
                patterns.append(Pattern(
                    pattern_type=PatternType.FAILURE_MODE,
                    pattern_id=f"frequent_{failure_type.lower().replace(' ', '_')}",
                    title=f"Frequent {failure_type}",
                    description=f"{failure_type} accounts for {count}/{total_failures} failures",
                    confidence_score=0.9,
                    impact_severity="high" if count / total_failures > 0.4 else "medium",
                    evidence=[
                        f"Failure count: {count}",
                        f"Percentage of total failures: {count/total_failures:.1%}"
                    ],
                    related_metrics={"failure_rate": count / total_failures},
                    recommendations=self._get_failure_specific_recommendations(failure_type)
                ))
        
        return patterns
    
    def _identify_conversation_flow_patterns(
        self, 
        evaluations: List[ConversationEvaluation]
    ) -> List[Pattern]:
        """Identify patterns in conversation flow quality."""
        patterns = []
        
        flow_scores = [e.conversation_flow_score for e in evaluations]
        avg_flow = statistics.mean(flow_scores)
        
        if avg_flow < 0.7:
            patterns.append(Pattern(
                pattern_type=PatternType.CONVERSATION_FLOW,
                pattern_id="poor_conversation_flow",
                title="Poor Conversation Flow",
                description=f"Conversation flow scores ({avg_flow:.2f}) indicate choppy interactions",
                confidence_score=0.8,
                impact_severity="medium",
                evidence=[
                    f"Average flow score: {avg_flow:.2f}",
                    f"{sum(1 for s in flow_scores if s < 0.5)} conversations with poor flow"
                ],
                related_metrics={"conversation_flow": avg_flow},
                recommendations=[
                    "Improve context tracking between turns",
                    "Enhance conversation coherence algorithms",
                    "Add conversation flow validation checkpoints"
                ]
            ))
        
        return patterns
    
    def _identify_quality_correlation_patterns(
        self, 
        evaluations: List[ConversationEvaluation]
    ) -> List[Pattern]:
        """Identify correlations between different quality metrics."""
        patterns = []
        
        if len(evaluations) < 10:
            return patterns
        
        # Analyze correlation between goal achievement and user satisfaction
        goal_scores = [e.goal_achievement_score for e in evaluations]
        satisfaction_scores = [e.user_satisfaction_prediction for e in evaluations]
        
        if len(goal_scores) == len(satisfaction_scores):
            correlation = self._calculate_correlation(goal_scores, satisfaction_scores)
            
            if correlation < 0.5:  # Weak correlation
                patterns.append(Pattern(
                    pattern_type=PatternType.QUALITY_CORRELATION,
                    pattern_id="weak_goal_satisfaction_correlation",
                    title="Weak Goal Achievement-Satisfaction Correlation",
                    description=f"Goal achievement and user satisfaction are weakly correlated ({correlation:.2f})",
                    confidence_score=0.7,
                    impact_severity="medium",
                    evidence=[
                        f"Correlation coefficient: {correlation:.2f}",
                        "Users may not perceive goal achievement as satisfying"
                    ],
                    related_metrics={"goal_satisfaction_correlation": correlation},
                    recommendations=[
                        "Investigate user perception of goal achievement",
                        "Improve communication of progress to users",
                        "Align goal achievement with user satisfaction factors"
                    ]
                ))
        
        return patterns
    
    def _analyze_performance_trends(
        self, 
        evaluations: List[ConversationEvaluation], 
        time_window_days: int
    ) -> List[PerformanceTrend]:
        """Analyze performance trends over time."""
        trends = []
        
        if len(evaluations) < 5:
            return trends
        
        # Sort by timestamp
        sorted_evals = sorted(evaluations, key=lambda e: e.evaluation_timestamp)
        
        # Analyze overall quality trend
        quality_trend = self._calculate_metric_trend(
            sorted_evals, 
            lambda e: e.overall_quality_score,
            "Overall Quality"
        )
        trends.append(quality_trend)
        
        # Analyze goal achievement trend
        goal_trend = self._calculate_metric_trend(
            sorted_evals,
            lambda e: e.goal_achievement_score,
            "Goal Achievement"
        )
        trends.append(goal_trend)
        
        return trends
    
    def _calculate_metric_trend(
        self,
        evaluations: List[ConversationEvaluation],
        metric_extractor: callable,
        metric_name: str
    ) -> PerformanceTrend:
        """Calculate trend for a specific metric."""
        
        # Extract data points
        data_points = [
            (e.evaluation_timestamp, metric_extractor(e))
            for e in evaluations
        ]
        
        # Convert to numerical arrays for trend analysis
        timestamps = [int(dp[0].timestamp()) for dp in data_points]
        values = [dp[1] for dp in data_points]
        
        # Simple linear regression for trend
        slope, r_squared = self._linear_regression(timestamps, values)
        
        # Determine trend direction
        if abs(slope) < 0.0001:  # Essentially flat
            direction = TrendDirection.STABLE
        elif slope > 0:
            direction = TrendDirection.IMPROVING
        else:
            direction = TrendDirection.DECLINING
        
        # Calculate change magnitude (first vs last)
        if len(values) >= 2:
            change_magnitude = ((values[-1] - values[0]) / values[0]) * 100
        else:
            change_magnitude = 0.0
        
        # Calculate confidence based on R-squared
        confidence = min(r_squared, 0.95)
        
        return PerformanceTrend(
            metric_name=metric_name,
            trend_direction=direction,
            change_magnitude=change_magnitude,
            confidence=confidence,
            time_period=f"{(data_points[-1][0] - data_points[0][0]).days} days",
            data_points=data_points,
            trend_line_slope=slope,
            r_squared=r_squared,
            significant_changes=self._identify_significant_changes(values),
            potential_causes=self._suggest_trend_causes(direction, metric_name)
        )
    
    def _identify_performance_bottlenecks(
        self,
        evaluations: List[ConversationEvaluation],
        batch_results: Optional[List[BatchResult]]
    ) -> List[BottleneckReport]:
        """Identify performance bottlenecks in the system."""
        bottlenecks = []
        
        # Analyze LLM evaluation bottlenecks
        if batch_results:
            total_cost = sum(b.total_llm_cost for b in batch_results)
            total_evals = sum(b.successful_evaluations for b in batch_results)
            
            if total_evals > 0:
                avg_cost_per_eval = total_cost / total_evals
                
                if avg_cost_per_eval > 0.1:  # High cost per evaluation
                    bottlenecks.append(BottleneckReport(
                        bottleneck_type="LLM Cost",
                        affected_component="LLM Evaluation System",
                        severity_score=min(avg_cost_per_eval * 5, 1.0),
                        frequency=total_evals,
                        average_impact_duration=0.0,
                        root_causes=[
                            "High token usage in evaluation prompts",
                            "Inefficient prompt design",
                            "Multiple LLM calls per evaluation"
                        ],
                        performance_impact={"cost_per_evaluation": avg_cost_per_eval},
                        immediate_fixes=[
                            "Optimize evaluation prompt length",
                            "Implement prompt caching",
                            "Batch multiple evaluations"
                        ],
                        long_term_improvements=[
                            "Develop local evaluation models",
                            "Implement smart prompt compression",
                            "Create evaluation result caching"
                        ],
                        estimated_improvement=0.5
                    ))
        
        return bottlenecks
    
    def _generate_improvement_recommendations(
        self,
        patterns: List[Pattern],
        trends: List[PerformanceTrend],
        bottlenecks: List[BottleneckReport]
    ) -> List[ImprovementRecommendation]:
        """Generate actionable improvement recommendations."""
        recommendations = []
        
        # Recommendations based on patterns
        for pattern in patterns:
            if pattern.impact_severity in ["high", "critical"]:
                recommendations.extend(self._pattern_to_recommendations(pattern))
        
        # Recommendations based on trends
        for trend in trends:
            if trend.trend_direction == TrendDirection.DECLINING and trend.confidence > 0.7:
                recommendations.extend(self._trend_to_recommendations(trend))
        
        # Recommendations based on bottlenecks
        for bottleneck in bottlenecks:
            if bottleneck.severity_score > 0.6:
                recommendations.extend(self._bottleneck_to_recommendations(bottleneck))
        
        # Remove duplicates and prioritize
        unique_recommendations = self._deduplicate_recommendations(recommendations)
        self._prioritize_recommendations(unique_recommendations)
        
        return sorted(unique_recommendations, key=lambda r: r.priority_score, reverse=True)
    
    def _calculate_summary_statistics(
        self, 
        evaluations: List[ConversationEvaluation]
    ) -> Dict[str, Any]:
        """Calculate summary statistics for the evaluations."""
        return {
            'unique_scenarios': len(set(e.conversation_id.split('_')[0] for e in evaluations)),
            'unique_user_types': 1,  # Would need user type data
            'avg_quality_score': statistics.mean([e.overall_quality_score for e in evaluations]) if evaluations else 0,
            'quality_score_std': statistics.stdev([e.overall_quality_score for e in evaluations]) if len(evaluations) > 1 else 0
        }
    
    def _assess_system_health(
        self,
        patterns: List[Pattern],
        trends: List[PerformanceTrend],
        bottlenecks: List[BottleneckReport]
    ) -> str:
        """Assess overall system health based on analysis."""
        
        # Count critical issues
        critical_patterns = [p for p in patterns if p.impact_severity == "critical"]
        declining_trends = [t for t in trends if t.trend_direction == TrendDirection.DECLINING]
        severe_bottlenecks = [b for b in bottlenecks if b.severity_score > 0.8]
        
        if critical_patterns or severe_bottlenecks:
            return "poor"
        elif len(declining_trends) > 1 or any(b.severity_score > 0.6 for b in bottlenecks):
            return "fair"
        elif any(t.trend_direction == TrendDirection.IMPROVING for t in trends):
            return "excellent"
        else:
            return "good"
    
    def _generate_key_insights(
        self,
        patterns: List[Pattern],
        recommendations: List[ImprovementRecommendation]
    ) -> Tuple[List[str], List[str], List[str]]:
        """Generate critical issues, quick wins, and long-term priorities."""
        
        critical_issues = [
            p.title for p in patterns 
            if p.impact_severity == "critical"
        ]
        
        quick_wins = [
            r.title for r in recommendations 
            if r.implementation_effort == "low" and r.expected_impact in ["medium", "high"]
        ]
        
        long_term_priorities = [
            r.title for r in recommendations 
            if r.implementation_effort == "high" and r.expected_impact == "high"
        ]
        
        return critical_issues, quick_wins, long_term_priorities
    
    # Helper methods
    
    def _calculate_correlation(self, x: List[float], y: List[float]) -> float:
        """Calculate Pearson correlation coefficient."""
        if len(x) != len(y) or len(x) < 2:
            return 0.0
        
        mean_x = statistics.mean(x)
        mean_y = statistics.mean(y)
        
        numerator = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(len(x)))
        sum_sq_x = sum((x[i] - mean_x) ** 2 for i in range(len(x)))
        sum_sq_y = sum((y[i] - mean_y) ** 2 for i in range(len(y)))
        
        denominator = math.sqrt(sum_sq_x * sum_sq_y)
        
        if denominator == 0:
            return 0.0
        
        return numerator / denominator
    
    def _linear_regression(self, x: List[float], y: List[float]) -> Tuple[float, float]:
        """Calculate linear regression slope and R-squared."""
        if len(x) != len(y) or len(x) < 2:
            return 0.0, 0.0
        
        n = len(x)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(x[i] * y[i] for i in range(n))
        sum_x_sq = sum(xi ** 2 for xi in x)
        sum_y_sq = sum(yi ** 2 for yi in y)
        
        # Calculate slope
        denominator = n * sum_x_sq - sum_x ** 2
        if denominator == 0:
            return 0.0, 0.0
        
        slope = (n * sum_xy - sum_x * sum_y) / denominator
        
        # Calculate R-squared
        mean_y = sum_y / n
        ss_tot = sum((yi - mean_y) ** 2 for yi in y)
        
        if ss_tot == 0:
            return slope, 1.0
        
        intercept = (sum_y - slope * sum_x) / n
        ss_res = sum((y[i] - (slope * x[i] + intercept)) ** 2 for i in range(n))
        r_squared = 1 - (ss_res / ss_tot)
        
        return slope, max(0.0, r_squared)
    
    def _calculate_pattern_priorities(self, patterns: List[Pattern]):
        """Calculate priority scores for patterns."""
        severity_weights = {"low": 0.25, "medium": 0.5, "high": 0.75, "critical": 1.0}
        
        for pattern in patterns:
            severity_score = severity_weights.get(pattern.impact_severity, 0.5)
            pattern.priority_score = pattern.confidence_score * severity_score
    
    def _get_failure_specific_recommendations(self, failure_type: str) -> List[str]:
        """Get specific recommendations for failure types."""
        recommendations_map = {
            "API Timeouts": [
                "Implement timeout retry logic",
                "Optimize API request efficiency",
                "Add circuit breaker pattern"
            ],
            "Rate Limiting": [
                "Implement exponential backoff",
                "Add request queuing system",
                "Optimize batch processing intervals"
            ],
            "Response Parsing": [
                "Improve response validation",
                "Add fallback parsing strategies",
                "Enhance error handling"
            ]
        }
        
        return recommendations_map.get(failure_type, ["Investigate root cause", "Implement error monitoring"])
    
    def _identify_significant_changes(self, values: List[float]) -> List[str]:
        """Identify significant changes in metric values."""
        if len(values) < 3:
            return []
        
        changes = []
        threshold = 0.2  # 20% change threshold
        
        for i in range(1, len(values)):
            change = abs(values[i] - values[i-1]) / values[i-1] if values[i-1] != 0 else 0
            if change > threshold:
                changes.append(f"Significant change at point {i}: {change:.1%}")
        
        return changes
    
    def _suggest_trend_causes(self, direction: TrendDirection, metric_name: str) -> List[str]:
        """Suggest potential causes for trends."""
        if direction == TrendDirection.DECLINING:
            return [
                f"Recent changes affecting {metric_name.lower()}",
                "Increased system load or complexity",
                "Data quality degradation"
            ]
        elif direction == TrendDirection.IMPROVING:
            return [
                f"Improvements to {metric_name.lower()} algorithms",
                "Better data quality",
                "System optimizations"
            ]
        else:
            return ["Stable performance indicates consistent system behavior"]
    
    def _pattern_to_recommendations(self, pattern: Pattern) -> List[ImprovementRecommendation]:
        """Convert pattern to improvement recommendations."""
        recommendations = []
        
        for i, rec_text in enumerate(pattern.recommendations):
            rec_id = f"{pattern.pattern_id}_rec_{i}"
            
            recommendations.append(ImprovementRecommendation(
                recommendation_id=rec_id,
                title=rec_text,
                description=f"Address {pattern.title}: {rec_text}",
                category="quality",
                implementation_effort="medium",
                expected_impact=pattern.impact_severity,
                time_to_implement="days",
                supporting_patterns=[pattern.pattern_id],
                priority_score=pattern.priority_score
            ))
        
        return recommendations
    
    def _trend_to_recommendations(self, trend: PerformanceTrend) -> List[ImprovementRecommendation]:
        """Convert trend to improvement recommendations."""
        recommendations = []
        
        if trend.trend_direction == TrendDirection.DECLINING:
            rec_id = f"trend_{trend.metric_name.lower().replace(' ', '_')}_decline"
            
            recommendations.append(ImprovementRecommendation(
                recommendation_id=rec_id,
                title=f"Address Declining {trend.metric_name}",
                description=f"Investigate and reverse the declining trend in {trend.metric_name}",
                category="performance",
                implementation_effort="medium",
                expected_impact="high",
                time_to_implement="weeks",
                priority_score=trend.confidence * 0.8
            ))
        
        return recommendations
    
    def _bottleneck_to_recommendations(self, bottleneck: BottleneckReport) -> List[ImprovementRecommendation]:
        """Convert bottleneck to improvement recommendations."""
        recommendations = []
        
        # Immediate fixes
        for i, fix in enumerate(bottleneck.immediate_fixes):
            rec_id = f"bottleneck_{bottleneck.affected_component.lower().replace(' ', '_')}_fix_{i}"
            
            recommendations.append(ImprovementRecommendation(
                recommendation_id=rec_id,
                title=fix,
                description=f"Immediate fix for {bottleneck.bottleneck_type}: {fix}",
                category="performance",
                implementation_effort="low",
                expected_impact="medium",
                time_to_implement="hours",
                priority_score=bottleneck.severity_score * 0.9
            ))
        
        return recommendations
    
    def _deduplicate_recommendations(
        self, 
        recommendations: List[ImprovementRecommendation]
    ) -> List[ImprovementRecommendation]:
        """Remove duplicate recommendations."""
        seen_titles = set()
        unique_recommendations = []
        
        for rec in recommendations:
            if rec.title not in seen_titles:
                seen_titles.add(rec.title)
                unique_recommendations.append(rec)
        
        return unique_recommendations
    
    def _prioritize_recommendations(self, recommendations: List[ImprovementRecommendation]):
        """Calculate and assign priority scores to recommendations."""
        effort_weights = {"low": 1.0, "medium": 0.7, "high": 0.4}
        impact_weights = {"low": 0.3, "medium": 0.6, "high": 1.0}
        
        for rec in recommendations:
            effort_score = effort_weights.get(rec.implementation_effort, 0.5)
            impact_score = impact_weights.get(rec.expected_impact, 0.5)
            
            # Priority = impact / effort (higher is better)
            rec.priority_score = impact_score / max(1 - effort_score + 0.1, 0.1)
    
    def get_analyzer_stats(self) -> Dict[str, Any]:
        """Get pattern analyzer statistics."""
        return {
            'analysis_count': self.analysis_count,
            'min_confidence_threshold': self.min_confidence_threshold
        } 