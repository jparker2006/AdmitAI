"""Performance bottleneck detection and optimization recommendations.

This module provides comprehensive bottleneck analysis including:
- Tool execution time analysis
- Resource utilization bottleneck detection
- Workflow stage performance analysis
- Optimization recommendations based on performance patterns
"""

import time
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any

import numpy as np


@dataclass
class Bottleneck:
    """Identified performance bottleneck."""
    type: str  # 'slow_tool', 'resource_constraint', 'workflow_stage', 'system_limit'
    component: str  # Name of the component (tool, resource, stage)
    severity: float  # Severity score (1.0 = baseline, higher = more severe)
    impact: str  # 'high', 'medium', 'low'
    description: str  # Human-readable description
    metrics: Dict[str, Any]  # Supporting metrics
    detected_at: float  # Timestamp when detected


@dataclass
class Optimization:
    """Optimization recommendation."""
    type: str  # 'parallel_processing', 'caching', 'resource_scaling', 'algorithm_change'
    target: str  # Target component for optimization
    description: str  # Human-readable description
    expected_improvement: float  # Expected improvement percentage
    implementation_effort: str  # 'low', 'medium', 'high'
    priority: str  # 'high', 'medium', 'low'
    specific_actions: List[str]  # Specific implementation steps


class BottleneckDetector:
    """Performance bottleneck detection and optimization system."""
    
    def __init__(self, threshold_percentile: float = 95.0, min_samples: int = 10):
        """Initialize bottleneck detector.
        
        Args:
            threshold_percentile: Percentile threshold for slow performance detection
            min_samples: Minimum number of samples needed for analysis
        """
        self.threshold_percentile = threshold_percentile
        self.min_samples = min_samples
        
        # Performance tracking
        self.tool_execution_times: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.resource_utilization_history: deque = deque(maxlen=1000)
        self.workflow_stage_times: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        
        # Bottleneck cache
        self._last_analysis_time = 0
        self._cached_bottlenecks: List[Bottleneck] = []
        
        # Optimization templates
        self.optimization_templates = self._initialize_optimization_templates()
    
    def record_tool_execution(self, tool_name: str, execution_time: float, 
                            success: bool, resource_usage: Dict[str, float] = None) -> None:
        """Record tool execution performance."""
        self.tool_execution_times[tool_name].append({
            'time': execution_time,
            'success': success,
            'timestamp': time.time(),
            'resource_usage': resource_usage or {}
        })
    
    def record_resource_utilization(self, cpu_percent: float, memory_percent: float, 
                                  disk_percent: float) -> None:
        """Record resource utilization metrics."""
        self.resource_utilization_history.append({
            'cpu': cpu_percent,
            'memory': memory_percent,
            'disk': disk_percent,
            'timestamp': time.time()
        })
    
    def record_workflow_stage(self, stage_name: str, execution_time: float, 
                            success: bool) -> None:
        """Record workflow stage performance."""
        self.workflow_stage_times[stage_name].append({
            'time': execution_time,
            'success': success,
            'timestamp': time.time()
        })
    
    def analyze_performance(self, time_window: int = 3600) -> List[Bottleneck]:
        """Analyze performance and identify bottlenecks.
        
        Args:
            time_window: Time window for analysis in seconds
            
        Returns:
            List of identified bottlenecks sorted by severity
        """
        # Use cache if recent enough (5 minutes)
        current_time = time.time()
        if current_time - self._last_analysis_time < 300:
            return self._cached_bottlenecks
        
        bottlenecks = []
        cutoff_time = current_time - time_window
        
        # Analyze tool performance bottlenecks
        bottlenecks.extend(self._analyze_tool_bottlenecks(cutoff_time))
        
        # Analyze resource bottlenecks
        bottlenecks.extend(self._analyze_resource_bottlenecks(cutoff_time))
        
        # Analyze workflow stage bottlenecks
        bottlenecks.extend(self._analyze_workflow_stage_bottlenecks(cutoff_time))
        
        # Sort by severity and impact
        bottlenecks.sort(key=lambda x: (
            {'high': 3, 'medium': 2, 'low': 1}.get(x.impact, 0),
            x.severity
        ), reverse=True)
        
        # Cache results
        self._cached_bottlenecks = bottlenecks
        self._last_analysis_time = current_time
        
        return bottlenecks
    
    def detect_slow_tools(self, tool_metrics: Dict[str, List[float]]) -> List[str]:
        """Detect tools with slow execution times.
        
        Args:
            tool_metrics: Dict mapping tool names to execution times
            
        Returns:
            List of tool names with slow performance
        """
        slow_tools = []
        
        for tool_name, times in tool_metrics.items():
            if len(times) < self.min_samples:
                continue
            
            # Calculate performance metrics
            avg_time = np.mean(times)
            p95_time = np.percentile(times, 95)
            
            # Check if tool is slow (p95 > 2x average or avg > 5 seconds)
            if p95_time > 2 * avg_time or avg_time > 5.0:
                slow_tools.append(tool_name)
        
        return slow_tools
    
    def suggest_optimizations(self, bottlenecks: List[Bottleneck]) -> List[Optimization]:
        """Generate optimization recommendations based on bottlenecks.
        
        Args:
            bottlenecks: List of identified bottlenecks
            
        Returns:
            List of optimization recommendations
        """
        optimizations = []
        
        for bottleneck in bottlenecks:
            # Get optimization templates for this bottleneck type
            templates = self.optimization_templates.get(bottleneck.type, [])
            
            for template in templates:
                # Customize template for this specific bottleneck
                optimization = self._customize_optimization(template, bottleneck)
                optimizations.append(optimization)
        
        # Sort by priority and expected improvement
        optimizations.sort(key=lambda x: (
            {'high': 3, 'medium': 2, 'low': 1}.get(x.priority, 0),
            x.expected_improvement
        ), reverse=True)
        
        return optimizations
    
    def get_current_bottlenecks(self) -> List[Bottleneck]:
        """Get current bottlenecks (cached or fresh analysis)."""
        return self.analyze_performance()
    
    def get_performance_trends(self, hours: int = 24) -> Dict[str, List[float]]:
        """Get performance trends over time."""
        cutoff_time = time.time() - (hours * 3600)
        
        # Tool performance trends
        tool_trends = {}
        for tool_name, executions in self.tool_execution_times.items():
            recent_times = [
                exec['time'] for exec in executions 
                if exec['timestamp'] >= cutoff_time
            ]
            
            if recent_times:
                # Calculate hourly averages
                hourly_avg = self._calculate_hourly_averages(
                    [(exec['timestamp'], exec['time']) for exec in executions 
                     if exec['timestamp'] >= cutoff_time]
                )
                tool_trends[tool_name] = hourly_avg
        
        return tool_trends
    
    def _analyze_tool_bottlenecks(self, cutoff_time: float) -> List[Bottleneck]:
        """Analyze tool execution bottlenecks."""
        bottlenecks = []
        
        for tool_name, executions in self.tool_execution_times.items():
            # Filter recent executions
            recent_executions = [
                exec for exec in executions if exec['timestamp'] >= cutoff_time
            ]
            
            if len(recent_executions) < self.min_samples:
                continue
            
            # Calculate metrics
            times = [exec['time'] for exec in recent_executions]
            success_rate = sum(1 for exec in recent_executions if exec['success']) / len(recent_executions)
            
            avg_time = np.mean(times)
            p95_time = np.percentile(times, self.threshold_percentile)
            
            # Detect slow tool bottleneck
            if p95_time > 10.0 or avg_time > 5.0:  # Thresholds for slow tools
                severity = max(p95_time / 5.0, avg_time / 2.5)  # Severity calculation
                impact = 'high' if severity > 3.0 else 'medium' if severity > 1.5 else 'low'
                
                bottlenecks.append(Bottleneck(
                    type='slow_tool',
                    component=tool_name,
                    severity=severity,
                    impact=impact,
                    description=f"Tool {tool_name} has slow execution times (avg: {avg_time:.2f}s, p95: {p95_time:.2f}s)",
                    metrics={
                        'avg_time': avg_time,
                        'p95_time': p95_time,
                        'success_rate': success_rate,
                        'sample_count': len(recent_executions)
                    },
                    detected_at=time.time()
                ))
            
            # Detect low success rate bottleneck
            if success_rate < 0.9:
                severity = (1.0 - success_rate) * 5.0  # Severity based on failure rate
                impact = 'high' if severity > 2.0 else 'medium' if severity > 1.0 else 'low'
                
                bottlenecks.append(Bottleneck(
                    type='reliability_issue',
                    component=tool_name,
                    severity=severity,
                    impact=impact,
                    description=f"Tool {tool_name} has low success rate ({success_rate:.1%})",
                    metrics={
                        'success_rate': success_rate,
                        'failure_count': sum(1 for exec in recent_executions if not exec['success']),
                        'sample_count': len(recent_executions)
                    },
                    detected_at=time.time()
                ))
        
        return bottlenecks
    
    def _analyze_resource_bottlenecks(self, cutoff_time: float) -> List[Bottleneck]:
        """Analyze resource utilization bottlenecks."""
        bottlenecks = []
        
        # Filter recent resource utilization
        recent_utilization = [
            util for util in self.resource_utilization_history 
            if util['timestamp'] >= cutoff_time
        ]
        
        if len(recent_utilization) < self.min_samples:
            return bottlenecks
        
        # Calculate average utilization
        avg_cpu = np.mean([util['cpu'] for util in recent_utilization])
        avg_memory = np.mean([util['memory'] for util in recent_utilization])
        avg_disk = np.mean([util['disk'] for util in recent_utilization])
        
        # Detect high resource utilization bottlenecks
        resource_thresholds = {'cpu': 80.0, 'memory': 85.0, 'disk': 90.0}
        
        for resource, threshold in resource_thresholds.items():
            avg_util = {'cpu': avg_cpu, 'memory': avg_memory, 'disk': avg_disk}[resource]
            
            if avg_util > threshold:
                severity = avg_util / threshold
                impact = 'high' if severity > 1.2 else 'medium' if severity > 1.1 else 'low'
                
                bottlenecks.append(Bottleneck(
                    type='resource_constraint',
                    component=resource,
                    severity=severity,
                    impact=impact,
                    description=f"High {resource} utilization ({avg_util:.1f}%)",
                    metrics={
                        'avg_utilization': avg_util,
                        'threshold': threshold,
                        'sample_count': len(recent_utilization)
                    },
                    detected_at=time.time()
                ))
        
        return bottlenecks
    
    def _analyze_workflow_stage_bottlenecks(self, cutoff_time: float) -> List[Bottleneck]:
        """Analyze workflow stage bottlenecks."""
        bottlenecks = []
        
        for stage_name, executions in self.workflow_stage_times.items():
            # Filter recent executions
            recent_executions = [
                exec for exec in executions if exec['timestamp'] >= cutoff_time
            ]
            
            if len(recent_executions) < self.min_samples:
                continue
            
            # Calculate metrics
            times = [exec['time'] for exec in recent_executions]
            success_rate = sum(1 for exec in recent_executions if exec['success']) / len(recent_executions)
            
            avg_time = np.mean(times)
            p95_time = np.percentile(times, self.threshold_percentile)
            
            # Detect slow workflow stage
            if p95_time > 30.0 or avg_time > 15.0:  # Thresholds for slow stages
                severity = max(p95_time / 15.0, avg_time / 7.5)
                impact = 'high' if severity > 3.0 else 'medium' if severity > 1.5 else 'low'
                
                bottlenecks.append(Bottleneck(
                    type='workflow_stage',
                    component=stage_name,
                    severity=severity,
                    impact=impact,
                    description=f"Workflow stage {stage_name} has slow execution (avg: {avg_time:.2f}s, p95: {p95_time:.2f}s)",
                    metrics={
                        'avg_time': avg_time,
                        'p95_time': p95_time,
                        'success_rate': success_rate,
                        'sample_count': len(recent_executions)
                    },
                    detected_at=time.time()
                ))
        
        return bottlenecks
    
    def _initialize_optimization_templates(self) -> Dict[str, List[Dict[str, Any]]]:
        """Initialize optimization recommendation templates."""
        return {
            'slow_tool': [
                {
                    'type': 'parallel_processing',
                    'description': 'Implement parallel processing for tool execution',
                    'expected_improvement': 40.0,
                    'implementation_effort': 'medium',
                    'priority': 'high',
                    'actions': [
                        'Analyze tool for parallelization opportunities',
                        'Implement async/await patterns',
                        'Add concurrent execution support'
                    ]
                },
                {
                    'type': 'caching',
                    'description': 'Implement caching for frequently used tool results',
                    'expected_improvement': 60.0,
                    'implementation_effort': 'low',
                    'priority': 'high',
                    'actions': [
                        'Identify cacheable operations',
                        'Implement cache layer',
                        'Add cache invalidation logic'
                    ]
                },
                {
                    'type': 'algorithm_change',
                    'description': 'Optimize tool algorithm for better performance',
                    'expected_improvement': 50.0,
                    'implementation_effort': 'high',
                    'priority': 'medium',
                    'actions': [
                        'Profile tool execution',
                        'Identify algorithmic bottlenecks',
                        'Implement optimized algorithms'
                    ]
                }
            ],
            'resource_constraint': [
                {
                    'type': 'resource_scaling',
                    'description': 'Scale up system resources',
                    'expected_improvement': 30.0,
                    'implementation_effort': 'low',
                    'priority': 'high',
                    'actions': [
                        'Increase CPU/memory allocation',
                        'Optimize resource usage',
                        'Monitor resource efficiency'
                    ]
                },
                {
                    'type': 'load_balancing',
                    'description': 'Distribute workload across multiple instances',
                    'expected_improvement': 50.0,
                    'implementation_effort': 'high',
                    'priority': 'medium',
                    'actions': [
                        'Implement load balancing',
                        'Add horizontal scaling',
                        'Optimize resource distribution'
                    ]
                }
            ],
            'workflow_stage': [
                {
                    'type': 'stage_optimization',
                    'description': 'Optimize workflow stage execution',
                    'expected_improvement': 35.0,
                    'implementation_effort': 'medium',
                    'priority': 'high',
                    'actions': [
                        'Analyze stage dependencies',
                        'Implement stage parallelization',
                        'Optimize stage transitions'
                    ]
                }
            ]
        }
    
    def _customize_optimization(self, template: Dict[str, Any], bottleneck: Bottleneck) -> Optimization:
        """Customize optimization template for specific bottleneck."""
        return Optimization(
            type=template['type'],
            target=bottleneck.component,
            description=template['description'].replace('tool', bottleneck.component),
            expected_improvement=template['expected_improvement'],
            implementation_effort=template['implementation_effort'],
            priority=template['priority'],
            specific_actions=[
                action.replace('tool', bottleneck.component) 
                for action in template['actions']
            ]
        )
    
    def _calculate_hourly_averages(self, timestamped_values: List[Tuple[float, float]]) -> List[float]:
        """Calculate hourly averages from timestamped values."""
        if not timestamped_values:
            return []
        
        # Sort by timestamp
        timestamped_values.sort(key=lambda x: x[0])
        
        # Group by hour
        hourly_data = defaultdict(list)
        for timestamp, value in timestamped_values:
            hour = int(timestamp // 3600)
            hourly_data[hour].append(value)
        
        # Calculate averages
        hourly_averages = []
        for hour in sorted(hourly_data.keys()):
            hourly_averages.append(np.mean(hourly_data[hour]))
        
        return hourly_averages 