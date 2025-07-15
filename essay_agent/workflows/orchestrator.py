"""Advanced workflow orchestration with comprehensive monitoring and resource management.

This module provides the central orchestration engine that coordinates workflow execution
with real-time monitoring, intelligent resource allocation, and performance optimization.
"""

import asyncio
import time
import uuid
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path

from ..executor import EssayExecutor
from ..monitoring import (
    WorkflowMetrics, 
    ResourceManager, 
    BottleneckDetector, 
    AnalyticsDashboard,
    SystemStatus,
    DashboardData
)
from ..utils.logging import tool_trace


@dataclass
class WorkflowConfig:
    """Configuration for workflow execution."""
    type: str  # 'essay_workflow', 'batch_workflow', 'analysis_workflow'
    prompt: str
    user_profile: Dict[str, Any]
    college_id: Optional[str] = None
    word_limit: int = 650
    resources: Optional[Dict[str, float]] = None
    priority: str = 'normal'  # 'low', 'normal', 'high'
    timeout: int = 300  # seconds


@dataclass
class WorkflowResult:
    """Result of workflow execution."""
    workflow_id: str
    success: bool
    result: Dict[str, Any]
    execution_time: float
    error_message: Optional[str] = None
    resource_usage: Optional[Dict[str, float]] = None
    metadata: Optional[Dict[str, Any]] = None


class ResourceUnavailableError(Exception):
    """Raised when insufficient resources are available for workflow execution."""
    pass


class MonitoringError(Exception):
    """Raised when monitoring operations fail."""
    pass


class OrchestrationError(Exception):
    """Raised when workflow orchestration fails."""
    pass


