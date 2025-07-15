"""Real-time workflow performance metrics collection and analysis.

This module provides comprehensive metrics tracking for essay workflows including:
- Workflow execution timing and success rates
- Tool-level performance monitoring
- Resource utilization tracking
- Performance trend analysis
"""

import json
import time
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta

import numpy as np


@dataclass
class PerformanceMetric:
    """Single performance measurement for a workflow or tool."""
    timestamp: float
    workflow_id: str
    tool_name: str
    execution_time: float
    success: bool
    error_message: Optional[str] = None
    resource_usage: Optional[Dict[str, float]] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class WorkflowExecution:
    """Complete workflow execution record."""
    workflow_id: str
    start_time: float
    end_time: Optional[float] = None
    success: Optional[bool] = None
    total_time: Optional[float] = None
    tool_executions: List[PerformanceMetric] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.tool_executions is None:
            self.tool_executions = []


@dataclass
class PerformanceReport:
    """Comprehensive performance analysis report."""
    time_window: int  # seconds
    total_workflows: int
    successful_workflows: int
    failed_workflows: int
    avg_execution_time: float
    p95_execution_time: float
    tool_performance: Dict[str, Dict[str, float]]
    resource_utilization: Dict[str, float]
    bottlenecks: List[str]
    recommendations: List[str]
    trend_analysis: Dict[str, List[float]]


