"""Integration tests for advanced orchestration and monitoring system.

Tests comprehensive workflow orchestration including:
- Resource-aware workflow execution
- Real-time performance monitoring
- Bottleneck detection and optimization
- Analytics dashboard functionality
"""

import asyncio
import pytest
import tempfile
import time
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from essay_agent.workflows.orchestrator import (
    WorkflowOrchestrator,
    WorkflowConfig,
    WorkflowResult,
    ResourceUnavailableError,
    MonitoringError,
    OrchestrationError
)
from essay_agent.monitoring import (
    WorkflowMetrics,
    ResourceManager,
    BottleneckDetector,
    AnalyticsDashboard,
    SystemStatus,
    DashboardData
)


class TestWorkflowOrchestrator:
    """Test suite for WorkflowOrchestrator."""
    
    @pytest.fixture
    def temp_metrics_store(self):
        """Create temporary metrics store directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @pytest.fixture
    def orchestrator(self, temp_metrics_store):
        """Create orchestrator instance for testing."""
        return WorkflowOrchestrator(
            max_concurrent_workflows=3,
            resource_limits={'cpu': 0.6, 'memory': 0.7, 'disk': 0.8},
            metrics_store=temp_metrics_store
        )
    
    @pytest.fixture
    def sample_workflow_config(self):
        """Sample workflow configuration for testing."""
        return WorkflowConfig(
            type='essay_workflow',
            prompt='Test prompt for essay writing',
            user_profile={'name': 'Test User', 'grade': 12},
            college_id='test_college',
            word_limit=650,
            priority='normal'
        )
    
    @pytest.mark.asyncio
    async def test_orchestrator_initialization(self, orchestrator):
        """Test orchestrator initialization."""
        assert orchestrator.max_concurrent_workflows == 3
        assert orchestrator.resource_manager.cpu_limit == 0.6
        assert orchestrator.resource_manager.memory_limit == 0.7
        assert orchestrator.resource_manager.disk_limit == 0.8
        assert isinstance(orchestrator.metrics, WorkflowMetrics)
        assert isinstance(orchestrator.dashboard, AnalyticsDashboard)
        
        # Clean up
        await orchestrator.shutdown()
    
    @pytest.mark.asyncio
    async def test_single_workflow_execution(self, orchestrator, sample_workflow_config):
        """Test single workflow execution."""
        try:
            # Mock the executor to return a simple result
            with patch.object(orchestrator.executor, 'arun') as mock_run:
                mock_run.return_value = {
                    'success': True,
                    'final_draft': 'Test essay content',
                    'selected_story': 'Test story',
                    'word_count': 650
                }
                
                result = await orchestrator.execute_workflow(sample_workflow_config)
                
                # Verify result
                assert result.success
                assert result.workflow_id
                assert result.execution_time > 0
                assert result.result['success']
                assert result.result['final_draft'] == 'Test essay content'
                
                # Verify metrics were recorded
                assert orchestrator.metrics.get_total_processed() > 0
                
        finally:
            await orchestrator.shutdown()
    
    @pytest.mark.asyncio
    async def test_workflow_failure_handling(self, orchestrator, sample_workflow_config):
        """Test workflow failure handling."""
        try:
            # Mock the executor to raise an exception
            with patch.object(orchestrator.executor, 'arun') as mock_run:
                mock_run.side_effect = Exception("Test execution failure")
                
                result = await orchestrator.execute_workflow(sample_workflow_config)
                
                # Verify failure was handled correctly
                assert not result.success
                assert result.error_message == "Test execution failure"
                assert result.workflow_id
                
        finally:
            await orchestrator.shutdown()
    
    @pytest.mark.asyncio
    async def test_resource_allocation_limits(self, orchestrator):
        """Test resource allocation limits."""
        try:
            # Create a high-resource workflow
            high_resource_config = WorkflowConfig(
                type='essay_workflow',
                prompt='Test prompt',
                user_profile={'name': 'Test User'},
                resources={'cpu': 0.8, 'memory': 0.9, 'disk': 0.5}  # Exceeds limits
            )
            
            # Mock resource manager to simulate resource unavailability
            with patch.object(orchestrator.resource_manager, 'allocate_resources') as mock_allocate:
                mock_allocate.return_value = False  # Simulate resource unavailable
                
                result = await orchestrator.execute_workflow(high_resource_config)
                
                # Verify resource unavailable error was handled
                assert not result.success
                assert "Insufficient resources" in result.error_message
                
        finally:
            await orchestrator.shutdown()
    
    @pytest.mark.asyncio
    async def test_async_workflow_submission(self, orchestrator, sample_workflow_config):
        """Test asynchronous workflow submission."""
        try:
            # Mock the executor for quick completion
            with patch.object(orchestrator.executor, 'arun') as mock_run:
                mock_run.return_value = {'success': True, 'final_draft': 'Test content'}
                
                # Submit workflow asynchronously
                workflow_id = await orchestrator.submit_workflow(sample_workflow_config)
                
                # Verify workflow was queued
                assert workflow_id
                assert len(workflow_id) > 0
                
                # Wait a bit for processing
                await asyncio.sleep(0.1)
                
                # Check workflow status
                status = await orchestrator.get_workflow_status(workflow_id)
                assert status['status'] in ['running', 'not_found']  # May complete quickly
                
        finally:
            await orchestrator.shutdown()
    
    @pytest.mark.asyncio
    async def test_concurrent_workflow_limits(self, orchestrator):
        """Test concurrent workflow execution limits."""
        try:
            # Mock slow executor
            async def slow_executor(*args, **kwargs):
                await asyncio.sleep(0.2)
                return {'success': True, 'final_draft': 'Test content'}
            
            with patch.object(orchestrator.executor, 'arun', side_effect=slow_executor):
                # Submit more workflows than the limit
                workflow_configs = [
                    WorkflowConfig(
                        type='essay_workflow',
                        prompt=f'Test prompt {i}',
                        user_profile={'name': f'User {i}'}
                    )
                    for i in range(5)  # More than max_concurrent_workflows=3
                ]
                
                workflow_ids = []
                for config in workflow_configs:
                    workflow_id = await orchestrator.submit_workflow(config)
                    workflow_ids.append(workflow_id)
                
                # Wait for some processing
                await asyncio.sleep(0.1)
                
                # Check that not all workflows are running simultaneously
                running_count = 0
                for workflow_id in workflow_ids:
                    status = await orchestrator.get_workflow_status(workflow_id)
                    if status['status'] == 'running':
                        running_count += 1
                
                # Should respect the concurrent limit
                assert running_count <= orchestrator.max_concurrent_workflows
                
        finally:
            await orchestrator.shutdown()
    
    @pytest.mark.asyncio
    async def test_workflow_cancellation(self, orchestrator, sample_workflow_config):
        """Test workflow cancellation."""
        try:
            # Mock slow executor
            async def slow_executor(*args, **kwargs):
                await asyncio.sleep(1.0)
                return {'success': True, 'final_draft': 'Test content'}
            
            with patch.object(orchestrator.executor, 'arun', side_effect=slow_executor):
                # Submit workflow
                workflow_id = await orchestrator.submit_workflow(sample_workflow_config)
                
                # Wait for it to start
                await asyncio.sleep(0.1)
                
                # Cancel the workflow
                cancelled = await orchestrator.cancel_workflow(workflow_id)
                
                # Verify cancellation
                assert cancelled
                
                # Check status
                status = await orchestrator.get_workflow_status(workflow_id)
                assert status['status'] == 'not_found'
                
        finally:
            await orchestrator.shutdown()
    
    def test_system_status_retrieval(self, orchestrator):
        """Test system status retrieval."""
        try:
            status = orchestrator.get_system_status()
            
            assert isinstance(status, SystemStatus)
            assert status.status in ['healthy', 'warning', 'critical']
            assert status.active_workflows >= 0
            assert status.total_processed >= 0
            assert status.avg_processing_time >= 0
            assert 0 <= status.success_rate <= 1
            assert 'cpu' in status.resource_utilization
            assert 'memory' in status.resource_utilization
            assert 'disk' in status.resource_utilization
            
        finally:
            asyncio.create_task(orchestrator.shutdown())
    
    def test_dashboard_data_generation(self, orchestrator):
        """Test dashboard data generation."""
        try:
            dashboard_data = orchestrator.get_dashboard_data()
            
            assert isinstance(dashboard_data, DashboardData)
            assert isinstance(dashboard_data.system_status, SystemStatus)
            assert hasattr(dashboard_data, 'performance_metrics')
            assert hasattr(dashboard_data, 'resource_analytics')
            assert hasattr(dashboard_data, 'bottleneck_analysis')
            assert hasattr(dashboard_data, 'trend_data')
            assert hasattr(dashboard_data, 'recommendations')
            assert hasattr(dashboard_data, 'alerts')
            assert dashboard_data.generated_at > 0
            
        finally:
            asyncio.create_task(orchestrator.shutdown())
    
    def test_performance_summary(self, orchestrator):
        """Test performance summary generation."""
        try:
            summary = orchestrator.get_performance_summary()
            
            assert isinstance(summary, dict)
            assert 'status' in summary
            assert 'active_workflows' in summary
            assert 'success_rate' in summary
            assert 'avg_processing_time' in summary
            assert 'cpu_utilization' in summary
            assert 'memory_utilization' in summary
            assert 'bottleneck_count' in summary
            assert 'alert_count' in summary
            assert 'last_updated' in summary
            
        finally:
            asyncio.create_task(orchestrator.shutdown())


class TestWorkflowMetrics:
    """Test suite for WorkflowMetrics."""
    
    @pytest.fixture
    def temp_metrics_store(self):
        """Create temporary metrics store directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @pytest.fixture
    def metrics(self, temp_metrics_store):
        """Create metrics instance for testing."""
        return WorkflowMetrics(temp_metrics_store)
    
    def test_workflow_tracking(self, metrics):
        """Test workflow execution tracking."""
        workflow_id = "test_workflow_123"
        metadata = {'type': 'essay_workflow', 'user': 'test_user'}
        
        # Record workflow start
        metrics.record_workflow_start(workflow_id, metadata)
        assert workflow_id in metrics.active_workflows
        
        # Record workflow end
        result = {'success': True, 'final_draft': 'Test content'}
        metrics.record_workflow_end(workflow_id, result)
        assert workflow_id not in metrics.active_workflows
        assert len(metrics.completed_workflows) == 1
    
    def test_tool_execution_tracking(self, metrics):
        """Test tool execution tracking."""
        tool_name = "test_tool"
        execution_time = 1.5
        success = True
        workflow_id = "test_workflow"
        
        # Record tool execution
        metrics.record_tool_execution(tool_name, execution_time, success, workflow_id)
        
        # Verify tracking
        assert tool_name in metrics.tool_metrics
        assert len(metrics.tool_metrics[tool_name]) == 1
        
        tool_metric = metrics.tool_metrics[tool_name][0]
        assert tool_metric.tool_name == tool_name
        assert tool_metric.execution_time == execution_time
        assert tool_metric.success == success
        assert tool_metric.workflow_id == workflow_id
    
    def test_performance_summary_generation(self, metrics):
        """Test performance summary generation."""
        # Add some sample data
        metrics.record_workflow_start("test_1", {'type': 'essay_workflow'})
        metrics.record_workflow_end("test_1", {'success': True})
        
        metrics.record_tool_execution("brainstorm", 2.0, True, "test_1")
        metrics.record_tool_execution("outline", 1.5, True, "test_1")
        
        # Generate summary
        summary = metrics.get_performance_summary()
        
        assert summary.total_workflows == 1
        assert summary.successful_workflows == 1
        assert summary.failed_workflows == 0
        assert summary.avg_execution_time > 0
        assert len(summary.tool_performance) == 2
        assert 'brainstorm' in summary.tool_performance
        assert 'outline' in summary.tool_performance
    
    def test_metrics_persistence(self, temp_metrics_store):
        """Test metrics persistence to storage."""
        metrics = WorkflowMetrics(temp_metrics_store)
        
        # Record some data
        workflow_id = "test_persist"
        metrics.record_workflow_start(workflow_id, {'type': 'test'})
        metrics.record_workflow_end(workflow_id, {'success': True})
        
        # Verify files were created
        metrics_dir = Path(temp_metrics_store)
        assert metrics_dir.exists()
        
        # Check for metrics files
        metrics_files = list(metrics_dir.glob("workflow_metrics_*.jsonl"))
        assert len(metrics_files) > 0


