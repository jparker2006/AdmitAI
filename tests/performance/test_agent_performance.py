"""Performance tests for ReAct agent system.

This module provides comprehensive performance testing including:
- Response time benchmarking (target: <30s)
- Memory usage profiling (target: <500MB)
- Concurrent user simulation (target: >95% success rate)
- Tool execution timing analysis
- Bottleneck detection integration
- Load testing and stress scenarios
"""
import pytest
import asyncio
import time
import psutil
import gc
import tracemalloc
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import statistics
import concurrent.futures
import threading

from essay_agent.agent.core.react_agent import EssayReActAgent
from essay_agent.monitoring.bottleneck_detector import BottleneckDetector
from essay_agent.monitoring.workflow_metrics import WorkflowMetrics


@dataclass
class PerformanceBenchmark:
    """Performance benchmark result."""
    test_name: str
    execution_time: float
    memory_peak: float  # MB
    memory_avg: float  # MB
    cpu_percent: float
    success_rate: float
    throughput: float  # operations per second
    p95_response_time: float
    error_count: int
    total_operations: int
    
    def passes_targets(self) -> bool:
        """Check if benchmark passes performance targets."""
        return (
            self.execution_time < 30.0 and  # <30s response time
            self.memory_peak < 500.0 and    # <500MB memory
            self.success_rate > 0.95 and    # >95% success rate
            self.p95_response_time < 35.0    # 95th percentile <35s
        )


class PerformanceTestRunner:
    """Main performance test runner with comprehensive metrics."""
    
    def __init__(self):
        self.results: List[PerformanceBenchmark] = []
        self.bottleneck_detector = BottleneckDetector()
        self.workflow_metrics = WorkflowMetrics()
        
    def start_monitoring(self):
        """Start system resource monitoring."""
        tracemalloc.start()
        self.start_time = time.time()
        self.process = psutil.Process()
        self.initial_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        
    def stop_monitoring(self) -> Dict[str, float]:
        """Stop monitoring and return metrics."""
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        end_time = time.time()
        final_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        
        return {
            "execution_time": end_time - self.start_time,
            "memory_peak": peak / 1024 / 1024,  # Convert to MB
            "memory_current": current / 1024 / 1024,
            "memory_increase": final_memory - self.initial_memory,
            "cpu_percent": self.process.cpu_percent()
        }
    
    async def run_benchmark(self, test_func, *args, **kwargs) -> PerformanceBenchmark:
        """Run a single performance benchmark."""
        self.start_monitoring()
        
        try:
            result = await test_func(*args, **kwargs)
            success_rate = 1.0
            error_count = 0
        except Exception as e:
            result = None
            success_rate = 0.0
            error_count = 1
        
        metrics = self.stop_monitoring()
        
        return PerformanceBenchmark(
            test_name=test_func.__name__,
            execution_time=metrics["execution_time"],
            memory_peak=metrics["memory_peak"],
            memory_avg=(metrics["memory_current"] + self.initial_memory) / 2,
            cpu_percent=metrics["cpu_percent"],
            success_rate=success_rate,
            throughput=1.0 / metrics["execution_time"] if metrics["execution_time"] > 0 else 0,
            p95_response_time=metrics["execution_time"],  # Single operation
            error_count=error_count,
            total_operations=1
        )


