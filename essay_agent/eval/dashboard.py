"""essay_agent.eval.dashboard

Dashboard and reporting system for LLM-powered evaluation results.

This module provides comprehensive reporting capabilities including HTML report generation,
live monitoring interfaces, data visualization, and export functionality for evaluation
results and pattern analysis insights.
"""

import json
import html
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
import threading
import time

from .llm_evaluator import ConversationEvaluation, TurnEvaluation
from .batch_processor import BatchResult, BatchProgress, EvaluationTask
from .pattern_analyzer import PatternAnalysis, Pattern, PerformanceTrend, BottleneckReport
from ..utils.logging import debug_print


@dataclass
class DashboardMetrics:
    """Real-time dashboard metrics."""
    current_evaluations_running: int = 0
    total_evaluations_completed: int = 0
    success_rate: float = 0.0
    average_quality_score: float = 0.0
    total_cost: float = 0.0
    system_health: str = "unknown"
    last_updated: datetime = field(default_factory=datetime.now)
    
    # Performance metrics
    avg_response_time: float = 0.0
    peak_parallel_tasks: int = 0
    total_api_calls: int = 0
    
    # Recent activity
    recent_batch_results: List[str] = field(default_factory=list)
    active_batches: List[str] = field(default_factory=list)


class LiveMonitor:
    """Live monitoring interface for ongoing evaluations."""
    
    def __init__(self):
        self.is_monitoring = False
        self.metrics = DashboardMetrics()
        self.update_interval = 5  # seconds
        self.monitor_thread = None
        self.callbacks = []
    
    def start_monitoring(self):
        """Start live monitoring."""
        if not self.is_monitoring:
            self.is_monitoring = True
            self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
            self.monitor_thread.start()
            debug_print(True, "Live monitoring started")
    
    def stop_monitoring(self):
        """Stop live monitoring."""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1)
        debug_print(True, "Live monitoring stopped")
    
    def add_callback(self, callback):
        """Add callback for metrics updates."""
        self.callbacks.append(callback)
    
    def update_metrics(self, **kwargs):
        """Update dashboard metrics."""
        for key, value in kwargs.items():
            if hasattr(self.metrics, key):
                setattr(self.metrics, key, value)
        
        self.metrics.last_updated = datetime.now()
        
        # Notify callbacks
        for callback in self.callbacks:
            try:
                callback(self.metrics)
            except Exception as e:
                debug_print(True, f"Callback error: {e}")
    
    def _monitoring_loop(self):
        """Main monitoring loop."""
        while self.is_monitoring:
            try:
                # Update metrics from current system state
                self._collect_system_metrics()
                
                # Notify callbacks
                for callback in self.callbacks:
                    try:
                        callback(self.metrics)
                    except Exception as e:
                        debug_print(True, f"Monitoring callback error: {e}")
                
                time.sleep(self.update_interval)
                
            except Exception as e:
                debug_print(True, f"Monitoring loop error: {e}")
                time.sleep(self.update_interval)
    
    def _collect_system_metrics(self):
        """Collect current system metrics."""
        # This would integrate with actual system monitoring
        # For now, just update timestamp
        self.metrics.last_updated = datetime.now()