class TestResourceManager:
    """Test suite for ResourceManager."""
    
    @pytest.fixture
    def resource_manager(self):
        """Create resource manager instance for testing."""
        return ResourceManager(cpu_limit=0.7, memory_limit=0.8, disk_limit=0.9)
    
    @pytest.mark.asyncio
    async def test_resource_allocation(self, resource_manager):
        """Test resource allocation and release."""
        workflow_id = "test_workflow"
        requirements = {'cpu': 0.1, 'memory': 0.05, 'disk': 0.01}
        
        # Allocate resources
        allocated = await resource_manager.allocate_resources(workflow_id, requirements)
        assert allocated
        assert workflow_id in resource_manager.active_allocations
        
        # Release resources
        await resource_manager.release_resources(workflow_id)
        assert workflow_id not in resource_manager.active_allocations
    
    @pytest.mark.asyncio
    async def test_resource_limit_enforcement(self, resource_manager):
        """Test resource limit enforcement."""
        workflow_id = "test_workflow"
        
        # Try to allocate resources that exceed limits
        high_requirements = {'cpu': 0.9, 'memory': 0.9, 'disk': 0.95}
        
        allocated = await resource_manager.allocate_resources(workflow_id, high_requirements)
        # Should fail due to exceeding limits
        assert not allocated
        assert workflow_id not in resource_manager.active_allocations
    
    def test_resource_utilization_tracking(self, resource_manager):
        """Test resource utilization tracking."""
        utilization = resource_manager.get_resource_utilization()
        
        assert hasattr(utilization, 'cpu_percent')
        assert hasattr(utilization, 'memory_percent')
        assert hasattr(utilization, 'disk_percent')
        assert hasattr(utilization, 'active_workflows')
        assert hasattr(utilization, 'timestamp')
        
        assert 0 <= utilization.cpu_percent <= 100
        assert 0 <= utilization.memory_percent <= 100
        assert 0 <= utilization.disk_percent <= 100
    
    def test_scaling_recommendations(self, resource_manager):
        """Test scaling recommendations."""
        recommendation = resource_manager.suggest_scaling()
        
        assert hasattr(recommendation, 'action')
        assert hasattr(recommendation, 'resource_type')
        assert hasattr(recommendation, 'current_utilization')
        assert hasattr(recommendation, 'target_utilization')
        assert hasattr(recommendation, 'reasoning')
        assert hasattr(recommendation, 'urgency')
        
        assert recommendation.action in ['scale_up', 'scale_down', 'maintain']
        assert recommendation.resource_type in ['cpu', 'memory', 'disk', 'all']
        assert recommendation.urgency in ['low', 'medium', 'high']
    
    def test_capacity_prediction(self, resource_manager):
        """Test capacity prediction."""
        prediction = resource_manager.predict_capacity(10, 'essay_workflow')
        
        assert 'workflow_count' in prediction
        assert 'workflow_type' in prediction
        assert 'can_accommodate' in prediction
        assert 'resource_requirements' in prediction
        assert 'available_resources' in prediction
        assert 'bottleneck_resource' in prediction
        
        assert prediction['workflow_count'] == 10
        assert prediction['workflow_type'] == 'essay_workflow'
        assert isinstance(prediction['can_accommodate'], bool)