class WorkflowMetrics:
    """Real-time workflow performance metrics collection and analysis."""
    
    def __init__(self, metrics_store: Optional[str] = None):
        """Initialize metrics collector.
        
        Args:
            metrics_store: Optional path to persistent metrics storage
        """
        self.metrics_store = Path(metrics_store) if metrics_store else None
        self.active_workflows: Dict[str, WorkflowExecution] = {}
        self.completed_workflows: deque = deque(maxlen=1000)  # Keep last 1000 executions
        self.tool_metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=500))
        self.resource_history: deque = deque(maxlen=1000)
        
        # Performance caches
        self._last_report_time = 0
        self._cached_report: Optional[PerformanceReport] = None
        
        # Load historical data if available
        if self.metrics_store and self.metrics_store.exists():
            self._load_historical_data()
    
    def record_workflow_start(self, workflow_id: str, metadata: Dict[str, Any]) -> None:
        """Record the start of a workflow execution."""
        execution = WorkflowExecution(
            workflow_id=workflow_id,
            start_time=time.time(),
            metadata=metadata
        )
        self.active_workflows[workflow_id] = execution
        
        # Log metrics
        print(f"📊 Workflow {workflow_id} started")
    
    def record_workflow_end(self, workflow_id: str, result: Dict[str, Any]) -> None:
        """Record the completion of a workflow execution."""
        if workflow_id not in self.active_workflows:
            print(f"⚠️  Warning: Workflow {workflow_id} not found in active workflows")
            return
        
        execution = self.active_workflows.pop(workflow_id)
        execution.end_time = time.time()
        execution.total_time = execution.end_time - execution.start_time
        execution.success = result.get('success', True)
        execution.error_message = result.get('error')
        
        # Add to completed workflows
        self.completed_workflows.append(execution)
        
        # Persist to storage if configured
        if self.metrics_store:
            self._persist_execution(execution)
        
        # Log metrics
        status = "✅" if execution.success else "❌"
        print(f"📊 Workflow {workflow_id} completed {status} in {execution.total_time:.2f}s")
    
    def record_tool_execution(self, tool_name: str, execution_time: float, 
                            success: bool, workflow_id: str = "unknown",
                            error_message: str = None, resource_usage: Dict[str, float] = None) -> None:
        """Record a tool execution within a workflow."""
        metric = PerformanceMetric(
            timestamp=time.time(),
            workflow_id=workflow_id,
            tool_name=tool_name,
            execution_time=execution_time,
            success=success,
            error_message=error_message,
            resource_usage=resource_usage
        )
        
        # Add to tool metrics
        self.tool_metrics[tool_name].append(metric)
        
        # Add to active workflow if it exists
        if workflow_id in self.active_workflows:
            self.active_workflows[workflow_id].tool_executions.append(metric)
        
        # Log metrics
        status = "✅" if success else "❌"
        print(f"🔧 Tool {tool_name} executed {status} in {execution_time:.2f}s")
    
    def record_workflow_failure(self, workflow_id: str, error_message: str) -> None:
        """Record a workflow failure."""
        if workflow_id in self.active_workflows:
            execution = self.active_workflows.pop(workflow_id)
            execution.end_time = time.time()
            execution.total_time = execution.end_time - execution.start_time
            execution.success = False
            execution.error_message = error_message
            
            self.completed_workflows.append(execution)
            
            if self.metrics_store:
                self._persist_execution(execution)
        
        print(f"❌ Workflow {workflow_id} failed: {error_message}")
    
    def get_performance_summary(self, time_window: int = 3600) -> PerformanceReport:
        """Get comprehensive performance summary for the specified time window.
        
        Args:
            time_window: Time window in seconds (default: 1 hour)
            
        Returns:
            PerformanceReport with comprehensive metrics
        """
        # Use cached report if recent enough (5 minute cache)
        current_time = time.time()
        if (self._cached_report and 
            current_time - self._last_report_time < 300):
            return self._cached_report
        
        cutoff_time = current_time - time_window
        
        # Filter recent executions
        recent_executions = [
            exec for exec in self.completed_workflows 
            if exec.start_time >= cutoff_time
        ]
        
        # Calculate basic metrics
        total_workflows = len(recent_executions)
        successful_workflows = sum(1 for exec in recent_executions if exec.success)
        failed_workflows = total_workflows - successful_workflows
        
        execution_times = [exec.total_time for exec in recent_executions if exec.total_time]
        avg_execution_time = np.mean(execution_times) if execution_times else 0
        p95_execution_time = np.percentile(execution_times, 95) if execution_times else 0
        
        # Tool performance analysis
        tool_performance = self._analyze_tool_performance(cutoff_time)
        
        # Resource utilization (mock for now - would integrate with actual system metrics)
        resource_utilization = {
            'cpu': 0.45,  # 45% CPU utilization
            'memory': 0.52,  # 52% memory utilization
            'disk': 0.23   # 23% disk utilization
        }
        
        # Identify bottlenecks
        bottlenecks = self._identify_bottlenecks(tool_performance)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(bottlenecks, tool_performance)
        
        # Trend analysis
        trend_analysis = self._analyze_trends(recent_executions)
        
        report = PerformanceReport(
            time_window=time_window,
            total_workflows=total_workflows,
            successful_workflows=successful_workflows,
            failed_workflows=failed_workflows,
            avg_execution_time=avg_execution_time,
            p95_execution_time=p95_execution_time,
            tool_performance=tool_performance,
            resource_utilization=resource_utilization,
            bottlenecks=bottlenecks,
            recommendations=recommendations,
            trend_analysis=trend_analysis
        )
        
        # Cache the report
        self._cached_report = report
        self._last_report_time = current_time
        
        return report
    
    def get_total_processed(self) -> int:
        """Get total number of workflows processed."""
        return len(self.completed_workflows)
    
    def get_avg_processing_time(self) -> float:
        """Get average processing time across all workflows."""
        times = [exec.total_time for exec in self.completed_workflows if exec.total_time]
        return np.mean(times) if times else 0
    
    def get_performance_trends(self, hours: int = 24) -> Dict[str, List[float]]:
        """Get performance trends over the specified time period."""
        cutoff_time = time.time() - (hours * 3600)
        recent_executions = [
            exec for exec in self.completed_workflows 
            if exec.start_time >= cutoff_time
        ]
        
        return self._analyze_trends(recent_executions)
    
    def _analyze_tool_performance(self, cutoff_time: float) -> Dict[str, Dict[str, float]]:
        """Analyze performance metrics for each tool."""
        tool_performance = {}
        
        for tool_name, metrics in self.tool_metrics.items():
            # Filter recent metrics
            recent_metrics = [m for m in metrics if m.timestamp >= cutoff_time]
            
            if not recent_metrics:
                continue
            
            execution_times = [m.execution_time for m in recent_metrics]
            success_rate = sum(1 for m in recent_metrics if m.success) / len(recent_metrics)
            
            tool_performance[tool_name] = {
                'avg_time': np.mean(execution_times),
                'p95_time': np.percentile(execution_times, 95),
                'success_rate': success_rate,
                'total_executions': len(recent_metrics)
            }
        
        return tool_performance
    
    def _identify_bottlenecks(self, tool_performance: Dict[str, Dict[str, float]]) -> List[str]:
        """Identify performance bottlenecks."""
        bottlenecks = []
        
        for tool_name, metrics in tool_performance.items():
            # High execution time bottleneck
            if metrics['avg_time'] > 10.0:  # 10 seconds threshold
                bottlenecks.append(f"High execution time: {tool_name} ({metrics['avg_time']:.2f}s)")
            
            # Low success rate bottleneck
            if metrics['success_rate'] < 0.9:  # 90% success rate threshold
                bottlenecks.append(f"Low success rate: {tool_name} ({metrics['success_rate']:.1%})")
        
        return bottlenecks
    
    def _generate_recommendations(self, bottlenecks: List[str], 
                                tool_performance: Dict[str, Dict[str, float]]) -> List[str]:
        """Generate optimization recommendations."""
        recommendations = []
        
        # Recommendations based on bottlenecks
        for bottleneck in bottlenecks:
            if "High execution time" in bottleneck:
                recommendations.append("Consider optimizing slow tools or adding parallel processing")
            elif "Low success rate" in bottleneck:
                recommendations.append("Improve error handling and retry logic for failing tools")
        
        # General recommendations
        if not bottlenecks:
            recommendations.append("System performance is optimal")
        
        return recommendations
    
    def _analyze_trends(self, executions: List[WorkflowExecution]) -> Dict[str, List[float]]:
        """Analyze performance trends over time."""
        if not executions:
            return {}
        
        # Sort by start time
        executions.sort(key=lambda x: x.start_time)
        
        # Calculate hourly averages
        hourly_times = []
        hourly_success_rates = []
        
        current_hour = int(executions[0].start_time // 3600)
        hour_times = []
        hour_successes = []
        
        for exec in executions:
            exec_hour = int(exec.start_time // 3600)
            
            if exec_hour != current_hour:
                # Save current hour data
                if hour_times:
                    hourly_times.append(np.mean(hour_times))
                    hourly_success_rates.append(np.mean(hour_successes))
                
                # Start new hour
                current_hour = exec_hour
                hour_times = []
                hour_successes = []
            
            if exec.total_time:
                hour_times.append(exec.total_time)
                hour_successes.append(1 if exec.success else 0)
        
        # Add final hour
        if hour_times:
            hourly_times.append(np.mean(hour_times))
            hourly_success_rates.append(np.mean(hour_successes))
        
        return {
            'execution_times': hourly_times,
            'success_rates': hourly_success_rates
        }
    
    def _persist_execution(self, execution: WorkflowExecution) -> None:
        """Persist execution data to storage."""
        if not self.metrics_store:
            return
        
        try:
            # Create timestamped filename
            timestamp = datetime.fromtimestamp(execution.start_time).strftime("%Y%m%d_%H")
            filename = self.metrics_store / f"workflow_metrics_{timestamp}.jsonl"
            
            # Write execution data
            with open(filename, 'a') as f:
                json.dump(asdict(execution), f, default=str)
                f.write('\n')
        except Exception as e:
            print(f"⚠️  Warning: Failed to persist metrics: {e}")
    
    def _load_historical_data(self) -> None:
        """Load historical metrics data from storage."""
        try:
            # Load recent metrics files
            for metrics_file in self.metrics_store.glob("workflow_metrics_*.jsonl"):
                with open(metrics_file, 'r') as f:
                    for line in f:
                        exec_data = json.loads(line)
                        # Convert back to WorkflowExecution (simplified)
                        if exec_data.get('end_time'):
                            self.completed_workflows.append(WorkflowExecution(**exec_data))
        except Exception as e:
            print(f"⚠️  Warning: Failed to load historical data: {e}") 