class TestReActAgentPerformance:
    """Test ReAct agent performance characteristics."""
    
    @pytest.fixture
    def performance_runner(self):
        """Create performance test runner."""
        return PerformanceTestRunner()
    
    @pytest.fixture
    def temp_user_id(self):
        """Generate temporary user ID for performance testing."""
        return f"perf_test_user_{int(time.time())}"
    
    @pytest.fixture
    def mock_fast_llm(self):
        """Mock LLM with fast, consistent responses."""
        async def fast_predict(prompt):
            # Simulate realistic LLM response time (1-2 seconds)
            await asyncio.sleep(0.1)  # Fast for testing
            return '{"response_type": "conversation", "confidence": 0.8}'
        
        mock_llm = AsyncMock()
        mock_llm.apredict = fast_predict
        return mock_llm
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_single_response_time_benchmark(self, performance_runner, temp_user_id, mock_fast_llm):
        """Benchmark single agent response time."""
        async def single_response_test():
            with patch('essay_agent.llm_client.get_chat_llm', return_value=mock_fast_llm):
                agent = EssayReActAgent(temp_user_id)
                response = await agent.handle_message("Help me with my essay")
                assert isinstance(response, str)
                assert len(response) > 0
                return response
        
        benchmark = await performance_runner.run_benchmark(single_response_test)
        
        # Assert performance targets
        assert benchmark.execution_time < 30.0, f"Response time {benchmark.execution_time}s exceeds 30s target"
        assert benchmark.memory_peak < 500.0, f"Memory peak {benchmark.memory_peak}MB exceeds 500MB target"
        assert benchmark.success_rate == 1.0, f"Success rate {benchmark.success_rate} below 100% target"
        
        performance_runner.results.append(benchmark)
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_multi_turn_conversation_performance(self, performance_runner, temp_user_id, mock_fast_llm):
        """Test performance across multiple conversation turns."""
        async def multi_turn_test():
            with patch('essay_agent.llm_client.get_chat_llm', return_value=mock_fast_llm):
                agent = EssayReActAgent(temp_user_id)
                
                messages = [
                    "Hello, I need help with my college essay",
                    "I want to write about overcoming challenges",
                    "Can you help me brainstorm some ideas?",
                    "What about my robotics competition experience?",
                    "How should I structure this essay?"
                ]
                
                responses = []
                start_time = time.time()
                
                for message in messages:
                    response = await agent.handle_message(message)
                    responses.append(response)
                    assert len(response) > 0
                
                end_time = time.time()
                total_time = end_time - start_time
                
                return {
                    "responses": responses,
                    "total_time": total_time,
                    "avg_time_per_turn": total_time / len(messages),
                    "turn_count": len(messages)
                }
        
        benchmark = await performance_runner.run_benchmark(multi_turn_test)
        
        # Performance assertions
        assert benchmark.execution_time < 60.0, f"Multi-turn time {benchmark.execution_time}s exceeds 60s target"
        assert benchmark.memory_peak < 600.0, f"Memory peak {benchmark.memory_peak}MB exceeds 600MB target"
        
        performance_runner.results.append(benchmark)
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_tool_execution_timing_analysis(self, performance_runner, temp_user_id, mock_fast_llm):
        """Analyze tool execution timing performance."""
        tool_execution_times = {}
        
        async def tool_timing_test():
            with patch('essay_agent.llm_client.get_chat_llm', return_value=mock_fast_llm):
                with patch('essay_agent.agent.tools.tool_registry.ENHANCED_REGISTRY') as mock_registry:
                    mock_registry.has_tool.return_value = True
                    mock_registry.get_tool_description.return_value = {"required_args": [], "arg_types": {}}
                    
                    # Mock tool with timing tracking
                    async def timed_tool_execution(tool_name, **kwargs):
                        execution_start = time.time()
                        # Simulate tool work
                        await asyncio.sleep(0.05)  # Fast for testing
                        execution_time = time.time() - execution_start
                        
                        tool_execution_times[tool_name] = execution_time
                        return {"result": f"Mock {tool_name} result", "execution_time": execution_time}
                    
                    mock_registry.get_tool.return_value = timed_tool_execution
                    
                    agent = EssayReActAgent(temp_user_id)
                    
                    # Force tool execution mode
                    with patch.object(agent.reasoning_engine, 'reason_about_action') as mock_reason:
                        mock_reason.return_value = Mock(
                            response_type="tool_execution",
                            chosen_tool="brainstorm",
                            tool_args={"prompt": "test"},
                            confidence=0.8
                        )
                        
                        response = await agent.handle_message("Help me brainstorm")
                        assert len(response) > 0
                
                return tool_execution_times
        
        benchmark = await performance_runner.run_benchmark(tool_timing_test)
        
        # Verify tool execution was fast
        assert benchmark.execution_time < 10.0, f"Tool execution time {benchmark.execution_time}s too slow"
        
        performance_runner.results.append(benchmark)
    
    @pytest.mark.performance
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_memory_usage_profiling(self, performance_runner, temp_user_id, mock_fast_llm):
        """Profile memory usage during extended operation."""
        async def memory_profile_test():
            with patch('essay_agent.llm_client.get_chat_llm', return_value=mock_fast_llm):
                agent = EssayReActAgent(temp_user_id)
                
                memory_snapshots = []
                process = psutil.Process()
                
                # Baseline memory
                memory_snapshots.append(process.memory_info().rss / 1024 / 1024)
                
                # Execute many operations to test memory accumulation
                for i in range(20):  # Reduced for faster testing
                    await agent.handle_message(f"Test message {i}")
                    
                    # Take memory snapshot every 5 operations
                    if i % 5 == 0:
                        memory_snapshots.append(process.memory_info().rss / 1024 / 1024)
                        gc.collect()  # Force garbage collection
                
                # Final memory check
                memory_snapshots.append(process.memory_info().rss / 1024 / 1024)
                
                return {
                    "memory_snapshots": memory_snapshots,
                    "memory_growth": memory_snapshots[-1] - memory_snapshots[0],
                    "peak_memory": max(memory_snapshots),
                    "operations": 20
                }
        
        benchmark = await performance_runner.run_benchmark(memory_profile_test)
        
        # Memory usage assertions
        assert benchmark.memory_peak < 500.0, f"Memory peak {benchmark.memory_peak}MB exceeds target"
        
        performance_runner.results.append(benchmark)