class TestBottleneckDetector:
    """Test suite for BottleneckDetector."""
    
    @pytest.fixture
    def detector(self):
        """Create bottleneck detector instance for testing."""
        return BottleneckDetector(threshold_percentile=95.0, min_samples=5)
    
    def test_tool_performance_recording(self, detector):
        """Test tool performance recording."""
        tool_name = "test_tool"
        
        # Record multiple executions
        for i in range(10):
            detector.record_tool_execution(tool_name, i * 0.5, True)
        
        assert tool_name in detector.tool_execution_times
        assert len(detector.tool_execution_times[tool_name]) == 10
    
    def test_bottleneck_detection(self, detector):
        """Test bottleneck detection."""
        # Record slow tool executions
        slow_tool = "slow_tool"
        for i in range(15):
            detector.record_tool_execution(slow_tool, 15.0 + i, True)  # Very slow
        
        # Record normal tool executions
        normal_tool = "normal_tool"
        for i in range(15):
            detector.record_tool_execution(normal_tool, 1.0 + i * 0.1, True)
        
        # Analyze performance
        bottlenecks = detector.analyze_performance()
        
        # Should detect the slow tool as a bottleneck
        slow_bottlenecks = [b for b in bottlenecks if b.component == slow_tool]
        assert len(slow_bottlenecks) > 0
        
        slow_bottleneck = slow_bottlenecks[0]
        assert slow_bottleneck.type == 'slow_tool'
        assert slow_bottleneck.severity > 1.0
    
    def test_optimization_suggestions(self, detector):
        """Test optimization suggestions."""
        # Create a bottleneck scenario
        tool_name = "bottleneck_tool"
        for i in range(15):
            detector.record_tool_execution(tool_name, 12.0, True)  # Slow but consistent
        
        bottlenecks = detector.analyze_performance()
        optimizations = detector.suggest_optimizations(bottlenecks)
        
        if bottlenecks:
            assert len(optimizations) > 0
            
            optimization = optimizations[0]
            assert hasattr(optimization, 'type')
            assert hasattr(optimization, 'target')
            assert hasattr(optimization, 'description')
            assert hasattr(optimization, 'expected_improvement')
            assert hasattr(optimization, 'implementation_effort')
            assert hasattr(optimization, 'priority')
            assert hasattr(optimization, 'specific_actions')
    
    def test_slow_tool_detection(self, detector):
        """Test slow tool detection."""
        # Create tool metrics
        tool_metrics = {
            'fast_tool': [0.5, 0.6, 0.7, 0.8, 0.9],
            'slow_tool': [10.0, 11.0, 12.0, 13.0, 14.0, 15.0],
            'variable_tool': [1.0, 2.0, 15.0, 1.5, 2.5]  # High variance
        }
        
        slow_tools = detector.detect_slow_tools(tool_metrics)
        
        # Should detect slow_tool and variable_tool
        assert 'slow_tool' in slow_tools
        assert 'variable_tool' in slow_tools
        assert 'fast_tool' not in slow_tools


