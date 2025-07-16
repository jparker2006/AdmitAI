"""essay_agent.eval.batch_processor

Intelligent batch processing system for large-scale conversation evaluations.

This module enables parallel execution of multiple evaluation scenarios with
smart scheduling, progress tracking, error recovery, and resource management.
Supports both one-time batch runs and continuous monitoring scenarios.
"""

import asyncio
import time
import json
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
import concurrent.futures
from contextlib import asynccontextmanager

from .llm_evaluator import LLMEvaluator, ConversationEvaluation
from .conversation_runner import ConversationRunner, ConversationResult
from .conversational_scenarios import ConversationScenario, ScenarioCategory
from .real_profiles import UserProfile, get_profile_by_id
from ..utils.logging import debug_print


class BatchStatus(Enum):
    """Status of batch processing."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class EvaluationStatus(Enum):
    """Status of individual evaluation."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class EvaluationTask:
    """Individual evaluation task in a batch."""
    task_id: str
    scenario: ConversationScenario
    profile: Optional[UserProfile] = None
    status: EvaluationStatus = EvaluationStatus.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    result: Optional[ConversationResult] = None
    evaluation: Optional[ConversationEvaluation] = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 2
    
    @property
    def duration_seconds(self) -> Optional[float]:
        """Get task duration in seconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None
    
    def is_retryable(self) -> bool:
        """Check if task can be retried."""
        return (self.status == EvaluationStatus.FAILED and 
                self.retry_count < self.max_retries)


@dataclass
class BatchProgress:
    """Progress tracking for batch processing."""
    total_tasks: int
    completed_tasks: int = 0
    failed_tasks: int = 0
    running_tasks: int = 0
    pending_tasks: int = 0
    
    start_time: datetime = field(default_factory=datetime.now)
    estimated_completion: Optional[datetime] = None
    
    @property
    def completion_percentage(self) -> float:
        """Get completion percentage."""
        if self.total_tasks == 0:
            return 100.0
        return (self.completed_tasks / self.total_tasks) * 100
    
    @property
    def elapsed_time(self) -> timedelta:
        """Get elapsed time since batch start."""
        return datetime.now() - self.start_time
    
    def update_eta(self, avg_task_duration: float):
        """Update estimated time of completion."""
        if self.completed_tasks > 0 and avg_task_duration > 0:
            remaining_tasks = self.total_tasks - self.completed_tasks
            remaining_seconds = remaining_tasks * avg_task_duration
            self.estimated_completion = datetime.now() + timedelta(seconds=remaining_seconds)


@dataclass
class BatchResult:
    """Results from batch processing."""
    batch_id: str
    status: BatchStatus
    progress: BatchProgress
    tasks: List[EvaluationTask]
    
    # Summary statistics
    total_duration_seconds: float
    successful_evaluations: int
    failed_evaluations: int
    average_evaluation_score: float
    
    # Resource usage
    total_llm_cost: float
    total_api_calls: int
    peak_parallel_tasks: int
    
    # Insights
    common_failure_reasons: List[str]
    performance_bottlenecks: List[str]
    recommendations: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'batch_id': self.batch_id,
            'status': self.status.value,
            'progress': {
                'total_tasks': self.progress.total_tasks,
                'completed_tasks': self.progress.completed_tasks,
                'failed_tasks': self.progress.failed_tasks,
                'completion_percentage': self.progress.completion_percentage,
                'elapsed_time_seconds': self.progress.elapsed_time.total_seconds()
            },
            'summary': {
                'total_duration_seconds': self.total_duration_seconds,
                'successful_evaluations': self.successful_evaluations,
                'failed_evaluations': self.failed_evaluations,
                'average_evaluation_score': self.average_evaluation_score,
                'total_llm_cost': self.total_llm_cost,
                'total_api_calls': self.total_api_calls,
                'peak_parallel_tasks': self.peak_parallel_tasks
            },
            'insights': {
                'common_failure_reasons': self.common_failure_reasons,
                'performance_bottlenecks': self.performance_bottlenecks,
                'recommendations': self.recommendations
            },
            'task_results': [
                {
                    'task_id': task.task_id,
                    'scenario_id': task.scenario.eval_id,
                    'status': task.status.value,
                    'duration_seconds': task.duration_seconds,
                    'overall_score': task.evaluation.overall_quality_score if task.evaluation else None,
                    'error': task.error
                }
                for task in self.tasks
            ]
        }
    
    def save_to_file(self, filepath: Union[str, Path]):
        """Save batch results to JSON file."""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)


class BatchProcessor:
    """Intelligent batch processing for large-scale evaluations."""
    
    def __init__(
        self,
        max_parallel: int = 5,
        rate_limit_delay: float = 1.0,
        enable_llm_evaluation: bool = True,
        progress_callback: Optional[Callable[[BatchProgress], None]] = None
    ):
        """
        Initialize batch processor.
        
        Args:
            max_parallel: Maximum number of parallel evaluations
            rate_limit_delay: Delay between API calls (seconds)
            enable_llm_evaluation: Whether to use LLM evaluation
            progress_callback: Callback for progress updates
        """
        self.max_parallel = max_parallel
        self.rate_limit_delay = rate_limit_delay
        self.enable_llm_evaluation = enable_llm_evaluation
        self.progress_callback = progress_callback
        
        # Initialize components
        self.llm_evaluator = LLMEvaluator() if enable_llm_evaluation else None
        self.conversation_runner = ConversationRunner()
        
        # Batch state
        self.current_batch_id: Optional[str] = None
        self.running_tasks: Dict[str, asyncio.Task] = {}
        self.cancelled = False
        
        # Statistics
        self.total_batches_processed = 0
        self.total_evaluations_completed = 0
        self.total_llm_cost = 0.0
    
    async def run_comprehensive_suite(
        self,
        scenarios: List[ConversationScenario],
        profiles: Optional[List[UserProfile]] = None,
        time_limit: Optional[int] = None,
        export_path: Optional[str] = None
    ) -> BatchResult:
        """
        Run comprehensive evaluation suite with intelligent scheduling.
        
        Args:
            scenarios: List of scenarios to evaluate
            profiles: Optional list of user profiles (auto-selected if None)
            time_limit: Maximum time in seconds (None for no limit)
            export_path: Path to export results (None to skip export)
            
        Returns:
            Complete batch results
        """
        
        batch_id = f"batch_{int(time.time())}"
        self.current_batch_id = batch_id
        self.cancelled = False
        
        debug_print(True, f"Starting comprehensive evaluation suite: {batch_id}")
        debug_print(True, f"Scenarios: {len(scenarios)}, Max parallel: {self.max_parallel}")
        
        # Create evaluation tasks
        tasks = self._create_evaluation_tasks(scenarios, profiles)
        progress = BatchProgress(total_tasks=len(tasks))
        
        # Start batch processing
        start_time = datetime.now()
        
        try:
            # Process tasks with smart scheduling
            await self._process_tasks_intelligently(tasks, progress, time_limit)
            
            # Calculate final results
            end_time = datetime.now()
            batch_result = self._calculate_batch_results(
                batch_id, tasks, progress, start_time, end_time
            )
            
            # Export results if requested
            if export_path:
                batch_result.save_to_file(export_path)
                debug_print(True, f"Results exported to: {export_path}")
            
            self.total_batches_processed += 1
            debug_print(True, f"Batch {batch_id} completed: {batch_result.successful_evaluations}/{len(tasks)} successful")
            
            return batch_result
            
        except Exception as e:
            debug_print(True, f"Batch processing failed: {e}")
            # Return partial results
            end_time = datetime.now()
            return self._calculate_batch_results(
                batch_id, tasks, progress, start_time, end_time, error=str(e)
            )
    
    async def run_continuous_monitoring(
        self,
        duration_hours: int,
        scenario_rotation: bool = True,
        base_scenarios: Optional[List[ConversationScenario]] = None
    ) -> List[BatchResult]:
        """
        Run continuous monitoring with periodic evaluation batches.
        
        Args:
            duration_hours: How long to run monitoring
            scenario_rotation: Whether to rotate scenarios
            base_scenarios: Base scenarios to use (auto-selected if None)
            
        Returns:
            List of batch results from monitoring period
        """
        
        debug_print(True, f"Starting continuous monitoring for {duration_hours} hours")
        
        end_time = datetime.now() + timedelta(hours=duration_hours)
        batch_results = []
        batch_count = 0
        
        # Determine batch interval (run every 30 minutes or based on scenario count)
        batch_interval_minutes = min(30, max(10, duration_hours * 60 // 10))
        
        while datetime.now() < end_time and not self.cancelled:
            batch_count += 1
            batch_start = datetime.now()
            
            debug_print(True, f"Starting monitoring batch {batch_count}")
            
            # Select scenarios for this batch
            if scenario_rotation and base_scenarios:
                # Rotate through different scenario subsets
                scenarios = self._select_rotated_scenarios(base_scenarios, batch_count)
            else:
                scenarios = base_scenarios or self._get_default_monitoring_scenarios()
            
            # Run batch
            try:
                batch_result = await self.run_comprehensive_suite(
                    scenarios=scenarios[:10],  # Limit to 10 scenarios per batch
                    time_limit=batch_interval_minutes * 60 - 120  # Leave 2 min buffer
                )
                batch_results.append(batch_result)
                
            except Exception as e:
                debug_print(True, f"Monitoring batch {batch_count} failed: {e}")
            
            # Wait for next batch interval
            next_batch_time = batch_start + timedelta(minutes=batch_interval_minutes)
            wait_time = (next_batch_time - datetime.now()).total_seconds()
            
            if wait_time > 0:
                debug_print(True, f"Waiting {wait_time:.1f}s until next batch")
                await asyncio.sleep(wait_time)
        
        debug_print(True, f"Continuous monitoring completed: {len(batch_results)} batches")
        return batch_results
    
    def cancel_current_batch(self):
        """Cancel currently running batch."""
        self.cancelled = True
        debug_print(True, f"Cancelling batch: {self.current_batch_id}")
        
        # Cancel running tasks
        for task_id, task in self.running_tasks.items():
            if not task.done():
                task.cancel()
                debug_print(True, f"Cancelled task: {task_id}")
    
    async def _process_tasks_intelligently(
        self,
        tasks: List[EvaluationTask],
        progress: BatchProgress,
        time_limit: Optional[int]
    ):
        """Process tasks with intelligent scheduling and resource management."""
        
        # Create semaphore for parallel control
        semaphore = asyncio.Semaphore(self.max_parallel)
        
        # Track timing for ETA calculation
        completed_durations = []
        peak_parallel = 0
        
        async def process_single_task(task: EvaluationTask) -> EvaluationTask:
            async with semaphore:
                current_parallel = len([t for t in self.running_tasks.values() if not t.done()])
                peak_parallel = max(peak_parallel, current_parallel)
                
                return await self._execute_evaluation_task(task, completed_durations, progress)
        
        # Start all tasks
        task_futures = []
        for task in tasks:
            if self.cancelled:
                break
                
            future = asyncio.create_task(process_single_task(task))
            self.running_tasks[task.task_id] = future
            task_futures.append(future)
            
            # Rate limiting
            if self.rate_limit_delay > 0:
                await asyncio.sleep(self.rate_limit_delay)
        
        # Wait for completion with timeout
        try:
            if time_limit:
                await asyncio.wait_for(
                    asyncio.gather(*task_futures, return_exceptions=True),
                    timeout=time_limit
                )
            else:
                await asyncio.gather(*task_futures, return_exceptions=True)
                
        except asyncio.TimeoutError:
            debug_print(True, f"Batch processing timed out after {time_limit}s")
            self.cancel_current_batch()
    
    async def _execute_evaluation_task(
        self,
        task: EvaluationTask,
        completed_durations: List[float],
        progress: BatchProgress
    ) -> EvaluationTask:
        """Execute a single evaluation task with error handling and retries."""
        
        task.status = EvaluationStatus.RUNNING
        task.start_time = datetime.now()
        progress.running_tasks += 1
        progress.pending_tasks -= 1
        
        if self.progress_callback:
            self.progress_callback(progress)
        
        try:
            # Execute conversation evaluation
            conversation_result = await self.conversation_runner.execute_evaluation(
                task.scenario, task.profile
            )
            task.result = conversation_result
            
            # Perform LLM evaluation if enabled
            if self.llm_evaluator and conversation_result.conversation_turns:
                llm_evaluation = await self.llm_evaluator.evaluate_conversation_quality(
                    conversation_result.conversation_turns,
                    task.profile or self._get_default_profile(),
                    task.scenario
                )
                task.evaluation = llm_evaluation
            
            task.status = EvaluationStatus.COMPLETED
            task.end_time = datetime.now()
            
            # Update progress
            progress.running_tasks -= 1
            progress.completed_tasks += 1
            
            # Track timing for ETA
            if task.duration_seconds:
                completed_durations.append(task.duration_seconds)
                if len(completed_durations) >= 3:  # Need some samples for ETA
                    avg_duration = sum(completed_durations) / len(completed_durations)
                    progress.update_eta(avg_duration)
            
            debug_print(True, f"Task {task.task_id} completed in {task.duration_seconds:.1f}s")
            
        except Exception as e:
            task.status = EvaluationStatus.FAILED
            task.error = str(e)
            task.end_time = datetime.now()
            
            progress.running_tasks -= 1
            progress.failed_tasks += 1
            
            debug_print(True, f"Task {task.task_id} failed: {e}")
            
            # Retry if possible
            if task.is_retryable():
                task.retry_count += 1
                task.status = EvaluationStatus.PENDING
                progress.failed_tasks -= 1
                progress.pending_tasks += 1
                
                debug_print(True, f"Retrying task {task.task_id} (attempt {task.retry_count + 1})")
                
                # Retry with exponential backoff
                await asyncio.sleep(2 ** task.retry_count)
                return await self._execute_evaluation_task(task, completed_durations, progress)
        
        if self.progress_callback:
            self.progress_callback(progress)
        
        return task
    
    def _create_evaluation_tasks(
        self,
        scenarios: List[ConversationScenario],
        profiles: Optional[List[UserProfile]]
    ) -> List[EvaluationTask]:
        """Create evaluation tasks from scenarios and profiles."""
        
        tasks = []
        
        for i, scenario in enumerate(scenarios):
            # Select appropriate profile
            if profiles:
                profile = profiles[i % len(profiles)]
            else:
                profile = self._select_profile_for_scenario(scenario)
            
            task = EvaluationTask(
                task_id=f"{scenario.eval_id}_{i}",
                scenario=scenario,
                profile=profile,
                status=EvaluationStatus.PENDING
            )
            
            tasks.append(task)
        
        # Update progress
        progress = BatchProgress(total_tasks=len(tasks))
        progress.pending_tasks = len(tasks)
        
        return tasks
    
    def _select_profile_for_scenario(self, scenario: ConversationScenario) -> Optional[UserProfile]:
        """Select appropriate user profile for scenario."""
        try:
            # Use scenario's specified profile or select based on category
            profile_id = scenario.user_profile
            
            if profile_id:
                return get_profile_by_id(profile_id)
            
            # Fallback selection based on scenario category
            if scenario.category == ScenarioCategory.NEW_USER:
                return get_profile_by_id("academic_achiever_emma")
            elif scenario.category == ScenarioCategory.COMPLEX:
                return get_profile_by_id("creative_artist_marcus")
            else:
                return get_profile_by_id("balanced_applicant_alex")
                
        except Exception as e:
            debug_print(True, f"Failed to select profile for {scenario.eval_id}: {e}")
            return None
    
    def _get_default_profile(self) -> UserProfile:
        """Get default user profile for fallback."""
        try:
            return get_profile_by_id("academic_achiever_emma")
        except:
            # Create minimal fallback profile
            from ..memory.user_profile_schema import (
                UserProfile, Background, WritingExperience, Goals, WritingStyle, EssayHistory
            )
            
            return UserProfile(
                profile_id="fallback_user",
                background=Background(
                    academic_level="high_school_senior",
                    intended_majors=["undecided"],
                    gpa=3.5,
                    test_scores={}
                ),
                writing_experience=WritingExperience(
                    essay_writing_experience="intermediate"
                ),
                goals=Goals(
                    primary_objectives=["get_into_college"]
                ),
                writing_style=WritingStyle(
                    communication_style="collaborative"
                ),
                essay_history=EssayHistory(essays=[])
            )
    
    def _calculate_batch_results(
        self,
        batch_id: str,
        tasks: List[EvaluationTask],
        progress: BatchProgress,
        start_time: datetime,
        end_time: datetime,
        error: Optional[str] = None
    ) -> BatchResult:
        """Calculate comprehensive batch results."""
        
        # Basic statistics
        successful_tasks = [t for t in tasks if t.status == EvaluationStatus.COMPLETED]
        failed_tasks = [t for t in tasks if t.status == EvaluationStatus.FAILED]
        
        total_duration = (end_time - start_time).total_seconds()
        
        # Calculate average evaluation score
        evaluation_scores = [
            t.evaluation.overall_quality_score 
            for t in successful_tasks 
            if t.evaluation
        ]
        avg_score = sum(evaluation_scores) / len(evaluation_scores) if evaluation_scores else 0.0
        
        # Calculate LLM costs
        total_cost = self.llm_evaluator.total_cost if self.llm_evaluator else 0.0
        total_api_calls = self.llm_evaluator.total_evaluations if self.llm_evaluator else 0
        
        # Analyze failure reasons
        failure_reasons = [t.error for t in failed_tasks if t.error]
        common_failures = self._analyze_common_failures(failure_reasons)
        
        # Generate recommendations
        recommendations = self._generate_batch_recommendations(
            tasks, successful_tasks, failed_tasks, total_duration
        )
        
        # Determine final status
        if error:
            status = BatchStatus.FAILED
        elif self.cancelled:
            status = BatchStatus.CANCELLED
        elif len(successful_tasks) == len(tasks):
            status = BatchStatus.COMPLETED
        else:
            status = BatchStatus.COMPLETED  # Partial success still counts as completed
        
        return BatchResult(
            batch_id=batch_id,
            status=status,
            progress=progress,
            tasks=tasks,
            total_duration_seconds=total_duration,
            successful_evaluations=len(successful_tasks),
            failed_evaluations=len(failed_tasks),
            average_evaluation_score=avg_score,
            total_llm_cost=total_cost,
            total_api_calls=total_api_calls,
            peak_parallel_tasks=self.max_parallel,
            common_failure_reasons=common_failures,
            performance_bottlenecks=self._identify_bottlenecks(tasks),
            recommendations=recommendations
        )
    
    def _analyze_common_failures(self, failure_reasons: List[str]) -> List[str]:
        """Analyze common failure patterns."""
        if not failure_reasons:
            return []
        
        # Simple frequency analysis
        failure_counts = {}
        for reason in failure_reasons:
            # Categorize error types
            if "timeout" in reason.lower():
                category = "API Timeouts"
            elif "rate limit" in reason.lower():
                category = "Rate Limiting" 
            elif "json" in reason.lower() or "parse" in reason.lower():
                category = "Response Parsing"
            elif "connection" in reason.lower():
                category = "Connection Issues"
            else:
                category = "Other Errors"
            
            failure_counts[category] = failure_counts.get(category, 0) + 1
        
        # Return most common failures
        return [
            f"{category}: {count} occurrences"
            for category, count in sorted(failure_counts.items(), key=lambda x: x[1], reverse=True)
        ]
    
    def _identify_bottlenecks(self, tasks: List[EvaluationTask]) -> List[str]:
        """Identify performance bottlenecks."""
        bottlenecks = []
        
        # Analyze task durations
        completed_tasks = [t for t in tasks if t.duration_seconds is not None]
        if completed_tasks:
            durations = [t.duration_seconds for t in completed_tasks]
            avg_duration = sum(durations) / len(durations)
            slow_tasks = [t for t in completed_tasks if t.duration_seconds > avg_duration * 2]
            
            if slow_tasks:
                bottlenecks.append(f"Slow evaluations: {len(slow_tasks)} tasks took >2x average time")
        
        # Check for rate limiting issues
        failed_tasks = [t for t in tasks if t.status == EvaluationStatus.FAILED]
        rate_limit_failures = [t for t in failed_tasks if t.error and "rate" in t.error.lower()]
        
        if rate_limit_failures:
            bottlenecks.append(f"Rate limiting: {len(rate_limit_failures)} tasks failed due to rate limits")
        
        return bottlenecks
    
    def _generate_batch_recommendations(
        self,
        all_tasks: List[EvaluationTask],
        successful_tasks: List[EvaluationTask],
        failed_tasks: List[EvaluationTask],
        total_duration: float
    ) -> List[str]:
        """Generate recommendations for improving batch processing."""
        recommendations = []
        
        # Success rate recommendations
        success_rate = len(successful_tasks) / len(all_tasks) if all_tasks else 0
        if success_rate < 0.9:
            recommendations.append(f"Improve success rate: {success_rate:.1%} success rate is below 90%")
        
        # Performance recommendations
        if total_duration > 600:  # More than 10 minutes
            recommendations.append("Consider increasing parallel execution limit for faster processing")
        
        # Cost recommendations
        if self.llm_evaluator and self.llm_evaluator.total_cost > 1.0:
            avg_cost = self.llm_evaluator.total_cost / len(successful_tasks) if successful_tasks else 0
            recommendations.append(f"Monitor LLM costs: ${avg_cost:.3f} average per evaluation")
        
        # Quality recommendations
        if successful_tasks:
            avg_quality = sum(
                t.evaluation.overall_quality_score for t in successful_tasks if t.evaluation
            ) / len([t for t in successful_tasks if t.evaluation])
            
            if avg_quality < 0.7:
                recommendations.append("Conversation quality is below 70% - investigate agent performance")
        
        return recommendations or ["Batch processing performed well - no major improvements needed"]
    
    def _select_rotated_scenarios(
        self,
        base_scenarios: List[ConversationScenario],
        batch_number: int
    ) -> List[ConversationScenario]:
        """Select rotated subset of scenarios for continuous monitoring."""
        # Simple rotation based on batch number
        scenarios_per_batch = min(5, len(base_scenarios))
        start_idx = (batch_number - 1) * scenarios_per_batch % len(base_scenarios)
        end_idx = start_idx + scenarios_per_batch
        
        if end_idx <= len(base_scenarios):
            return base_scenarios[start_idx:end_idx]
        else:
            # Wrap around
            return base_scenarios[start_idx:] + base_scenarios[:end_idx - len(base_scenarios)]
    
    def _get_default_monitoring_scenarios(self) -> List[ConversationScenario]:
        """Get default scenarios for monitoring."""
        # This would typically load from the conversational_scenarios module
        # For now, return empty list - this would be populated with actual scenarios
        return []
    
    def get_processor_stats(self) -> Dict[str, Any]:
        """Get batch processor statistics."""
        return {
            'total_batches_processed': self.total_batches_processed,
            'total_evaluations_completed': self.total_evaluations_completed,
            'total_llm_cost': self.total_llm_cost,
            'max_parallel': self.max_parallel,
            'rate_limit_delay': self.rate_limit_delay,
            'llm_evaluation_enabled': self.enable_llm_evaluation,
            'current_batch_id': self.current_batch_id
        } 