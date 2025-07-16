"""essay_agent.workflows.qa_pipeline

Multi-stage QA validation pipeline with comprehensive quality checks.
Orchestrates plagiarism detection, cliche identification, outline alignment, and final polish validation.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from essay_agent.workflows.base import WorkflowNode, WorkflowState
from essay_agent.workflows import register_workflow_node
from essay_agent.tools.validation_tools import (
    PlagiarismValidator, ClicheDetectionValidator, 
    OutlineAlignmentValidator, FinalPolishValidator,
    ComprehensiveValidationResult, ValidationResult, ValidationSeverity, ValidationIssue
)
from essay_agent.models import EssayPlan, Phase
from essay_agent.utils.logging import tool_trace


class QAValidationPipeline:
    """Pipeline for comprehensive essay QA validation."""
    
    def __init__(self, early_stopping: bool = True):
        """Initialize QA validation pipeline."""
        self.early_stopping = early_stopping
        self.validators = [
            PlagiarismValidator(),
            ClicheDetectionValidator(),
            OutlineAlignmentValidator(),
            FinalPolishValidator()
        ]
    
    def run_validation(self, essay: str, context: Dict[str, Any]) -> ComprehensiveValidationResult:
        """Run complete validation pipeline."""
        start_time = time.time()
        validator_results = {}
        all_issues = []
        total_score = 0.0
        validators_run = 0
        
        for validator in self.validators:
            try:
                # Run individual validator
                result = validator.validate(essay, context)
                validator_results[validator.name] = result
                all_issues.extend(result.issues)
                total_score += result.score
                validators_run += 1
                
                # Stop early if critical failure and early stopping is enabled
                critical_issues = [issue for issue in result.issues if issue.severity == ValidationSeverity.CRITICAL]
                if self.early_stopping and critical_issues:
                    break
                    
            except Exception as e:
                print(f"Validator {validator.name} failed: {e}")
                # Continue with other validators
                continue
        
        # Calculate overall results
        overall_score = total_score / validators_run if validators_run > 0 else 0.0
        overall_status = self._determine_overall_status(validator_results, overall_score)
        recommendations = self._generate_recommendations(all_issues)
        
        return ComprehensiveValidationResult(
            overall_status=overall_status,
            overall_score=overall_score,
            validator_results=validator_results,
            issues=all_issues,
            recommendations=recommendations,
            execution_time=time.time() - start_time,
            validators_run=validators_run
        )
    
    def _determine_overall_status(self, validator_results: Dict[str, ValidationResult], overall_score: float) -> str:
        """Determine overall validation status."""
        # Check for critical issues
        for result in validator_results.values():
            critical_issues = [issue for issue in result.issues if issue.severity == ValidationSeverity.CRITICAL]
            if critical_issues:
                return "fail"
        
        # Check overall score
        if overall_score >= 0.8:
            return "pass"
        elif overall_score >= 0.6:
            return "warning"
        else:
            return "fail"
    
    def _generate_recommendations(self, issues: List[ValidationIssue]) -> List[str]:
        """Generate recommendations based on issues."""
        recommendations = []
        
        # Group issues by type
        issue_types = {}
        for issue in issues:
            if issue.issue_type not in issue_types:
                issue_types[issue.issue_type] = []
            issue_types[issue.issue_type].append(issue)
        
        # Generate recommendations for each issue type
        for issue_type, type_issues in issue_types.items():
            if issue_type == "potential_plagiarism":
                recommendations.append("Review flagged sections for originality and add more personal details")
            elif issue_type == "cliche":
                recommendations.append("Replace identified cliches with more original and specific language")
            elif issue_type == "structure_mismatch" or issue_type == "content_gap":
                recommendations.append("Improve alignment between essay content and planned outline structure")
            elif issue_type in ["grammar_error", "formatting_error", "word_count_error"]:
                recommendations.append("Address grammar, word count, and formatting issues before submission")
        
        return recommendations


@register_workflow_node("qa_validation")
class QAValidationNode(WorkflowNode):
    """Workflow node for QA validation pipeline."""
    
    def __init__(self, early_stopping: bool = True):
        super().__init__()
        self.pipeline = QAValidationPipeline(early_stopping=early_stopping)
    
    def get_name(self) -> str:
        """Get node name."""
        return "qa_validation"
    
    async def execute(self, state: EssayPlan) -> Dict[str, Any]:
        """Execute QA validation pipeline."""
        with tool_trace("qa_validation"):
            # Get essay text
            essay_text = self._get_essay_text(state)
            
            if not essay_text:
                return {
                    "validation_results": {
                        "overall_status": "fail",
                        "overall_score": 0.0,
                        "issues": [
                            {
                                "type": "missing_essay",
                                "severity": "critical",
                                "message": "No essay text found for validation",
                                "suggestion": "Generate essay content before validation"
                            }
                        ],
                        "recommendations": ["Generate essay content before validation"]
                    }
                }
            
            # Prepare validation context
            context = self._prepare_validation_context(state)
            
            # Run validation
            result = self.pipeline.run_validation(essay_text, context)
            
            # Convert result to dict for state updates
            return {
                "validation_results": {
                    "overall_status": result.overall_status,
                    "overall_score": result.overall_score,
                    "validators_run": result.validators_run,
                    "issues": [
                        {
                            "type": issue.issue_type,
                            "severity": issue.severity,
                            "message": issue.message,
                            "suggestion": issue.suggestion
                        }
                        for issue in result.issues
                    ],
                    "recommendations": result.recommendations,
                    "execution_time": result.execution_time
                }
            }
    
    def _get_essay_text(self, state: EssayPlan) -> str:
        """Extract essay text from state."""
        tool_outputs = state.data.get("tool_outputs", {})
        
        # Check polish output first, then draft
        if "polish" in tool_outputs:
            result = tool_outputs["polish"]
            if isinstance(result, dict) and "polished_essay" in result:
                return result["polished_essay"]
        
        if "draft" in tool_outputs:
            result = tool_outputs["draft"]
            if isinstance(result, dict) and "essay_text" in result:
                return result["essay_text"]
        
        return ""
    
    def _prepare_validation_context(self, state: EssayPlan) -> Dict[str, Any]:
        """Prepare context for validation."""
        context = state.data.get("context", {}).copy()
        
        # Add tool outputs to context
        tool_outputs = state.data.get("tool_outputs", {})
        
        # Add outline if available
        if "outline" in tool_outputs:
            context["outline"] = tool_outputs["outline"]
        
        # Add other relevant context
        if "brainstorm" in tool_outputs:
            context["brainstorm"] = tool_outputs["brainstorm"]
        
        return context


@register_workflow_node("qa_gate")
class QAGateNode(WorkflowNode):
    """Quality gate node that routes based on validation results."""
    
    def __init__(self, pass_threshold: float = 0.8):
        super().__init__()
        self.pass_threshold = pass_threshold
    
    def get_name(self) -> str:
        """Get node name."""
        return "qa_gate"
    
    async def execute(self, state: EssayPlan) -> Dict[str, Any]:
        """Execute quality gate logic."""
        with tool_trace("qa_gate"):
            # Get validation results
            validation_results = state.data.get("validation_results", {})
            
            if not validation_results:
                return {
                    "qa_decision": "retry",
                    "qa_reason": "No validation results found"
                }
            
            overall_status = validation_results.get("overall_status", "fail")
            overall_score = validation_results.get("overall_score", 0.0)
            issues = validation_results.get("issues", [])
            
            # Check for critical issues
            critical_issues = [issue for issue in issues if issue.get("severity") == "critical"]
            if critical_issues:
                return {
                    "qa_decision": "fail",
                    "qa_reason": "Critical validation issues found",
                    "critical_issues": critical_issues
                }
            
            # Check overall score
            if overall_score >= self.pass_threshold:
                return {
                    "qa_decision": "pass",
                    "qa_reason": f"Validation passed with score {overall_score:.2f}"
                }
            elif overall_score >= 0.6:
                return {
                    "qa_decision": "warning",
                    "qa_reason": f"Validation passed with warnings (score: {overall_score:.2f})"
                }
            else:
                return {
                    "qa_decision": "fail",
                    "qa_reason": f"Validation failed with score {overall_score:.2f}"
                }


# ---------------------------------------------------------------------------
# Utility Functions
# ---------------------------------------------------------------------------

def should_run_qa_validation(state: EssayPlan) -> bool:
    """Determine if QA validation should run."""
    # Check if we have content to validate
    tool_outputs = state.data.get("tool_outputs", {})
    
    # Need either draft or polish output
    has_draft = "draft" in tool_outputs
    has_polish = "polish" in tool_outputs
    
    return has_draft or has_polish


def get_qa_validation_recommendations(state: EssayPlan) -> List[str]:
    """Get QA validation recommendations from state."""
    validation_results = state.data.get("validation_results", {})
    return validation_results.get("recommendations", []) 