class TestAnalyticsDashboard:
    """Test suite for AnalyticsDashboard."""
    
    @pytest.fixture
    def dashboard_components(self):
        """Create dashboard components for testing."""
        metrics = WorkflowMetrics()
        resource_manager = ResourceManager()
        detector = BottleneckDetector()
        return metrics, resource_manager, detector
    
    @pytest.fixture
    def dashboard(self, dashboard_components):
        """Create analytics dashboard instance for testing."""
        metrics, resource_manager, detector = dashboard_components
        return AnalyticsDashboard(metrics, resource_manager, detector)
    
    def test_dashboard_data_generation(self, dashboard):
        """Test dashboard data generation."""
        dashboard_data = dashboard.generate_dashboard_data()
        
        assert isinstance(dashboard_data, DashboardData)
        assert hasattr(dashboard_data, 'system_status')
        assert hasattr(dashboard_data, 'performance_metrics')
        assert hasattr(dashboard_data, 'resource_analytics')
        assert hasattr(dashboard_data, 'bottleneck_analysis')
        assert hasattr(dashboard_data, 'trend_data')
        assert hasattr(dashboard_data, 'recommendations')
        assert hasattr(dashboard_data, 'alerts')
        assert dashboard_data.generated_at > 0
    
    def test_real_time_metrics(self, dashboard):
        """Test real-time metrics retrieval."""
        metrics = dashboard.get_real_time_metrics()
        
        assert 'timestamp' in metrics
        assert 'active_workflows' in metrics
        assert 'cpu_percent' in metrics
        assert 'memory_percent' in metrics
        assert 'disk_percent' in metrics
        assert 'total_processed' in metrics
        assert 'avg_processing_time' in metrics
    
    def test_report_export(self, dashboard):
        """Test report export functionality."""
        # Test JSON export
        json_report = dashboard.export_report('json')
        assert isinstance(json_report, str)
        assert len(json_report) > 0
        
        # Test HTML export
        html_report = dashboard.export_report('html')
        assert isinstance(html_report, str)
        assert '<html>' in html_report
        
        # Test CSV export
        csv_report = dashboard.export_report('csv')
        assert isinstance(csv_report, str)
        assert 'Metric,Value' in csv_report
    
    def test_performance_summary(self, dashboard):
        """Test performance summary generation."""
        summary = dashboard.get_performance_summary()
        
        assert isinstance(summary, dict)
        assert 'status' in summary
        assert 'active_workflows' in summary
        assert 'success_rate' in summary
        assert 'avg_processing_time' in summary
        assert 'cpu_utilization' in summary
        assert 'memory_utilization' in summary
        assert 'bottleneck_count' in summary
        assert 'alert_count' in summary
        assert 'last_updated' in summary


