"""Intelligent resource allocation and management for workflow orchestration.

This module provides comprehensive resource management capabilities including:
- CPU and memory allocation tracking
- Resource limit enforcement
- Dynamic resource scaling recommendations
- Resource utilization monitoring
"""

import asyncio
import psutil
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from collections import defaultdict

import numpy as np


@dataclass
class ResourceUtilization:
    """Current system resource utilization."""
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    active_workflows: int
    timestamp: float


@dataclass
class ResourceAllocation:
    """Resource allocation for a specific workflow."""
    workflow_id: str
    cpu_allocation: float
    memory_allocation: float
    disk_allocation: float
    allocated_at: float
    estimated_duration: float


@dataclass
class ScalingRecommendation:
    """Recommendation for resource scaling."""
    action: str  # 'scale_up', 'scale_down', 'maintain'
    resource_type: str  # 'cpu', 'memory', 'disk'
    current_utilization: float
    target_utilization: float
    reasoning: str
    urgency: str  # 'low', 'medium', 'high'


class ResourceManager:
    """Intelligent resource allocation and management system."""
    
    def __init__(self, cpu_limit: float = 0.8, memory_limit: float = 0.8, 
                 disk_limit: float = 0.9):
        """Initialize resource manager with configurable limits.
        
        Args:
            cpu_limit: Maximum CPU utilization (0.0-1.0)
            memory_limit: Maximum memory utilization (0.0-1.0)
            disk_limit: Maximum disk utilization (0.0-1.0)
        """
        self.cpu_limit = cpu_limit
        self.memory_limit = memory_limit
        self.disk_limit = disk_limit
        
        # Active resource allocations
        self.active_allocations: Dict[str, ResourceAllocation] = {}
        
        # Resource usage history
        self.utilization_history: List[ResourceUtilization] = []
        
        # Default resource requirements for different workflow types
        self.default_requirements = {
            'essay_workflow': {'cpu': 0.1, 'memory': 0.05, 'disk': 0.01},
            'batch_workflow': {'cpu': 0.2, 'memory': 0.1, 'disk': 0.02},
            'analysis_workflow': {'cpu': 0.15, 'memory': 0.08, 'disk': 0.015}
        }
        
        # Start monitoring task
        self._monitoring_task = None
        self._start_monitoring()
    
    async def allocate_resources(self, workflow_id: str, 
                               resource_requirements: Dict[str, float]) -> bool:
        """Allocate resources for a workflow.
        
        Args:
            workflow_id: Unique identifier for the workflow
            resource_requirements: Dict with 'cpu', 'memory', 'disk' requirements
            
        Returns:
            bool: True if allocation successful, False if insufficient resources
        """
        # Get current resource utilization
        current_usage = await self._get_current_utilization()
        
        # Calculate required resources
        cpu_required = resource_requirements.get('cpu', 0.1)
        memory_required = resource_requirements.get('memory', 0.05)
        disk_required = resource_requirements.get('disk', 0.01)
        
        # Check if allocation would exceed limits
        if (current_usage.cpu_percent / 100.0 + cpu_required) > self.cpu_limit:
            print(f"🚫 CPU limit exceeded for workflow {workflow_id}")
            return False
        
        if (current_usage.memory_percent / 100.0 + memory_required) > self.memory_limit:
            print(f"🚫 Memory limit exceeded for workflow {workflow_id}")
            return False
        
        if (current_usage.disk_percent / 100.0 + disk_required) > self.disk_limit:
            print(f"🚫 Disk limit exceeded for workflow {workflow_id}")
            return False
        
        # Allocate resources
        allocation = ResourceAllocation(
            workflow_id=workflow_id,
            cpu_allocation=cpu_required,
            memory_allocation=memory_required,
            disk_allocation=disk_required,
            allocated_at=time.time(),
            estimated_duration=resource_requirements.get('estimated_duration', 60.0)
        )
        
        self.active_allocations[workflow_id] = allocation
        
        print(f"✅ Resources allocated for workflow {workflow_id}: "
              f"CPU={cpu_required:.2f}, Memory={memory_required:.2f}, Disk={disk_required:.2f}")
        
        return True
    
    async def release_resources(self, workflow_id: str) -> None:
        """Release resources for a completed workflow.
        
        Args:
            workflow_id: Unique identifier for the workflow
        """
        if workflow_id in self.active_allocations:
            allocation = self.active_allocations.pop(workflow_id)
            print(f"🔄 Resources released for workflow {workflow_id}")
        else:
            print(f"⚠️  Warning: No allocation found for workflow {workflow_id}")
    
    def get_resource_utilization(self) -> ResourceUtilization:
        """Get current resource utilization.
        
        Returns:
            ResourceUtilization: Current system resource usage
        """
        # Get system resource usage directly (synchronous)
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory_percent = psutil.virtual_memory().percent
        disk_percent = psutil.disk_usage('/').percent
        
        utilization = ResourceUtilization(
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            disk_percent=disk_percent,
            active_workflows=len(self.active_allocations),
            timestamp=time.time()
        )
        
        # Add to history
        self.utilization_history.append(utilization)
        
        # Keep only last 1000 entries
        if len(self.utilization_history) > 1000:
            self.utilization_history.pop(0)
        
        return utilization
    
    async def _get_current_utilization(self) -> ResourceUtilization:
        """Get current system resource utilization."""
        # Get system resource usage
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory_percent = psutil.virtual_memory().percent
        disk_percent = psutil.disk_usage('/').percent
        
        utilization = ResourceUtilization(
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            disk_percent=disk_percent,
            active_workflows=len(self.active_allocations),
            timestamp=time.time()
        )
        
        # Add to history
        self.utilization_history.append(utilization)
        
        # Keep only last 1000 entries
        if len(self.utilization_history) > 1000:
            self.utilization_history.pop(0)
        
        return utilization
    
    def suggest_scaling(self) -> ScalingRecommendation:
        """Suggest resource scaling based on current utilization.
        
        Returns:
            ScalingRecommendation: Recommendation for resource scaling
        """
        if not self.utilization_history:
            return ScalingRecommendation(
                action='maintain',
                resource_type='all',
                current_utilization=0.0,
                target_utilization=0.5,
                reasoning="No historical data available",
                urgency='low'
            )
        
        # Get recent utilization (last 10 minutes)
        recent_time = time.time() - 600
        recent_utilization = [
            u for u in self.utilization_history 
            if u.timestamp >= recent_time
        ]
        
        if not recent_utilization:
            recent_utilization = self.utilization_history[-10:]
        
        # Calculate average utilization
        avg_cpu = np.mean([u.cpu_percent for u in recent_utilization]) / 100.0
        avg_memory = np.mean([u.memory_percent for u in recent_utilization]) / 100.0
        avg_disk = np.mean([u.disk_percent for u in recent_utilization]) / 100.0
        
        # Determine scaling recommendations
        recommendations = []
        
        # CPU scaling
        if avg_cpu > 0.9:
            recommendations.append(ScalingRecommendation(
                action='scale_up',
                resource_type='cpu',
                current_utilization=avg_cpu,
                target_utilization=0.7,
                reasoning="High CPU utilization detected",
                urgency='high'
            ))
        elif avg_cpu < 0.3:
            recommendations.append(ScalingRecommendation(
                action='scale_down',
                resource_type='cpu',
                current_utilization=avg_cpu,
                target_utilization=0.5,
                reasoning="Low CPU utilization detected",
                urgency='low'
            ))
        
        # Memory scaling
        if avg_memory > 0.9:
            recommendations.append(ScalingRecommendation(
                action='scale_up',
                resource_type='memory',
                current_utilization=avg_memory,
                target_utilization=0.7,
                reasoning="High memory utilization detected",
                urgency='high'
            ))
        elif avg_memory < 0.3:
            recommendations.append(ScalingRecommendation(
                action='scale_down',
                resource_type='memory',
                current_utilization=avg_memory,
                target_utilization=0.5,
                reasoning="Low memory utilization detected",
                urgency='low'
            ))
        
        # Disk scaling
        if avg_disk > 0.95:
            recommendations.append(ScalingRecommendation(
                action='scale_up',
                resource_type='disk',
                current_utilization=avg_disk,
                target_utilization=0.8,
                reasoning="High disk utilization detected",
                urgency='high'
            ))
        
        # Return highest priority recommendation
        if recommendations:
            # Sort by urgency (high -> medium -> low)
            urgency_order = {'high': 3, 'medium': 2, 'low': 1}
            recommendations.sort(key=lambda x: urgency_order.get(x.urgency, 0), reverse=True)
            return recommendations[0]
        
        # No scaling needed
        return ScalingRecommendation(
            action='maintain',
            resource_type='all',
            current_utilization=max(avg_cpu, avg_memory, avg_disk),
            target_utilization=0.6,
            reasoning="Resource utilization is optimal",
            urgency='low'
        )
    
    def get_allocation_summary(self) -> Dict[str, Any]:
        """Get summary of current resource allocations.
        
        Returns:
            Dict with allocation summary information
        """
        total_cpu = sum(alloc.cpu_allocation for alloc in self.active_allocations.values())
        total_memory = sum(alloc.memory_allocation for alloc in self.active_allocations.values())
        total_disk = sum(alloc.disk_allocation for alloc in self.active_allocations.values())
        
        return {
            'active_workflows': len(self.active_allocations),
            'total_cpu_allocated': total_cpu,
            'total_memory_allocated': total_memory,
            'total_disk_allocated': total_disk,
            'cpu_utilization_percent': total_cpu / self.cpu_limit * 100,
            'memory_utilization_percent': total_memory / self.memory_limit * 100,
            'disk_utilization_percent': total_disk / self.disk_limit * 100
        }
    
    def predict_capacity(self, workflow_count: int, workflow_type: str = 'essay_workflow') -> Dict[str, Any]:
        """Predict resource capacity for a given number of workflows.
        
        Args:
            workflow_count: Number of workflows to predict capacity for
            workflow_type: Type of workflow (affects resource requirements)
            
        Returns:
            Dict with capacity prediction information
        """
        requirements = self.default_requirements.get(workflow_type, 
                                                   self.default_requirements['essay_workflow'])
        
        total_cpu_needed = workflow_count * requirements['cpu']
        total_memory_needed = workflow_count * requirements['memory']
        total_disk_needed = workflow_count * requirements['disk']
        
        current_usage = self.get_resource_utilization()
        available_cpu = self.cpu_limit - (current_usage.cpu_percent / 100.0)
        available_memory = self.memory_limit - (current_usage.memory_percent / 100.0)
        available_disk = self.disk_limit - (current_usage.disk_percent / 100.0)
        
        can_accommodate = (
            total_cpu_needed <= available_cpu and
            total_memory_needed <= available_memory and
            total_disk_needed <= available_disk
        )
        
        return {
            'workflow_count': workflow_count,
            'workflow_type': workflow_type,
            'can_accommodate': can_accommodate,
            'resource_requirements': {
                'cpu': total_cpu_needed,
                'memory': total_memory_needed,
                'disk': total_disk_needed
            },
            'available_resources': {
                'cpu': available_cpu,
                'memory': available_memory,
                'disk': available_disk
            },
            'bottleneck_resource': self._identify_bottleneck_resource(
                total_cpu_needed, total_memory_needed, total_disk_needed,
                available_cpu, available_memory, available_disk
            )
        }
    
    def _identify_bottleneck_resource(self, cpu_needed: float, memory_needed: float, 
                                    disk_needed: float, cpu_available: float, 
                                    memory_available: float, disk_available: float) -> str:
        """Identify which resource is the bottleneck."""
        cpu_ratio = cpu_needed / cpu_available if cpu_available > 0 else float('inf')
        memory_ratio = memory_needed / memory_available if memory_available > 0 else float('inf')
        disk_ratio = disk_needed / disk_available if disk_available > 0 else float('inf')
        
        if cpu_ratio >= memory_ratio and cpu_ratio >= disk_ratio:
            return 'cpu'
        elif memory_ratio >= disk_ratio:
            return 'memory'
        else:
            return 'disk'
    
    def _start_monitoring(self) -> None:
        """Start background monitoring task."""
        async def monitor():
            while True:
                await self._get_current_utilization()
                await asyncio.sleep(30)  # Update every 30 seconds
        
        # Start monitoring in background
        try:
            loop = asyncio.get_event_loop()
            self._monitoring_task = loop.create_task(monitor())
        except RuntimeError:
            # No event loop running, monitoring will be manual
            pass
    
    def cleanup(self) -> None:
        """Clean up resources and stop monitoring."""
        if self._monitoring_task:
            self._monitoring_task.cancel()
        
        # Release all active allocations
        for workflow_id in list(self.active_allocations.keys()):
            asyncio.create_task(self.release_resources(workflow_id))
    
    def __del__(self):
        """Cleanup on deletion."""
        self.cleanup() 