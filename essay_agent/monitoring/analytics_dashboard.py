"""Analytics dashboard for workflow performance visualization and reporting.

This module provides comprehensive performance analytics including:
- Real-time system status dashboard
- Performance trend visualization
- Resource utilization analytics
- Bottleneck reporting and recommendations
"""

import json
import time
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

import numpy as np

from .workflow_metrics import WorkflowMetrics, PerformanceReport
from .resource_manager import ResourceManager, ResourceUtilization
from .bottleneck_detector import BottleneckDetector, Bottleneck


@dataclass
class SystemStatus:
    """Current system status summary."""
    status: str  # 'healthy', 'warning', 'critical'
    active_workflows: int
    total_processed: int
    avg_processing_time: float
    success_rate: float
    resource_utilization: Dict[str, float]
    current_bottlenecks: List[str]
    last_updated: float


@dataclass
class DashboardData:
    """Complete dashboard data structure."""
    system_status: SystemStatus
    performance_metrics: PerformanceReport
    resource_analytics: Dict[str, Any]
    bottleneck_analysis: List[Bottleneck]
    trend_data: Dict[str, List[float]]
    recommendations: List[str]
    alerts: List[Dict[str, Any]]
    generated_at: float


class AnalyticsDashboard:
    """Comprehensive analytics dashboard for workflow monitoring."""
    
    def __init__(self, metrics: WorkflowMetrics, resource_manager: ResourceManager, 
                 bottleneck_detector: BottleneckDetector):
        """Initialize analytics dashboard.
        
        Args:
            metrics: WorkflowMetrics instance for performance data
            resource_manager: ResourceManager for resource analytics
            bottleneck_detector: BottleneckDetector for bottleneck analysis
        """
        self.metrics = metrics
        self.resource_manager = resource_manager
        self.bottleneck_detector = bottleneck_detector
        
        # Dashboard cache
        self._last_update = 0
        self._cached_dashboard: Optional[DashboardData] = None
        
        # Alert thresholds
        self.alert_thresholds = {
            'success_rate': 0.9,
            'avg_processing_time': 60.0,
            'cpu_utilization': 0.8,
            'memory_utilization': 0.85,
            'disk_utilization': 0.9
        }
    
    def generate_dashboard_data(self, force_refresh: bool = False) -> DashboardData:
        """Generate comprehensive dashboard data.
        
        Args:
            force_refresh: Force refresh of cached data
            
        Returns:
            DashboardData: Complete dashboard information
        """
        current_time = time.time()
        
        # Use cache if recent enough (30 seconds) and not forcing refresh
        if (not force_refresh and self._cached_dashboard and 
            current_time - self._last_update < 30):
            return self._cached_dashboard
        
        # Generate system status
        system_status = self._generate_system_status()
        
        # Get performance metrics
        performance_metrics = self.metrics.get_performance_summary()
        
        # Get resource analytics
        resource_analytics = self._generate_resource_analytics()
        
        # Get bottleneck analysis
        bottleneck_analysis = self.bottleneck_detector.analyze_performance()
        
        # Get trend data
        trend_data = self._generate_trend_data()
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            system_status, performance_metrics, bottleneck_analysis
        )
        
        # Generate alerts
        alerts = self._generate_alerts(system_status, performance_metrics)
        
        dashboard_data = DashboardData(
            system_status=system_status,
            performance_metrics=performance_metrics,
            resource_analytics=resource_analytics,
            bottleneck_analysis=bottleneck_analysis,
            trend_data=trend_data,
            recommendations=recommendations,
            alerts=alerts,
            generated_at=current_time
        )
        
        # Cache the data
        self._cached_dashboard = dashboard_data
        self._last_update = current_time
        
        return dashboard_data
    
    def get_real_time_metrics(self) -> Dict[str, Any]:
        """Get real-time metrics for dashboard updates."""
        resource_util = self.resource_manager.get_resource_utilization()
        
        return {
            'timestamp': time.time(),
            'active_workflows': len(self.resource_manager.active_allocations),
            'cpu_percent': resource_util.cpu_percent,
            'memory_percent': resource_util.memory_percent,
            'disk_percent': resource_util.disk_percent,
            'total_processed': self.metrics.get_total_processed(),
            'avg_processing_time': self.metrics.get_avg_processing_time()
        }
    
    def export_report(self, format: str = 'json', time_window: int = 3600) -> str:
        """Export comprehensive performance report.
        
        Args:
            format: Export format ('json', 'html', 'csv')
            time_window: Time window for report in seconds
            
        Returns:
            str: Formatted report
        """
        dashboard_data = self.generate_dashboard_data(force_refresh=True)
        
        if format == 'json':
            return self._export_json_report(dashboard_data)
        elif format == 'html':
            return self._export_html_report(dashboard_data)
        elif format == 'csv':
            return self._export_csv_report(dashboard_data)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get concise performance summary."""
        dashboard_data = self.generate_dashboard_data()
        
        return {
            'status': dashboard_data.system_status.status,
            'active_workflows': dashboard_data.system_status.active_workflows,
            'success_rate': dashboard_data.system_status.success_rate,
            'avg_processing_time': dashboard_data.system_status.avg_processing_time,
            'cpu_utilization': dashboard_data.system_status.resource_utilization.get('cpu', 0),
            'memory_utilization': dashboard_data.system_status.resource_utilization.get('memory', 0),
            'bottleneck_count': len(dashboard_data.bottleneck_analysis),
            'alert_count': len(dashboard_data.alerts),
            'last_updated': dashboard_data.system_status.last_updated
        }
    
    def _generate_system_status(self) -> SystemStatus:
        """Generate current system status."""
        # Get basic metrics
        resource_util = self.resource_manager.get_resource_utilization()
        active_workflows = len(self.resource_manager.active_allocations)
        total_processed = self.metrics.get_total_processed()
        avg_processing_time = self.metrics.get_avg_processing_time()
        
        # Calculate success rate
        performance_report = self.metrics.get_performance_summary()
        success_rate = (performance_report.successful_workflows / 
                       max(performance_report.total_workflows, 1))
        
        # Get current bottlenecks
        bottlenecks = self.bottleneck_detector.get_current_bottlenecks()
        current_bottlenecks = [b.description for b in bottlenecks[:5]]  # Top 5
        
        # Determine overall status
        status = self._determine_system_status(
            resource_util, success_rate, avg_processing_time, bottlenecks
        )
        
        return SystemStatus(
            status=status,
            active_workflows=active_workflows,
            total_processed=total_processed,
            avg_processing_time=avg_processing_time,
            success_rate=success_rate,
            resource_utilization={
                'cpu': resource_util.cpu_percent / 100.0,
                'memory': resource_util.memory_percent / 100.0,
                'disk': resource_util.disk_percent / 100.0
            },
            current_bottlenecks=current_bottlenecks,
            last_updated=time.time()
        )
    
    def _generate_resource_analytics(self) -> Dict[str, Any]:
        """Generate resource utilization analytics."""
        resource_util = self.resource_manager.get_resource_utilization()
        allocation_summary = self.resource_manager.get_allocation_summary()
        scaling_recommendation = self.resource_manager.suggest_scaling()
        
        # Calculate resource efficiency
        efficiency = {
            'cpu': min(resource_util.cpu_percent / 80.0, 1.0),  # Target 80% utilization
            'memory': min(resource_util.memory_percent / 85.0, 1.0),  # Target 85% utilization
            'disk': min(resource_util.disk_percent / 70.0, 1.0)  # Target 70% utilization
        }
        
        return {
            'current_utilization': {
                'cpu': resource_util.cpu_percent,
                'memory': resource_util.memory_percent,
                'disk': resource_util.disk_percent
            },
            'allocation_summary': allocation_summary,
            'scaling_recommendation': asdict(scaling_recommendation),
            'efficiency_scores': efficiency,
            'capacity_prediction': self.resource_manager.predict_capacity(50)  # Predict for 50 workflows
        }
    
    def _generate_trend_data(self) -> Dict[str, List[float]]:
        """Generate performance trend data."""
        # Get performance trends from metrics
        performance_trends = self.metrics.get_performance_trends()
        
        # Get bottleneck trends
        bottleneck_trends = self.bottleneck_detector.get_performance_trends()
        
        # Combine trends
        trend_data = {
            'workflow_times': performance_trends.get('execution_times', []),
            'success_rates': performance_trends.get('success_rates', []),
            'tool_performance': bottleneck_trends
        }
        
        return trend_data
    
    def _generate_recommendations(self, system_status: SystemStatus, 
                                performance_metrics: PerformanceReport,
                                bottlenecks: List[Bottleneck]) -> List[str]:
        """Generate optimization recommendations."""
        recommendations = []
        
        # System status recommendations
        if system_status.status == 'critical':
            recommendations.append("🚨 System is in critical state - immediate attention required")
        elif system_status.status == 'warning':
            recommendations.append("⚠️ System performance is degraded - review bottlenecks")
        
        # Success rate recommendations
        if system_status.success_rate < self.alert_thresholds['success_rate']:
            recommendations.append(f"📉 Success rate is low ({system_status.success_rate:.1%}) - investigate failing workflows")
        
        # Processing time recommendations
        if system_status.avg_processing_time > self.alert_thresholds['avg_processing_time']:
            recommendations.append(f"⏱️ Average processing time is high ({system_status.avg_processing_time:.1f}s) - optimize slow tools")
        
        # Resource utilization recommendations
        if system_status.resource_utilization['cpu'] > self.alert_thresholds['cpu_utilization']:
            recommendations.append("🖥️ High CPU utilization - consider scaling or optimization")
        
        if system_status.resource_utilization['memory'] > self.alert_thresholds['memory_utilization']:
            recommendations.append("💾 High memory utilization - monitor for memory leaks")
        
        # Bottleneck recommendations
        if bottlenecks:
            high_impact_bottlenecks = [b for b in bottlenecks if b.impact == 'high']
            if high_impact_bottlenecks:
                recommendations.append(f"🔧 {len(high_impact_bottlenecks)} high-impact bottlenecks detected - prioritize optimization")
        
        # Add specific optimization recommendations
        optimizations = self.bottleneck_detector.suggest_optimizations(bottlenecks[:3])  # Top 3
        for opt in optimizations[:2]:  # Top 2 recommendations
            recommendations.append(f"💡 {opt.description} (expected {opt.expected_improvement:.0f}% improvement)")
        
        return recommendations
    
    def _generate_alerts(self, system_status: SystemStatus, 
                        performance_metrics: PerformanceReport) -> List[Dict[str, Any]]:
        """Generate system alerts."""
        alerts = []
        current_time = time.time()
        
        # Success rate alert
        if system_status.success_rate < self.alert_thresholds['success_rate']:
            alerts.append({
                'type': 'performance',
                'severity': 'high',
                'message': f"Success rate dropped to {system_status.success_rate:.1%}",
                'timestamp': current_time,
                'metric': 'success_rate',
                'value': system_status.success_rate,
                'threshold': self.alert_thresholds['success_rate']
            })
        
        # Processing time alert
        if system_status.avg_processing_time > self.alert_thresholds['avg_processing_time']:
            alerts.append({
                'type': 'performance',
                'severity': 'medium',
                'message': f"Average processing time increased to {system_status.avg_processing_time:.1f}s",
                'timestamp': current_time,
                'metric': 'avg_processing_time',
                'value': system_status.avg_processing_time,
                'threshold': self.alert_thresholds['avg_processing_time']
            })
        
        # Resource utilization alerts
        for resource, utilization in system_status.resource_utilization.items():
            threshold = self.alert_thresholds.get(f'{resource}_utilization', 0.8)
            if utilization > threshold:
                alerts.append({
                    'type': 'resource',
                    'severity': 'high' if utilization > 0.95 else 'medium',
                    'message': f"{resource.upper()} utilization is {utilization:.1%}",
                    'timestamp': current_time,
                    'metric': f'{resource}_utilization',
                    'value': utilization,
                    'threshold': threshold
                })
        
        return alerts
    
    def _determine_system_status(self, resource_util: ResourceUtilization, 
                               success_rate: float, avg_processing_time: float,
                               bottlenecks: List[Bottleneck]) -> str:
        """Determine overall system status."""
        # Critical conditions
        if (resource_util.cpu_percent > 95 or 
            resource_util.memory_percent > 95 or
            success_rate < 0.8):
            return 'critical'
        
        # Warning conditions
        if (resource_util.cpu_percent > 80 or 
            resource_util.memory_percent > 85 or
            success_rate < 0.9 or
            avg_processing_time > 60 or
            len([b for b in bottlenecks if b.impact == 'high']) > 0):
            return 'warning'
        
        return 'healthy'
    
    def _export_json_report(self, dashboard_data: DashboardData) -> str:
        """Export report as JSON."""
        return json.dumps(asdict(dashboard_data), indent=2, default=str)
    
    def _export_html_report(self, dashboard_data: DashboardData) -> str:
        """Export report as HTML."""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Essay Agent Performance Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .status-healthy {{ color: green; }}
                .status-warning {{ color: orange; }}
                .status-critical {{ color: red; }}
                .metric {{ margin: 10px 0; }}
                .bottleneck {{ background: #f0f0f0; padding: 10px; margin: 5px 0; }}
                .recommendation {{ background: #e8f4f8; padding: 10px; margin: 5px 0; }}
            </style>
        </head>
        <body>
            <h1>Essay Agent Performance Report</h1>
            <p>Generated at: {datetime.fromtimestamp(dashboard_data.generated_at).strftime('%Y-%m-%d %H:%M:%S')}</p>
            
            <h2>System Status</h2>
            <div class="status-{dashboard_data.system_status.status}">
                <strong>Status: {dashboard_data.system_status.status.upper()}</strong>
            </div>
            
            <h2>Performance Metrics</h2>
            <div class="metric">Active Workflows: {dashboard_data.system_status.active_workflows}</div>
            <div class="metric">Success Rate: {dashboard_data.system_status.success_rate:.1%}</div>
            <div class="metric">Avg Processing Time: {dashboard_data.system_status.avg_processing_time:.2f}s</div>
            
            <h2>Resource Utilization</h2>
            <div class="metric">CPU: {dashboard_data.system_status.resource_utilization['cpu']:.1%}</div>
            <div class="metric">Memory: {dashboard_data.system_status.resource_utilization['memory']:.1%}</div>
            <div class="metric">Disk: {dashboard_data.system_status.resource_utilization['disk']:.1%}</div>
            
            <h2>Bottlenecks</h2>
            {''.join(f'<div class="bottleneck">{b.description}</div>' for b in dashboard_data.bottleneck_analysis[:5])}
            
            <h2>Recommendations</h2>
            {''.join(f'<div class="recommendation">{rec}</div>' for rec in dashboard_data.recommendations)}
        </body>
        </html>
        """
        return html
    
    def _export_csv_report(self, dashboard_data: DashboardData) -> str:
        """Export report as CSV."""
        lines = [
            "Metric,Value",
            f"Status,{dashboard_data.system_status.status}",
            f"Active Workflows,{dashboard_data.system_status.active_workflows}",
            f"Success Rate,{dashboard_data.system_status.success_rate:.3f}",
            f"Avg Processing Time,{dashboard_data.system_status.avg_processing_time:.2f}",
            f"CPU Utilization,{dashboard_data.system_status.resource_utilization['cpu']:.3f}",
            f"Memory Utilization,{dashboard_data.system_status.resource_utilization['memory']:.3f}",
            f"Disk Utilization,{dashboard_data.system_status.resource_utilization['disk']:.3f}",
            f"Bottleneck Count,{len(dashboard_data.bottleneck_analysis)}",
            f"Alert Count,{len(dashboard_data.alerts)}"
        ]
        return '\n'.join(lines) 