class EvaluationDashboard:
    """Main dashboard for evaluation results and insights."""
    
    def __init__(self):
        self.live_monitor = LiveMonitor()
        self.report_templates = self._load_report_templates()
    
    def generate_html_report(
        self,
        batch_results: List[BatchResult],
        pattern_analysis: Optional[PatternAnalysis] = None,
        title: str = "Evaluation Report",
        include_charts: bool = True
    ) -> str:
        """
        Generate comprehensive HTML report.
        
        Args:
            batch_results: List of batch evaluation results
            pattern_analysis: Optional pattern analysis results
            title: Report title
            include_charts: Whether to include charts and visualizations
            
        Returns:
            Complete HTML report string
        """
        
        # Calculate summary metrics
        summary = self._calculate_report_summary(batch_results)
        
        # Generate HTML sections
        html_content = self._build_html_structure(
            title=title,
            summary=summary,
            batch_results=batch_results,
            pattern_analysis=pattern_analysis,
            include_charts=include_charts
        )
        
        return html_content
    
    def export_report(
        self,
        batch_results: List[BatchResult],
        output_path: Union[str, Path],
        pattern_analysis: Optional[PatternAnalysis] = None,
        title: str = "Evaluation Report"
    ):
        """Export HTML report to file."""
        
        html_content = self.generate_html_report(
            batch_results, pattern_analysis, title
        )
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        debug_print(True, f"HTML report exported to: {output_path}")
    
    def create_live_monitor(self) -> LiveMonitor:
        """Create and return live monitor instance."""
        return self.live_monitor
    
    def generate_summary_json(
        self,
        batch_results: List[BatchResult],
        pattern_analysis: Optional[PatternAnalysis] = None
    ) -> Dict[str, Any]:
        """Generate JSON summary of evaluation results."""
        
        summary = self._calculate_report_summary(batch_results)
        
        json_summary = {
            "report_generated": datetime.now().isoformat(),
            "summary_metrics": summary,
            "batch_count": len(batch_results),
            "batch_summaries": [self._batch_to_summary(batch) for batch in batch_results],
        }
        
        if pattern_analysis:
            json_summary["pattern_analysis"] = {
                "analysis_id": pattern_analysis.analysis_id,
                "system_health": pattern_analysis.overall_system_health,
                "patterns_found": len(pattern_analysis.identified_patterns),
                "critical_issues": pattern_analysis.critical_issues,
                "quick_wins": pattern_analysis.quick_wins,
                "recommendations_count": len(pattern_analysis.improvement_recommendations)
            }
        
        return json_summary
    
    def _calculate_report_summary(self, batch_results: List[BatchResult]) -> Dict[str, Any]:
        """Calculate summary metrics from batch results."""
        
        if not batch_results:
            return {
                "total_evaluations": 0,
                "success_rate": 0.0,
                "average_quality": 0.0,
                "total_cost": 0.0,
                "total_duration": 0.0,
                "avg_cost_per_evaluation": 0.0
            }
        
        total_successful = sum(b.successful_evaluations for b in batch_results)
        total_failed = sum(b.failed_evaluations for b in batch_results)
        total_evaluations = total_successful + total_failed
        
        # Calculate weighted average quality
        quality_scores = []
        for batch in batch_results:
            if batch.successful_evaluations > 0:
                quality_scores.extend([batch.average_evaluation_score] * batch.successful_evaluations)
        
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
        
        total_cost = sum(b.total_llm_cost for b in batch_results)
        total_duration = sum(b.total_duration_seconds for b in batch_results)
        
        return {
            "total_evaluations": total_evaluations,
            "successful_evaluations": total_successful,
            "failed_evaluations": total_failed,
            "success_rate": total_successful / total_evaluations if total_evaluations > 0 else 0.0,
            "average_quality": avg_quality,
            "total_cost": total_cost,
            "total_duration": total_duration,
            "avg_cost_per_evaluation": total_cost / total_successful if total_successful > 0 else 0.0,
            "avg_duration_per_evaluation": total_duration / total_evaluations if total_evaluations > 0 else 0.0
        }
    
    def _build_html_structure(
        self,
        title: str,
        summary: Dict[str, Any],
        batch_results: List[BatchResult],
        pattern_analysis: Optional[PatternAnalysis],
        include_charts: bool
    ) -> str:
        """Build complete HTML report structure."""
        
        # HTML template with embedded CSS
        html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html.escape(title)}</title>
    <style>
        {self._get_css_styles()}
    </style>
    {self._get_chart_scripts() if include_charts else ''}
</head>
<body>
    <div class="container">
        <header class="report-header">
            <h1>{html.escape(title)}</h1>
            <p class="report-date">Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        </header>
        
        <div class="summary-section">
            <h2>📊 Executive Summary</h2>
            {self._build_summary_cards(summary)}
        </div>
        
        {self._build_charts_section(batch_results) if include_charts else ''}
        
        <div class="batch-results-section">
            <h2>🔄 Batch Results</h2>
            {self._build_batch_results_table(batch_results)}
        </div>
        
        {self._build_pattern_analysis_section(pattern_analysis) if pattern_analysis else ''}
        
        <div class="recommendations-section">
            <h2>💡 Recommendations</h2>
            {self._build_recommendations_section(batch_results, pattern_analysis)}
        </div>
        
        <footer class="report-footer">
            <p>Report generated by Essay Agent Evaluation System</p>
        </footer>
    </div>