class TestEndToEndOrchestration:
    """End-to-end integration tests for the orchestration system."""
    
    @pytest.fixture
    def temp_metrics_store(self):
        """Create temporary metrics store directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @pytest.mark.asyncio
    async def test_full_workflow_orchestration(self, temp_metrics_store):
        """Test complete workflow orchestration flow."""
        # Initialize orchestrator
        orchestrator = WorkflowOrchestrator(
            max_concurrent_workflows=2,
            resource_limits={'cpu': 0.8, 'memory': 0.8, 'disk': 0.9},
            metrics_store=temp_metrics_store
        )
        
        try:
            # Mock successful execution
            with patch.object(orchestrator.executor, 'arun') as mock_run:
                mock_run.return_value = {
                    'success': True,
                    'final_draft': 'Test essay content',
                    'selected_story': 'Test story',
                    'word_count': 650
                }
                
                # Create workflow configurations
                configs = [
                    WorkflowConfig(
                        type='essay_workflow',
                        prompt=f'Test prompt {i}',
                        user_profile={'name': f'User {i}', 'grade': 12},
                        college_id=f'college_{i}',
                        priority='normal'
                    )
                    for i in range(3)
                ]
                
                # Submit workflows
                workflow_ids = []
                for config in configs:
                    workflow_id = await orchestrator.submit_workflow(config)
                    workflow_ids.append(workflow_id)
                
                # Wait for processing
                await asyncio.sleep(0.2)
                
                # Check system status
                status = orchestrator.get_system_status()
                assert status.status in ['healthy', 'warning', 'critical']
                
                # Check dashboard data
                dashboard_data = orchestrator.get_dashboard_data()
                assert dashboard_data.system_status.total_processed >= 0
                
                # Check performance summary
                summary = orchestrator.get_performance_summary()
                assert 'status' in summary
                assert summary['active_workflows'] >= 0
                
        finally:
            await orchestrator.shutdown()
    
    @pytest.mark.asyncio
    async def test_monitoring_integration(self, temp_metrics_store):
        """Test integration between monitoring components."""
        orchestrator = WorkflowOrchestrator(
            max_concurrent_workflows=1,
            resource_limits={'cpu': 0.5, 'memory': 0.6, 'disk': 0.7},
            metrics_store=temp_metrics_store
        )
        
        try:
            # Enable monitoring in executor
            orchestrator.executor.monitoring_enabled = True
            
            # Mock executor with monitoring
            with patch.object(orchestrator.executor, 'arun') as mock_run:
                mock_run.return_value = {'success': True, 'final_draft': 'Test'}
                
                config = WorkflowConfig(
                    type='essay_workflow',
                    prompt='Test monitoring integration',
                    user_profile={'name': 'Test User'}
                )
                
                result = await orchestrator.execute_workflow(config)
                
                # Verify monitoring data was collected
                assert result.success
                assert orchestrator.metrics.get_total_processed() > 0
                
                # Check dashboard has monitoring data
                dashboard_data = orchestrator.get_dashboard_data()
                assert dashboard_data.performance_metrics.total_workflows > 0
                
        finally:
            await orchestrator.shutdown()
    
    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self, temp_metrics_store):
        """Test error handling and recovery mechanisms."""
        orchestrator = WorkflowOrchestrator(
            max_concurrent_workflows=1,
            metrics_store=temp_metrics_store
        )
        
        try:
            # Mock executor failure
            with patch.object(orchestrator.executor, 'arun') as mock_run:
                mock_run.side_effect = Exception("Simulated failure")
                
                config = WorkflowConfig(
                    type='essay_workflow',
                    prompt='Test error handling',
                    user_profile={'name': 'Test User'}
                )
                
                result = await orchestrator.execute_workflow(config)
                
                # Verify error was handled gracefully
                assert not result.success
                assert result.error_message == "Simulated failure"
                
                # Check that system remains operational
                status = orchestrator.get_system_status()
                assert status.status in ['healthy', 'warning', 'critical']
                
        finally:
            await orchestrator.shutdown()


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 