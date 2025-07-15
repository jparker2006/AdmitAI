"""Monitoring infrastructure for workflow performance and resource management.

This package provides comprehensive monitoring capabilities for essay workflows including:
- Real-time performance metrics collection
- Intelligent resource allocation and management
- Bottleneck detection and optimization recommendations
- Analytics dashboard for performance insights
"""

from .workflow_metrics import WorkflowMetrics, PerformanceMetric, PerformanceReport
from .resource_manager import ResourceManager, ResourceUtilization, ScalingRecommendation
from .bottleneck_detector import BottleneckDetector, Bottleneck, Optimization
from .analytics_dashboard import AnalyticsDashboard, DashboardData, SystemStatus

__all__ = [
    "WorkflowMetrics",
    "PerformanceMetric", 
    "PerformanceReport",
    "ResourceManager",
    "ResourceUtilization",
    "ScalingRecommendation",
    "BottleneckDetector",
    "Bottleneck",
    "Optimization",
    "AnalyticsDashboard",
    "DashboardData",
    "SystemStatus",
] 