class WorkflowOrchestrator:
    """Advanced workflow orchestration with monitoring and resource management."""
    
    def __init__(self, max_concurrent_workflows: int = 10, 
                 resource_limits: Optional[Dict[str, Any]] = None,
                 metrics_store: Optional[str] = None):
        """Initialize workflow orchestrator.
        
        Args:
            max_concurrent_workflows: Maximum number of concurrent workflows
            resource_limits: Resource limits for CPU, memory, disk
            metrics_store: Optional path for persistent metrics storage
        """
        self.max_concurrent_workflows = max_concurrent_workflows
        
        # Initialize monitoring components
        self.metrics = WorkflowMetrics(metrics_store)
        self.resource_manager = ResourceManager(
            cpu_limit=resource_limits.get('cpu', 0.8) if resource_limits else 0.8,
            memory_limit=resource_limits.get('memory', 0.8) if resource_limits else 0.8,
            disk_limit=resource_limits.get('disk', 0.9) if resource_limits else 0.9
        )
        self.bottleneck_detector = BottleneckDetector()
        self.dashboard = AnalyticsDashboard(
            self.metrics, self.resource_manager, self.bottleneck_detector
        )
        
        # Workflow execution
        self.executor = EssayExecutor(mode="advanced")
        self.active_workflows: Dict[str, asyncio.Task] = {}
        self.workflow_queue: asyncio.Queue = asyncio.Queue()
        
        # Start background tasks
        self._processing_task: Optional[asyncio.Task] = None
        self._monitoring_task: Optional[asyncio.Task] = None
        self._start_background_tasks()
    
    async def execute_workflow(self, workflow_config: WorkflowConfig) -> WorkflowResult:
        """Execute a single workflow with full monitoring.
        
        Args:
            workflow_config: Configuration for the workflow
            
        Returns:
            WorkflowResult: Result of workflow execution
        """
        workflow_id = str(uuid.uuid4())
        
        try:
            # Check resource availability
            resource_requirements = workflow_config.resources or self._get_default_resources(workflow_config.type)
            
            if not await self.resource_manager.allocate_resources(workflow_id, resource_requirements):
                raise ResourceUnavailableError(f"Insufficient resources for workflow {workflow_id}")
            
            # Record workflow start
            metadata = {
                'type': workflow_config.type,
                'priority': workflow_config.priority,
                'prompt_length': len(workflow_config.prompt),
                'college_id': workflow_config.college_id
            }
            self.metrics.record_workflow_start(workflow_id, metadata)
            
            # Execute workflow with monitoring
            start_time = time.time()
            result = await self._execute_with_monitoring(workflow_id, workflow_config)
            execution_time = time.time() - start_time
            
            # Record success
            self.metrics.record_workflow_end(workflow_id, {'success': True, 'result': result})
            
            return WorkflowResult(
                workflow_id=workflow_id,
                success=True,
                result=result,
                execution_time=execution_time,
                metadata=metadata
            )
            
        except Exception as e:
            # Record failure
            self.metrics.record_workflow_failure(workflow_id, str(e))
            
            return WorkflowResult(
                workflow_id=workflow_id,
                success=False,
                result={},
                execution_time=time.time() - start_time if 'start_time' in locals() else 0,
                error_message=str(e)
            )
            
        finally:
            # Always clean up resources
            await self.resource_manager.release_resources(workflow_id)
    
    async def submit_workflow(self, workflow_config: WorkflowConfig) -> str:
        """Submit workflow for asynchronous execution.
        
        Args:
            workflow_config: Configuration for the workflow
            
        Returns:
            str: Workflow ID for tracking
        """
        workflow_id = str(uuid.uuid4())
        
        # Add to queue
        await self.workflow_queue.put((workflow_id, workflow_config))
        
        tool_trace("start", "workflow_queue", args={'workflow_id': workflow_id, 'type': workflow_config.type})
        
        return workflow_id
    
    async def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get status of a specific workflow.
        
        Args:
            workflow_id: ID of the workflow
            
        Returns:
            Dict with workflow status information
        """
        if workflow_id in self.active_workflows:
            task = self.active_workflows[workflow_id]
            return {
                'status': 'running',
                'done': task.done(),
                'cancelled': task.cancelled(),
                'result': task.result() if task.done() and not task.cancelled() else None
            }
        else:
            return {'status': 'not_found'}
    
    async def cancel_workflow(self, workflow_id: str) -> bool:
        """Cancel a running workflow.
        
        Args:
            workflow_id: ID of the workflow to cancel
            
        Returns:
            bool: True if cancelled successfully
        """
        if workflow_id in self.active_workflows:
            task = self.active_workflows[workflow_id]
            task.cancel()
            await self.resource_manager.release_resources(workflow_id)
            del self.active_workflows[workflow_id]
            return True
        return False
    
    def get_system_status(self) -> SystemStatus:
        """Get current system status.
        
        Returns:
            SystemStatus: Current system status
        """
        return self.dashboard.generate_dashboard_data().system_status
    
    def get_dashboard_data(self) -> DashboardData:
        """Get complete dashboard data.
        
        Returns:
            DashboardData: Complete dashboard information
        """
        return self.dashboard.generate_dashboard_data()
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get concise performance summary.
        
        Returns:
            Dict: Performance summary
        """
        return self.dashboard.get_performance_summary()
    
    async def manage_resources(self) -> None:
        """Manage system resources and scaling."""
        # Get scaling recommendation
        recommendation = self.resource_manager.suggest_scaling()
        
        if recommendation.urgency == 'high':
            tool_trace("start", "resource_scaling", args={'action': recommendation.action, 'resource': recommendation.resource_type})
            
            # In a real implementation, this would trigger actual scaling
            # For now, we just log the recommendation
            print(f"🔄 Resource scaling recommended: {recommendation.action} {recommendation.resource_type}")
            print(f"   Reason: {recommendation.reasoning}")
    
    async def monitor_performance(self) -> None:
        """Monitor system performance and detect issues."""
        try:
            # Analyze bottlenecks
            bottlenecks = self.bottleneck_detector.analyze_performance()
            
            # Check for critical bottlenecks
            critical_bottlenecks = [b for b in bottlenecks if b.impact == 'high']
            if critical_bottlenecks:
                tool_trace("start", "bottleneck_alert", args={'count': len(critical_bottlenecks)})
                
                # Generate optimizations
                optimizations = self.bottleneck_detector.suggest_optimizations(critical_bottlenecks)
                
                for opt in optimizations[:2]:  # Top 2 optimizations
                    print(f"💡 Optimization suggestion: {opt.description}")
                    print(f"   Expected improvement: {opt.expected_improvement:.0f}%")
                    print(f"   Implementation effort: {opt.implementation_effort}")
        
        except Exception as e:
            raise MonitoringError(f"Performance monitoring failed: {e}")
    
    async def _execute_with_monitoring(self, workflow_id: str, 
                                     workflow_config: WorkflowConfig) -> Dict[str, Any]:
        """Execute workflow with comprehensive monitoring."""
        # Prepare execution context
        context = {
            'workflow_id': workflow_id,
            'college_id': workflow_config.college_id,
            'word_limit': workflow_config.word_limit
        }
        
        # Add resource monitoring hook
        original_record = self.metrics.record_tool_execution
        
        def monitored_record(tool_name: str, execution_time: float, success: bool, 
                           workflow_id: str = workflow_id, error_message: str = None,
                           resource_usage: Dict[str, float] = None):
            # Record in metrics
            original_record(tool_name, execution_time, success, workflow_id, error_message, resource_usage)
            
            # Record in bottleneck detector
            self.bottleneck_detector.record_tool_execution(tool_name, execution_time, success, resource_usage)
        
        # Temporarily replace record method
        self.metrics.record_tool_execution = monitored_record
        
        try:
            # Execute the workflow
            result = await self.executor.arun(workflow_config.prompt, context)
            return result
            
        finally:
            # Restore original method
            self.metrics.record_tool_execution = original_record
    
    def _get_default_resources(self, workflow_type: str) -> Dict[str, float]:
        """Get default resource requirements for workflow type."""
        defaults = {
            'essay_workflow': {'cpu': 0.1, 'memory': 0.05, 'disk': 0.01},
            'batch_workflow': {'cpu': 0.2, 'memory': 0.1, 'disk': 0.02},
            'analysis_workflow': {'cpu': 0.15, 'memory': 0.08, 'disk': 0.015}
        }
        return defaults.get(workflow_type, defaults['essay_workflow'])
    
    def _start_background_tasks(self) -> None:
        """Start background monitoring and processing tasks."""
        try:
            loop = asyncio.get_event_loop()
            
            # Start workflow processing task
            self._processing_task = loop.create_task(self._process_workflow_queue())
            
            # Start monitoring task
            self._monitoring_task = loop.create_task(self._background_monitoring())
            
        except RuntimeError:
            # No event loop running - tasks will be started manually
            pass
    
    async def _process_workflow_queue(self) -> None:
        """Process queued workflows."""
        while True:
            try:
                # Check if we can process more workflows
                if len(self.active_workflows) >= self.max_concurrent_workflows:
                    await asyncio.sleep(1)
                    continue
                
                # Get next workflow from queue
                try:
                    workflow_id, workflow_config = await asyncio.wait_for(
                        self.workflow_queue.get(), timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue
                
                # Start workflow execution
                task = asyncio.create_task(self.execute_workflow(workflow_config))
                self.active_workflows[workflow_id] = task
                
                # Clean up completed tasks
                await self._cleanup_completed_workflows()
                
            except Exception as e:
                print(f"⚠️  Error in workflow processing: {e}")
                await asyncio.sleep(5)
    
    async def _background_monitoring(self) -> None:
        """Background monitoring task."""
        while True:
            try:
                # Monitor performance every 30 seconds
                await self.monitor_performance()
                
                # Manage resources every 60 seconds
                await self.manage_resources()
                
                await asyncio.sleep(30)
                
            except Exception as e:
                print(f"⚠️  Error in background monitoring: {e}")
                await asyncio.sleep(60)
    
    async def _cleanup_completed_workflows(self) -> None:
        """Clean up completed workflow tasks."""
        completed_workflows = []
        
        for workflow_id, task in self.active_workflows.items():
            if task.done():
                completed_workflows.append(workflow_id)
        
        for workflow_id in completed_workflows:
            del self.active_workflows[workflow_id]
    
    async def shutdown(self) -> None:
        """Gracefully shutdown the orchestrator."""
        print("🔄 Shutting down workflow orchestrator...")
        
        # Cancel all active workflows
        for workflow_id, task in self.active_workflows.items():
            task.cancel()
            await self.resource_manager.release_resources(workflow_id)
        
        # Cancel background tasks
        if self._processing_task:
            self._processing_task.cancel()
        if self._monitoring_task:
            self._monitoring_task.cancel()
        
        # Cleanup resource manager
        self.resource_manager.cleanup()
        
        print("✅ Orchestrator shutdown complete")
    
    def __del__(self):
        """Cleanup on deletion."""
        try:
            asyncio.create_task(self.shutdown())
        except RuntimeError:
            # Event loop not running
            pass 