</body>
</html>
"""
        
        return html_template
    
    def _get_css_styles(self) -> str:
        """Get CSS styles for HTML report."""
        return """
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: white;
            box-shadow: 0 0 20px rgba(0,0,0,0.1);
        }
        
        .report-header {
            text-align: center;
            margin-bottom: 40px;
            padding-bottom: 20px;
            border-bottom: 2px solid #eee;
        }
        
        .report-header h1 {
            color: #2c3e50;
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .report-date {
            color: #7f8c8d;
            font-size: 1.1em;
        }
        
        .summary-section {
            margin-bottom: 40px;
        }
        
        .summary-cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        
        .summary-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 25px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }
        
        .summary-card.success {
            background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
        }
        
        .summary-card.warning {
            background: linear-gradient(135deg, #ff9800 0%, #f57c00 100%);
        }
        
        .summary-card.error {
            background: linear-gradient(135deg, #f44336 0%, #d32f2f 100%);
        }
        
        .summary-card h3 {
            font-size: 1.2em;
            margin-bottom: 10px;
        }
        
        .summary-card .value {
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 5px;
        }
        
        .summary-card .label {
            font-size: 0.9em;
            opacity: 0.9;
        }
        
        .batch-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        
        .batch-table th,
        .batch-table td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        
        .batch-table th {
            background: #f8f9fa;
            font-weight: 600;
            color: #2c3e50;
        }
        
        .batch-table tr:hover {
            background: #f8f9fa;
        }
        
        .status-completed {
            color: #4CAF50;
            font-weight: bold;
        }
        
        .status-failed {
            color: #f44336;
            font-weight: bold;
        }
        
        .recommendations-list {
            list-style: none;
        }
        
        .recommendations-list li {
            background: #f8f9fa;
            margin: 10px 0;
            padding: 15px;
            border-radius: 5px;
            border-left: 4px solid #667eea;
        }
        
        .pattern-analysis {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
        }
        
        .pattern-item {
            background: white;
            padding: 15px;
            margin: 10px 0;
            border-radius: 5px;
            border-left: 4px solid #667eea;
        }
        
        .pattern-item.critical {
            border-left-color: #f44336;
        }
        
        .pattern-item.high {
            border-left-color: #ff9800;
        }
        
        .pattern-item.medium {
            border-left-color: #2196F3;
        }
        
        .chart-container {
            margin: 30px 0;
            text-align: center;
        }
        
        .report-footer {
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #eee;
            color: #7f8c8d;
        }
        
        h2 {
            color: #2c3e50;
            margin: 30px 0 20px 0;
            font-size: 1.8em;
        }
        
        .section {
            margin-bottom: 40px;
        }
        """
    
    def _get_chart_scripts(self) -> str:
        """Get JavaScript for charts (Chart.js CDN)."""
        return """
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        """
    
    def _build_summary_cards(self, summary: Dict[str, Any]) -> str:
        """Build summary cards HTML."""
        
        success_rate = summary.get('success_rate', 0.0)
        avg_quality = summary.get('average_quality', 0.0)
        
        # Determine card classes based on metrics
        success_class = 'success' if success_rate >= 0.9 else 'warning' if success_rate >= 0.7 else 'error'
        quality_class = 'success' if avg_quality >= 0.8 else 'warning' if avg_quality >= 0.6 else 'error'
        
        return f"""
        <div class="summary-cards">
            <div class="summary-card">
                <h3>Total Evaluations</h3>
                <div class="value">{summary.get('total_evaluations', 0)}</div>
                <div class="label">Scenarios Tested</div>
            </div>
            <div class="summary-card {success_class}">
                <h3>Success Rate</h3>
                <div class="value">{success_rate:.1%}</div>
                <div class="label">{summary.get('successful_evaluations', 0)} / {summary.get('total_evaluations', 0)}</div>
            </div>
            <div class="summary-card {quality_class}">
                <h3>Avg Quality</h3>
                <div class="value">{avg_quality:.2f}</div>
                <div class="label">Conversation Quality</div>
            </div>
            <div class="summary-card">
                <h3>Total Cost</h3>
                <div class="value">${summary.get('total_cost', 0.0):.3f}</div>
                <div class="label">LLM Evaluation Cost</div>
            </div>
        </div>
        """
    
    def _build_charts_section(self, batch_results: List[BatchResult]) -> str:
        """Build charts section with JavaScript charts."""
        
        if not batch_results:
            return ""
        
        # Prepare data for charts
        batch_labels = [f"Batch {i+1}" for i in range(len(batch_results))]
        success_rates = [
            b.successful_evaluations / max(1, b.successful_evaluations + b.failed_evaluations) 
            for b in batch_results
        ]
        quality_scores = [b.average_evaluation_score for b in batch_results]
        costs = [b.total_llm_cost for b in batch_results]
        
        return f"""
        <div class="section">
            <h2>📈 Performance Charts</h2>
            <div class="chart-container">
                <canvas id="successRateChart" width="400" height="200"></canvas>
            </div>
            <div class="chart-container">
                <canvas id="qualityChart" width="400" height="200"></canvas>
            </div>
            <div class="chart-container">
                <canvas id="costChart" width="400" height="200"></canvas>
            </div>
        </div>
        
        <script>
            // Success Rate Chart
            const successCtx = document.getElementById('successRateChart').getContext('2d');
            new Chart(successCtx, {{
                type: 'line',
                data: {{
                    labels: {json.dumps(batch_labels)},
                    datasets: [{{
                        label: 'Success Rate',
                        data: {json.dumps(success_rates)},
                        borderColor: '#4CAF50',
                        backgroundColor: 'rgba(76, 175, 80, 0.1)',
                        tension: 0.4
                    }}]
                }},
                options: {{
                    responsive: true,
                    plugins: {{
                        title: {{
                            display: true,
                            text: 'Success Rate Over Time'
                        }}
                    }},
                    scales: {{
                        y: {{
                            beginAtZero: true,
                            max: 1.0
                        }}
                    }}
                }}
            }});
            
            // Quality Chart
            const qualityCtx = document.getElementById('qualityChart').getContext('2d');
            new Chart(qualityCtx, {{
                type: 'bar',
                data: {{
                    labels: {json.dumps(batch_labels)},
                    datasets: [{{
                        label: 'Average Quality Score',
                        data: {json.dumps(quality_scores)},
                        backgroundColor: '#2196F3',
                        borderColor: '#1976D2',
                        borderWidth: 1
                    }}]
                }},
                options: {{
                    responsive: true,
                    plugins: {{
                        title: {{
                            display: true,
                            text: 'Quality Scores by Batch'
                        }}
                    }},
                    scales: {{
                        y: {{
                            beginAtZero: true,
                            max: 1.0
                        }}
                    }}
                }}
            }});
            
            // Cost Chart
            const costCtx = document.getElementById('costChart').getContext('2d');
            new Chart(costCtx, {{
                type: 'line',
                data: {{
                    labels: {json.dumps(batch_labels)},
                    datasets: [{{
                        label: 'Cost ($)',
                        data: {json.dumps(costs)},
                        borderColor: '#ff9800',
                        backgroundColor: 'rgba(255, 152, 0, 0.1)',
                        tension: 0.4
                    }}]
                }},
                options: {{
                    responsive: true,
                    plugins: {{
                        title: {{
                            display: true,
                            text: 'LLM Costs Over Time'
                        }}
                    }},
                    scales: {{
                        y: {{
                            beginAtZero: true
                        }}
                    }}
                }}
            }});
        </script>
        """
    
    def _build_batch_results_table(self, batch_results: List[BatchResult]) -> str:
        """Build batch results table HTML."""
        
        if not batch_results:
            return "<p>No batch results to display.</p>"
        
        table_rows = []
        for i, batch in enumerate(batch_results, 1):
            status_class = 'status-completed' if batch.status.value == 'completed' else 'status-failed'
            success_rate = batch.successful_evaluations / max(1, batch.successful_evaluations + batch.failed_evaluations)
            
            table_rows.append(f"""
            <tr>
                <td>Batch {i}</td>
                <td><span class="{status_class}">{batch.status.value.title()}</span></td>
                <td>{batch.successful_evaluations + batch.failed_evaluations}</td>
                <td>{success_rate:.1%}</td>
                <td>{batch.average_evaluation_score:.2f}</td>
                <td>${batch.total_llm_cost:.3f}</td>
                <td>{batch.total_duration_seconds:.1f}s</td>
            </tr>
            """)
        
        return f"""
        <table class="batch-table">
            <thead>
                <tr>
                    <th>Batch</th>
                    <th>Status</th>
                    <th>Total Evaluations</th>
                    <th>Success Rate</th>
                    <th>Avg Quality</th>
                    <th>Cost</th>
                    <th>Duration</th>
                </tr>
            </thead>
            <tbody>
                {''.join(table_rows)}
            </tbody>
        </table>
        """
    
    def _build_pattern_analysis_section(self, pattern_analysis: PatternAnalysis) -> str:
        """Build pattern analysis section HTML."""
        
        patterns_html = []
        for pattern in pattern_analysis.identified_patterns[:10]:  # Limit to top 10
            severity_class = pattern.impact_severity
            patterns_html.append(f"""
            <div class="pattern-item {severity_class}">
                <h4>{html.escape(pattern.title)}</h4>
                <p><strong>Type:</strong> {pattern.pattern_type.value.replace('_', ' ').title()}</p>
                <p><strong>Description:</strong> {html.escape(pattern.description)}</p>
                <p><strong>Confidence:</strong> {pattern.confidence_score:.1%}</p>
                <p><strong>Impact:</strong> {pattern.impact_severity.title()}</p>
                {self._build_recommendations_list(pattern.recommendations)}
            </div>
            """)
        
        return f"""
        <div class="section">
            <h2>🧠 Pattern Analysis</h2>
            <div class="pattern-analysis">
                <p><strong>System Health:</strong> {pattern_analysis.overall_system_health.title()}</p>
                <p><strong>Patterns Identified:</strong> {len(pattern_analysis.identified_patterns)}</p>
                <p><strong>Analysis Period:</strong> {pattern_analysis.data_period[0].strftime("%Y-%m-%d")} to {pattern_analysis.data_period[1].strftime("%Y-%m-%d")}</p>
                
                <h3>Identified Patterns</h3>
                {''.join(patterns_html)}
            </div>
        </div>
        """
    
    def _build_recommendations_section(
        self, 
        batch_results: List[BatchResult], 
        pattern_analysis: Optional[PatternAnalysis]
    ) -> str:
        """Build recommendations section HTML."""
        
        recommendations = []
        
        # Recommendations from batch results
        for batch in batch_results:
            recommendations.extend(batch.recommendations)
        
        # Recommendations from pattern analysis
        if pattern_analysis:
            for rec in pattern_analysis.improvement_recommendations:
                recommendations.append(rec.title)
        
        # Remove duplicates and limit
        unique_recommendations = list(dict.fromkeys(recommendations))[:10]
        
        if not unique_recommendations:
            return "<p>No specific recommendations available.</p>"
        
        return self._build_recommendations_list(unique_recommendations)
    
    def _build_recommendations_list(self, recommendations: List[str]) -> str:
        """Build recommendations list HTML."""
        
        rec_items = [f"<li>{html.escape(rec)}</li>" for rec in recommendations]
        
        return f"""
        <ul class="recommendations-list">
            {''.join(rec_items)}
        </ul>
        """
    
    def _batch_to_summary(self, batch: BatchResult) -> Dict[str, Any]:
        """Convert batch result to summary format."""
        return {
            "batch_id": batch.batch_id,
            "status": batch.status.value,
            "successful_evaluations": batch.successful_evaluations,
            "failed_evaluations": batch.failed_evaluations,
            "average_evaluation_score": batch.average_evaluation_score,
            "total_llm_cost": batch.total_llm_cost,
            "duration_seconds": batch.total_duration_seconds
        }
    
    def _load_report_templates(self) -> Dict[str, str]:
        """Load report templates (placeholder for future customization)."""
        return {
            "default": "default_template",
            "executive": "executive_summary_template",
            "technical": "technical_detailed_template"
        }


# Utility functions for CLI integration

def create_live_monitor() -> LiveMonitor:
    """Create a live monitor instance."""
    return LiveMonitor()


def generate_evaluation_report(
    batch_results: List[BatchResult],
    output_path: str,
    pattern_analysis: Optional[PatternAnalysis] = None,
    title: str = "Evaluation Report"
):
    """Generate and export evaluation report."""
    dashboard = EvaluationDashboard()
    dashboard.export_report(batch_results, output_path, pattern_analysis, title)


def print_live_progress(metrics: DashboardMetrics):
    """Print live progress updates to console."""
    print(f"\r📊 Live Metrics | "
          f"Running: {metrics.current_evaluations_running} | "
          f"Completed: {metrics.total_evaluations_completed} | "
          f"Success Rate: {metrics.success_rate:.1%} | "
          f"Avg Quality: {metrics.average_quality_score:.2f} | "
          f"Cost: ${metrics.total_cost:.3f}", 
          end="", flush=True) 