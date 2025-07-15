#!/usr/bin/env python3
"""Demo script for advanced orchestration and monitoring system.

This script demonstrates the comprehensive orchestration capabilities including:
- Resource-aware workflow execution
- Real-time performance monitoring
- Bottleneck detection and optimization
- Analytics dashboard
"""

import asyncio
import time
from typing import Dict, Any

from essay_agent.workflows.orchestrator import WorkflowOrchestrator, WorkflowConfig
from essay_agent.models import UserProfile


async def demo_orchestration():
    """Demonstrate advanced orchestration capabilities."""
    print("🚀 Starting Essay Agent Orchestration Demo")
    print("=" * 60)
    
    # Initialize orchestrator with resource limits
    orchestrator = WorkflowOrchestrator(
        max_concurrent_workflows=5,
        resource_limits={'cpu': 0.7, 'memory': 0.8, 'disk': 0.9},
        metrics_store="demo_metrics"
    )
    
    # Sample user profile
    user_profile = {
        "name": "Demo User",
        "grade": 12,
        "interests": ["robotics", "volunteering", "creative writing"],
        "defining_moments": [
            {
                "title": "Robotics Competition Victory",
                "description": "Led team to state championship",
                "story_category": "accomplishment"
            },
            {
                "title": "Community Garden Project",
                "description": "Started neighborhood garden initiative",
                "story_category": "community"
            }
        ]
    }
    
    # Demo workflows
    demo_workflows = [
        {
            "type": "essay_workflow",
            "prompt": "Tell us about a time when you showed leadership. How did this experience change you?",
            "college_id": "harvard",
            "priority": "high"
        },
        {
            "type": "essay_workflow", 
            "prompt": "Describe a challenge you overcame. What did you learn from this experience?",
            "college_id": "stanford",
            "priority": "normal"
        },
        {
            "type": "essay_workflow",
            "prompt": "What activity or experience has been most meaningful to you?",
            "college_id": "mit",
            "priority": "normal"
        }
    ]
    
    try:
        # 1. Show initial system status
        print("\n📊 Initial System Status")
        print("-" * 30)
        status = orchestrator.get_system_status()
        print(f"Status: {status.status}")
        print(f"Active workflows: {status.active_workflows}")
        print(f"CPU utilization: {status.resource_utilization['cpu']:.1%}")
        print(f"Memory utilization: {status.resource_utilization['memory']:.1%}")
        
        # 2. Submit workflows for execution
        print("\n🔄 Submitting Workflows")
        print("-" * 30)
        
        workflow_ids = []
        for i, workflow_info in enumerate(demo_workflows):
            config = WorkflowConfig(
                type=workflow_info["type"],
                prompt=workflow_info["prompt"],
                user_profile=user_profile,
                college_id=workflow_info["college_id"],
                priority=workflow_info["priority"]
            )
            
            workflow_id = await orchestrator.submit_workflow(config)
            workflow_ids.append(workflow_id)
            print(f"✅ Submitted workflow {i+1}: {workflow_id[:8]}...")
        
        # 3. Monitor workflow execution
        print("\n⏱️  Monitoring Workflow Execution")
        print("-" * 30)
        
        completed_workflows = 0
        monitoring_iterations = 0
        
        while completed_workflows < len(demo_workflows) and monitoring_iterations < 60:
            # Check workflow status
            running_count = 0
            for workflow_id in workflow_ids:
                status_info = await orchestrator.get_workflow_status(workflow_id)
                if status_info['status'] == 'running':
                    running_count += 1
                elif status_info['status'] == 'not_found':
                    completed_workflows += 1
            
            # Get real-time metrics
            metrics = orchestrator.get_dashboard_data()
            
            print(f"  Running: {running_count}, Completed: {completed_workflows}")
            print(f"  CPU: {metrics.system_status.resource_utilization['cpu']:.1%}, "
                  f"Memory: {metrics.system_status.resource_utilization['memory']:.1%}")
            
            # Show bottlenecks if any
            if metrics.bottleneck_analysis:
                print(f"  🔧 Bottlenecks detected: {len(metrics.bottleneck_analysis)}")
                for bottleneck in metrics.bottleneck_analysis[:2]:  # Show top 2
                    print(f"    - {bottleneck.description}")
            
            await asyncio.sleep(2)
            monitoring_iterations += 1
        
        # 4. Show final performance report
        print("\n📈 Final Performance Report")
        print("-" * 30)
        
        dashboard_data = orchestrator.get_dashboard_data()
        
        print(f"System Status: {dashboard_data.system_status.status}")
        print(f"Total Processed: {dashboard_data.system_status.total_processed}")
        print(f"Success Rate: {dashboard_data.system_status.success_rate:.1%}")
        print(f"Avg Processing Time: {dashboard_data.system_status.avg_processing_time:.2f}s")
        
        # Resource analytics
        print(f"\nResource Utilization:")
        print(f"  CPU: {dashboard_data.system_status.resource_utilization['cpu']:.1%}")
        print(f"  Memory: {dashboard_data.system_status.resource_utilization['memory']:.1%}")
        print(f"  Disk: {dashboard_data.system_status.resource_utilization['disk']:.1%}")
        
        # Performance metrics
        perf_metrics = dashboard_data.performance_metrics
        print(f"\nPerformance Metrics:")
        print(f"  Total Workflows: {perf_metrics.total_workflows}")
        print(f"  Successful: {perf_metrics.successful_workflows}")
        print(f"  Failed: {perf_metrics.failed_workflows}")
        print(f"  P95 Execution Time: {perf_metrics.p95_execution_time:.2f}s")
        
        # Bottleneck analysis
        if dashboard_data.bottleneck_analysis:
            print(f"\nBottleneck Analysis:")
            for bottleneck in dashboard_data.bottleneck_analysis[:3]:  # Top 3
                print(f"  - {bottleneck.description} (severity: {bottleneck.severity:.1f})")
        
        # Recommendations
        if dashboard_data.recommendations:
            print(f"\nRecommendations:")
            for rec in dashboard_data.recommendations[:3]:  # Top 3
                print(f"  • {rec}")
        
        # 5. Export report
        print("\n📄 Generating Performance Report")
        print("-" * 30)
        
        # Generate JSON report
        json_report = orchestrator.dashboard.export_report('json')
        with open('orchestration_report.json', 'w') as f:
            f.write(json_report)
        print("✅ JSON report saved to orchestration_report.json")
        
        # Generate HTML report
        html_report = orchestrator.dashboard.export_report('html')
        with open('orchestration_report.html', 'w') as f:
            f.write(html_report)
        print("✅ HTML report saved to orchestration_report.html")
        
        # 6. Demonstrate capacity prediction
        print("\n🔮 Capacity Prediction")
        print("-" * 30)
        
        capacity_prediction = orchestrator.resource_manager.predict_capacity(
            workflow_count=20,
            workflow_type='essay_workflow'
        )
        
        print(f"Can accommodate 20 workflows: {capacity_prediction['can_accommodate']}")
        print(f"Bottleneck resource: {capacity_prediction['bottleneck_resource']}")
        print(f"CPU needed: {capacity_prediction['resource_requirements']['cpu']:.2f}")
        print(f"Memory needed: {capacity_prediction['resource_requirements']['memory']:.2f}")
        
        # 7. Show scaling recommendation
        print("\n📊 Scaling Recommendation")
        print("-" * 30)
        
        scaling_rec = orchestrator.resource_manager.suggest_scaling()
        print(f"Action: {scaling_rec.action}")
        print(f"Resource: {scaling_rec.resource_type}")
        print(f"Current utilization: {scaling_rec.current_utilization:.1%}")
        print(f"Target utilization: {scaling_rec.target_utilization:.1%}")
        print(f"Reasoning: {scaling_rec.reasoning}")
        print(f"Urgency: {scaling_rec.urgency}")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean shutdown
        await orchestrator.shutdown()
        print("\n✅ Demo completed successfully!")


def demo_analytics_dashboard():
    """Demonstrate analytics dashboard capabilities."""
    print("\n🎯 Analytics Dashboard Demo")
    print("=" * 40)
    
    # This would typically use real data from the orchestrator
    print("Dashboard features:")
    print("• Real-time system status")
    print("• Performance trend analysis")
    print("• Resource utilization tracking")
    print("• Bottleneck detection and alerts")
    print("• Optimization recommendations")
    print("• Export capabilities (JSON, HTML, CSV)")


async def main():
    """Main demo function."""
    print("🎭 Essay Agent Advanced Orchestration Demo")
    print("=" * 60)
    
    await demo_orchestration()
    demo_analytics_dashboard()


if __name__ == "__main__":
    asyncio.run(main()) 