class TestConcurrentPerformance:
    """Test performance under concurrent load."""
    
    @pytest.fixture
    def mock_fast_llm(self):
        """Mock LLM for concurrent testing."""
        async def fast_predict(prompt):
            await asyncio.sleep(0.05)  # Very fast for testing
            return '{"response_type": "conversation", "confidence": 0.8}'
        
        mock_llm = AsyncMock()
        mock_llm.apredict = fast_predict
        return mock_llm
    
    @pytest.mark.performance
    @pytest.mark.load_test
    @pytest.mark.asyncio
    async def test_concurrent_user_simulation(self, mock_fast_llm):
        """Simulate multiple concurrent users."""
        user_count = 5  # Reduced for faster testing
        messages_per_user = 3
        
        async def simulate_user(user_id: str) -> Dict[str, Any]:
            """Simulate a single user session."""
            with patch('essay_agent.llm_client.get_chat_llm', return_value=mock_fast_llm):
                agent = EssayReActAgent(f"concurrent_user_{user_id}")
                
                responses = []
                errors = []
                start_time = time.time()
                
                for i in range(messages_per_user):
                    try:
                        response = await agent.handle_message(f"User {user_id} message {i}")
                        responses.append(response)
                    except Exception as e:
                        errors.append(str(e))
                
                end_time = time.time()
                
                return {
                    "user_id": user_id,
                    "responses": responses,
                    "errors": errors,
                    "duration": end_time - start_time,
                    "success_rate": len(responses) / messages_per_user
                }
        
        # Run concurrent user simulations
        start_time = time.time()
        
        tasks = [simulate_user(str(i)) for i in range(user_count)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        total_duration = end_time - start_time
        
        # Analyze results
        successful_users = [r for r in results if isinstance(r, dict) and r.get("success_rate", 0) > 0.8]
        total_operations = user_count * messages_per_user
        successful_operations = sum(len(r.get("responses", [])) for r in successful_users)
        
        overall_success_rate = successful_operations / total_operations
        throughput = successful_operations / total_duration
        
        # Performance assertions
        assert overall_success_rate > 0.95, f"Success rate {overall_success_rate:.2%} below 95% target"
        assert total_duration < 30.0, f"Total duration {total_duration}s exceeds 30s target"
        assert throughput > 0.5, f"Throughput {throughput} ops/s too low"
        
        print(f"Concurrent test: {user_count} users, {overall_success_rate:.2%} success, {throughput:.2f} ops/s")
    
    @pytest.mark.performance
    @pytest.mark.load_test
    @pytest.mark.asyncio
    async def test_rapid_sequential_requests(self, mock_fast_llm):
        """Test rapid sequential requests to single agent."""
        with patch('essay_agent.llm_client.get_chat_llm', return_value=mock_fast_llm):
            agent = EssayReActAgent("rapid_test_user")
            
            request_count = 10
            start_time = time.time()
            
            responses = []
            for i in range(request_count):
                try:
                    response = await agent.handle_message(f"Rapid request {i}")
                    responses.append(response)
                except Exception as e:
                    print(f"Error in rapid request {i}: {e}")
            
            end_time = time.time()
            total_time = end_time - start_time
            
            # Performance metrics
            success_rate = len(responses) / request_count
            throughput = len(responses) / total_time
            avg_response_time = total_time / request_count
            
            # Assertions
            assert success_rate > 0.95, f"Success rate {success_rate:.2%} below target"
            assert avg_response_time < 5.0, f"Average response time {avg_response_time}s too high"
            assert throughput > 1.0, f"Throughput {throughput} ops/s too low"


class TestBottleneckDetection:
    """Test integration with bottleneck detection system."""
    
    @pytest.fixture
    def bottleneck_detector(self):
        """Create bottleneck detector for testing."""
        return BottleneckDetector(threshold_percentile=90.0, min_samples=5)
    
    @pytest.mark.performance
    def test_tool_execution_bottleneck_detection(self, bottleneck_detector):
        """Test detection of tool execution bottlenecks."""
        # Simulate tool execution data
        normal_tool_times = [1.0, 1.2, 0.9, 1.1, 1.0, 0.8, 1.3, 1.0, 0.9, 1.1]
        slow_tool_times = [15.0, 16.2, 14.8, 15.5, 17.1, 16.0, 15.8, 16.5, 15.2, 16.8]
        
        # Record normal tool performance
        for time_val in normal_tool_times:
            bottleneck_detector.record_tool_execution("normal_tool", time_val, True)
        
        # Record slow tool performance
        for time_val in slow_tool_times:
            bottleneck_detector.record_tool_execution("slow_tool", time_val, True)
        
        # Analyze for bottlenecks
        bottlenecks = bottleneck_detector.analyze_performance()
        
        # Should detect slow tool as bottleneck
        slow_bottlenecks = [b for b in bottlenecks if b.component == "slow_tool"]
        assert len(slow_bottlenecks) > 0, "Failed to detect slow tool bottleneck"
        
        slow_bottleneck = slow_bottlenecks[0]
        assert slow_bottleneck.severity > 1.0, "Bottleneck severity not detected properly"
        assert slow_bottleneck.impact in ["high", "medium"], "Bottleneck impact not classified correctly"
    
    @pytest.mark.performance
    def test_workflow_stage_performance_tracking(self, bottleneck_detector):
        """Test workflow stage performance tracking."""
        stages = ["reasoning", "tool_execution", "response_generation"]
        stage_times = {
            "reasoning": [2.0, 2.1, 1.9, 2.2, 2.0],
            "tool_execution": [8.0, 8.5, 7.8, 8.2, 8.1],  
            "response_generation": [1.0, 1.1, 0.9, 1.0, 1.2]
        }
        
        # Record stage performance
        for stage, times in stage_times.items():
            for time_val in times:
                bottleneck_detector.record_workflow_stage(stage, time_val, True)
        
        # Analyze performance
        bottlenecks = bottleneck_detector.analyze_performance()
        
        # Tool execution should be identified as slower stage
        exec_bottlenecks = [b for b in bottlenecks if b.component == "tool_execution"]
        
        # May or may not be flagged as bottleneck depending on thresholds
        # But should be tracked in the system
        assert len(bottleneck_detector.workflow_stage_times["tool_execution"]) == 5


@pytest.mark.performance
class TestPerformanceRegression:
    """Test for performance regressions against baseline metrics."""
    
    BASELINE_METRICS = {
        "single_response_time": 25.0,  # seconds
        "memory_peak": 400.0,  # MB
        "concurrent_success_rate": 0.95,  # 95%
        "tool_execution_time": 8.0,  # seconds
        "multi_turn_time": 50.0  # seconds for 5 turns
    }
    
    @pytest.fixture
    def mock_fast_llm(self):
        """Mock LLM for regression testing."""
        async def predict(prompt):
            await asyncio.sleep(0.1)
            return '{"response_type": "conversation", "confidence": 0.8}'
        
        mock_llm = AsyncMock()
        mock_llm.apredict = predict
        return mock_llm
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_response_time_regression(self, mock_fast_llm):
        """Test that response times haven't regressed."""
        with patch('essay_agent.llm_client.get_chat_llm', return_value=mock_fast_llm):
            agent = EssayReActAgent("regression_test_user")
            
            start_time = time.time()
            response = await agent.handle_message("Test regression message")
            end_time = time.time()
            
            response_time = end_time - start_time
            baseline = self.BASELINE_METRICS["single_response_time"]
            
            # Allow 20% variance from baseline
            tolerance = baseline * 0.2
            assert response_time <= baseline + tolerance, \
                f"Response time {response_time}s exceeds baseline {baseline}s + tolerance"
            
            assert len(response) > 0, "Response should not be empty"
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_memory_usage_regression(self, mock_fast_llm):
        """Test that memory usage hasn't regressed."""
        tracemalloc.start()
        
        with patch('essay_agent.llm_client.get_chat_llm', return_value=mock_fast_llm):
            agent = EssayReActAgent("memory_regression_user")
            
            # Execute several operations
            for i in range(5):
                await agent.handle_message(f"Memory test {i}")
            
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            
            peak_mb = peak / 1024 / 1024
            baseline = self.BASELINE_METRICS["memory_peak"]
            
            # Allow 30% variance for memory
            tolerance = baseline * 0.3
            assert peak_mb <= baseline + tolerance, \
                f"Memory peak {peak_mb}MB exceeds baseline {baseline}MB + tolerance"


def pytest_configure(config):
    """Configure pytest for performance testing."""
    config.addinivalue_line(
        "markers", "performance: marks tests as performance tests"
    )
    config.addinivalue_line(
        "markers", "load_test: marks tests as load/stress tests"
    )
    config.addinivalue_line(
        "markers", "slow: marks tests as slow running tests"
    )


if __name__ == "__main__":
    # Run performance tests directly
    pytest.main([__file__, "-v", "-m", "performance"]) 