"""essay_agent.tools.validation_tools

Comprehensive validation tools for the QA pipeline.
Includes plagiarism detection, cliche identification, outline alignment, and final polish validation.
"""

from __future__ import annotations

import json
import re
import time
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from difflib import SequenceMatcher

from pydantic import BaseModel, Field

from essay_agent.tools.base import ValidatedTool
from essay_agent.tools import register_tool
from essay_agent.llm_client import call_llm, get_chat_llm
from essay_agent.prompts.validation import (
    PLAGIARISM_DETECTION_PROMPT,
    CLICHE_DETECTION_PROMPT,
    OUTLINE_ALIGNMENT_PROMPT,
    FINAL_POLISH_PROMPT,
    COMPREHENSIVE_VALIDATION_PROMPT,
)
from essay_agent.response_parser import safe_parse, pydantic_parser
from essay_agent.prompts.templates import render_template


def simple_json_parse(text: str) -> Dict[str, Any]:
    """Improved JSON parsing for validation responses."""
    try:
        # First try direct JSON parsing
        if isinstance(text, dict):
            return text
        
        # Clean the text first
        text = str(text).strip()
        
        # Try to extract JSON from markdown code blocks
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
        if json_match:
            text = json_match.group(1)
        
        # Try to parse as JSON
        parsed = json.loads(text)
        
        # Ensure it's a dictionary
        if isinstance(parsed, dict):
            return parsed
        else:
            print(f"Warning: Parsed JSON is not a dict: {type(parsed)}")
            return {"error": "Invalid JSON structure"}
            
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
        print(f"Raw text: {text[:200]}...")
        
        # Try to extract key-value pairs with regex as fallback
        fallback_dict = {}
        
        # Look for common patterns in the response
        if "similarity_score" in text.lower():
            score_match = re.search(r'"similarity_score":\s*([0-9.]+)', text)
            if score_match:
                fallback_dict["similarity_score"] = float(score_match.group(1))
        
        if "authenticity_score" in text.lower():
            score_match = re.search(r'"authenticity_score":\s*([0-9.]+)', text)
            if score_match:
                fallback_dict["authenticity_score"] = float(score_match.group(1))
        
        if "overall_score" in text.lower():
            score_match = re.search(r'"overall_score":\s*([0-9.]+)', text)
            if score_match:
                fallback_dict["overall_score"] = float(score_match.group(1))
        
        if "assessment" in text.lower():
            assessment_match = re.search(r'"(?:overall_)?assessment":\s*"([^"]+)"', text)
            if assessment_match:
                fallback_dict["overall_assessment"] = assessment_match.group(1)
        
        # If we found some data, return it
        if fallback_dict:
            print(f"Using fallback parsing: {fallback_dict}")
            return fallback_dict
            
        # Last resort: return indicator that parsing failed
        return {"parse_error": str(e)}
    
    except Exception as e:
        print(f"Unexpected error in JSON parsing: {e}")
        return {"parse_error": str(e)}


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

class ValidationSeverity(str, Enum):
    """Severity levels for validation issues."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ValidationIssue(BaseModel):
    """Individual validation issue."""
    issue_type: str
    severity: ValidationSeverity
    message: str
    text_excerpt: str = ""
    line_number: Optional[int] = None
    suggestion: str = ""


class ValidationResult(BaseModel):
    """Result of validation process."""
    validator_name: str
    passed: bool
    score: float = Field(ge=0.0, le=1.0)
    issues: List[ValidationIssue] = Field(default_factory=list)
    execution_time: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ComprehensiveValidationResult(BaseModel):
    """Result of comprehensive validation pipeline."""
    readiness_score: float = Field(..., ge=0.0, le=10.0)
    is_ready_for_submission: bool
    summary: str
    passed_checks: List[str]
    failed_checks: List[str]


# ---------------------------------------------------------------------------
# Base Validator
# ---------------------------------------------------------------------------

class BaseValidator(ABC):
    """Base class for all validators."""
    
    def __init__(self, name: str, **kwargs):
        self.name = name
        self.config = kwargs
    
    @abstractmethod
    def validate(self, essay: str, context: Dict[str, Any]) -> ValidationResult:
        """Validate essay and return result."""
        pass
    
    def _create_issue(self, issue_type: str, severity: ValidationSeverity, 
                     message: str, text_excerpt: str = "", line_number: Optional[int] = None, 
                     suggestion: str = "") -> ValidationIssue:
        """Helper to create validation issues."""
        return ValidationIssue(
            issue_type=issue_type,
            severity=severity,
            message=message,
            text_excerpt=text_excerpt,
            line_number=line_number,
            suggestion=suggestion
        )
    
    def _count_words(self, text: str) -> int:
        """Count words in text."""
        return len(text.split())


# ---------------------------------------------------------------------------
# Plagiarism Validator
# ---------------------------------------------------------------------------

class PlagiarismValidator(BaseValidator):
    """Detects potential plagiarism using text similarity analysis."""
    
    def __init__(self, threshold: float = 0.15):
        super().__init__("plagiarism", threshold=threshold)
        self.similarity_threshold = threshold
    
    def validate(self, essay: str, context: Dict[str, Any]) -> ValidationResult:
        """Validate essay for potential plagiarism."""
        start_time = time.time()
        issues = []
        error_info = None
        
        try:
            # Use LLM for sophisticated plagiarism detection
            llm = get_chat_llm()
            prompt = PLAGIARISM_DETECTION_PROMPT.format(
                essay_text=essay,
                context=json.dumps(context, default=str)
            )
            llm_response = call_llm(llm, prompt)
            
            # Handle both string and dict responses (for testing)
            if isinstance(llm_response, dict):
                parsed_result = llm_response
            else:
                parsed_result = simple_json_parse(llm_response)
            
            # Check if parsing was successful
            if parsed_result and isinstance(parsed_result, dict) and "parse_error" not in parsed_result:
                # Parse LLM response
                similarity_score = parsed_result.get("similarity_score", 0.5)
                authenticity_score = parsed_result.get("authenticity_score", 0.5)
                flagged_sections = parsed_result.get("flagged_sections", [])
                overall_assessment = parsed_result.get("overall_assessment", "warning")
                
                # Calculate overall score
                overall_score = (authenticity_score + (1 - similarity_score)) / 2
                
                # Generate issues for flagged sections
                for section in flagged_sections:
                    severity_map = {
                        "critical": ValidationSeverity.CRITICAL,
                        "high": ValidationSeverity.HIGH,
                        "medium": ValidationSeverity.MEDIUM,
                        "low": ValidationSeverity.LOW
                    }
                    
                    issues.append(ValidationIssue(
                        issue_type="potential_plagiarism",
                        severity=severity_map.get(section.get("severity", "medium"), ValidationSeverity.MEDIUM),
                        message=f"Potential plagiarism detected: {section.get('reason', 'Similar text found')}",
                        text_excerpt=section.get("text", ""),
                        line_number=section.get("line_number"),
                        suggestion=section.get("suggestion", "Rewrite in your own words")
                    ))
                
                # Determine if passed based on assessment and score
                passed = overall_assessment == "pass" and overall_score >= 0.7
                
            else:
                # Fallback to basic similarity check
                print("Using fallback plagiarism detection")
                fallback_score, fallback_issues = self._basic_similarity_check(essay)
                passed = fallback_score >= 0.7
                overall_score = fallback_score
                issues.extend(fallback_issues)
                
        except Exception as e:
            # LLM call failed, use fallback
            print(f"Plagiarism detection error: {e}")
            fallback_score, fallback_issues = self._basic_similarity_check(essay)
            passed = fallback_score >= 0.7
            overall_score = fallback_score
            issues.extend(fallback_issues)
            error_info = str(e)
        
        return ValidationResult(
            validator_name=self.name,
            passed=passed,
            score=overall_score,
            issues=issues,
            execution_time=time.time() - start_time,
            metadata={"error": error_info}
        )
    
    def _basic_similarity_check(self, essay: str) -> tuple[float, List[ValidationIssue]]:
        """Basic similarity check as fallback."""
        issues = []
        
        # Check for very generic phrases
        generic_phrases = [
            "this experience taught me",
            "i learned that",
            "this changed my perspective",
            "i realized that",
            "from this experience"
        ]
        
        generic_count = 0
        for phrase in generic_phrases:
            if phrase in essay.lower():
                generic_count += 1
        
        # Calculate score based on generic phrase density
        total_words = self._count_words(essay)
        generic_density = generic_count / max(total_words / 100, 1)  # Per 100 words
        
        if generic_density > 0.5:
            issues.append(self._create_issue(
                issue_type="generic_language",
                severity=ValidationSeverity.MEDIUM,
                message="Essay contains many generic phrases",
                text_excerpt="Multiple generic phrases detected",
                suggestion="Add more specific personal details and unique perspectives"
            ))
        
        validation_score = max(0.0, 1.0 - generic_density)
        return validation_score, issues


# ---------------------------------------------------------------------------
# Cliche Detection Validator
# ---------------------------------------------------------------------------

class ClicheDetectionValidator(BaseValidator):
    """Identifies overused college essay phrases and cliches."""
    
    def __init__(self, severity_threshold: int = 3):
        super().__init__("cliche_detection", severity_threshold=severity_threshold)
        self.severity_threshold = severity_threshold
        self.common_cliches = self._load_cliche_database()
    
    def _load_cliche_database(self) -> Dict[str, int]:
        """Load common college essay cliches with severity ratings."""
        return {
            "changed my life": 5,
            "life-changing experience": 5,
            "life changing": 5,
            "passion for helping others": 4,
            "make a difference": 4,
            "making a difference": 4,
            "overcome obstacles": 3,
            "overcame obstacles": 3,
            "perseverance pays off": 3,
            "diverse background": 3,
            "unique perspective": 3,
            "leadership skills": 3,
            "team player": 3,
            "hard work pays off": 3,
            "never give up": 4,
            "follow your dreams": 4,
            "anything is possible": 4,
            "learning experience": 2,
            "valuable lesson": 2,
            "comfort zone": 3,
            "out of my comfort zone": 3,
            "step out of my comfort zone": 3,
            "journey of discovery": 4,
            "found my calling": 4,
            "believe in yourself": 4,
            "reach for the stars": 4,
            "sky is the limit": 4,
            "dream come true": 3,
            "work hard, play hard": 3,
            "give back to the community": 3,
            "bright future ahead": 3,
            "walked in my shoes": 3,
        }
    
    def validate(self, essay: str, context: Dict[str, Any]) -> ValidationResult:
        """Validate essay for cliches."""
        start_time = time.time()
        issues = []
        error_info = None
        
        try:
            # Use LLM for sophisticated cliche detection
            llm = get_chat_llm()
            prompt = CLICHE_DETECTION_PROMPT.format(
                essay_text=essay,
                context=json.dumps(context, default=str)
            )
            llm_response = call_llm(llm, prompt)
            
            # Handle both string and dict responses (for testing)
            if isinstance(llm_response, dict):
                parsed_result = llm_response
            else:
                parsed_result = simple_json_parse(llm_response)
            
            # Check if parsing was successful
            if parsed_result and isinstance(parsed_result, dict) and "parse_error" not in parsed_result:
                # Parse LLM response
                cliches_found = parsed_result.get("cliches_found", [])
                cliche_density = parsed_result.get("cliche_density", 0.5)
                overall_originality = parsed_result.get("overall_originality", 0.5)
                assessment = parsed_result.get("assessment", "warning")
                
                # Calculate overall score
                overall_score = overall_originality
                
                # Generate issues for detected cliches
                for cliche in cliches_found:
                    severity_map = {
                        5: ValidationSeverity.CRITICAL,
                        4: ValidationSeverity.HIGH,
                        3: ValidationSeverity.MEDIUM,
                        2: ValidationSeverity.LOW,
                        1: ValidationSeverity.LOW
                    }
                    
                    cliche_severity = cliche.get("severity", 3)
                    issues.append(ValidationIssue(
                        issue_type="cliche",
                        severity=severity_map.get(cliche_severity, ValidationSeverity.MEDIUM),
                        message=f"Cliche detected: '{cliche.get('text', '')}'",
                        text_excerpt=cliche.get("text", ""),
                        line_number=cliche.get("line_number"),
                        suggestion=cliche.get("suggestion", "Use more original and specific language")
                    ))
                
                # Determine if passed
                passed = assessment == "pass" and overall_score >= 0.7
                
            else:
                # Fallback to basic cliche check
                print("Using fallback cliche detection")
                fallback_score, fallback_issues = self._basic_cliche_check(essay)
                passed = fallback_score >= 0.7
                overall_score = fallback_score
                issues.extend(fallback_issues)
                
        except Exception as e:
            # LLM call failed, use fallback
            print(f"Cliche detection error: {e}")
            fallback_score, fallback_issues = self._basic_cliche_check(essay)
            passed = fallback_score >= 0.7
            overall_score = fallback_score
            issues.extend(fallback_issues)
            error_info = str(e)
        
        return ValidationResult(
            validator_name=self.name,
            passed=passed,
            score=overall_score,
            issues=issues,
            execution_time=time.time() - start_time,
            metadata={"error": error_info}
        )
    
    def _basic_cliche_check(self, essay: str) -> tuple[float, List[ValidationIssue]]:
        """Basic cliche check as fallback."""
        issues = []
        essay_lower = essay.lower()
        found_cliches = []
        
        # Check for cliches in database
        for cliche, severity in self.common_cliches.items():
            if cliche in essay_lower:
                found_cliches.append((cliche, severity))
                
                # Create issue if severity is high enough
                if severity >= self.severity_threshold:
                    sev_map = {5: ValidationSeverity.CRITICAL, 4: ValidationSeverity.HIGH, 3: ValidationSeverity.MEDIUM}
                    
                    issues.append(self._create_issue(
                        issue_type="cliche",
                        severity=sev_map.get(severity, ValidationSeverity.MEDIUM),
                        message=f"Common cliche detected: '{cliche}'",
                        text_excerpt=cliche,
                        suggestion="Consider more original phrasing"
                    ))
        
        # Calculate score based on cliche density and severity
        total_words = self._count_words(essay)
        cliche_impact = sum(severity for _, severity in found_cliches)
        cliche_density = cliche_impact / max(total_words / 100, 1)  # Per 100 words
        
        validation_score = max(0.0, 1.0 - (cliche_density * 0.1))
        return validation_score, issues


# ---------------------------------------------------------------------------
# Outline Alignment Validator
# ---------------------------------------------------------------------------

class OutlineAlignmentValidator(BaseValidator):
    """Verifies essay follows planned outline structure."""
    
    def __init__(self, min_coverage: float = 0.8):
        super().__init__("outline_alignment", min_coverage=min_coverage)
        self.coverage_threshold = min_coverage
    
    def validate(self, essay: str, context: Dict[str, Any]) -> ValidationResult:
        """Validate essay alignment with outline."""
        start_time = time.time()
        issues = []
        error_info = None
        
        try:
            # Check if outline exists in context
            if "outline" not in context:
                issues.append(ValidationIssue(
                    issue_type="missing_outline",
                    severity=ValidationSeverity.MEDIUM,
                    message="No outline provided for alignment check",
                    text_excerpt="",
                    suggestion="Provide outline for alignment validation"
                ))
                return ValidationResult(
                    validator_name=self.name,
                    passed=False,
                    score=0.5,
                    issues=issues,
                    execution_time=time.time() - start_time,
                    metadata={"error": "No outline provided"}
                )
            
            # Use LLM for sophisticated outline alignment checking
            llm = get_chat_llm()
            prompt = OUTLINE_ALIGNMENT_PROMPT.format(
                essay_text=essay,
                context=json.dumps(context, default=str)
            )
            llm_response = call_llm(llm, prompt)
            
            # Handle both string and dict responses (for testing)
            if isinstance(llm_response, dict):
                parsed_result = llm_response
            else:
                parsed_result = simple_json_parse(llm_response)
            
            # Check if parsing was successful
            if parsed_result and isinstance(parsed_result, dict) and "parse_error" not in parsed_result:
                # Parse LLM response
                overall_alignment = parsed_result.get("overall_alignment", 0.5)
                structural_flow = parsed_result.get("structural_flow", 0.5)
                section_coverage = parsed_result.get("section_coverage", {})
                missing_elements = parsed_result.get("missing_elements", [])
                
                # Calculate overall score
                overall_score = (overall_alignment + structural_flow) / 2
                
                # Generate issues for structure problems
                for section, coverage_info in section_coverage.items():
                    if isinstance(coverage_info, dict):
                        coverage = coverage_info.get("coverage_percentage", 0)
                        if coverage < 70:  # Less than 70% coverage
                            issues.append(ValidationIssue(
                                issue_type="structure_mismatch",
                                severity=ValidationSeverity.MEDIUM,
                                message=f"Section '{section}' has low coverage ({coverage}%)",
                                text_excerpt=coverage_info.get("found_content", ""),
                                suggestion="Align content with planned outline"
                            ))
                
                # Generate issues for missing elements
                for element in missing_elements:
                    issues.append(ValidationIssue(
                        issue_type="content_gap",
                        severity=ValidationSeverity.MEDIUM,
                        message=f"Missing element: {element}",
                        text_excerpt="",
                        suggestion="Add missing content from outline"
                    ))
                
                # Determine if passed
                passed = overall_score >= 0.7 and len(issues) == 0
                
            else:
                # Fallback to basic outline check
                print("Using fallback outline alignment check")
                outline = context.get("outline", {})
                fallback_score, fallback_issues = self._basic_outline_check(essay, outline)
                passed = fallback_score >= 0.7
                overall_score = fallback_score
                issues.extend(fallback_issues)
                
        except Exception as e:
            # LLM call failed, use fallback
            print(f"Outline alignment error: {e}")
            outline = context.get("outline", {})
            fallback_score, fallback_issues = self._basic_outline_check(essay, outline)
            passed = fallback_score >= 0.7
            overall_score = fallback_score
            issues.extend(fallback_issues)
            error_info = str(e)
        
        return ValidationResult(
            validator_name=self.name,
            passed=passed,
            score=overall_score,
            issues=issues,
            execution_time=time.time() - start_time,
            metadata={"error": error_info}
        )
    
    def _basic_outline_check(self, essay: str, outline: Dict[str, Any]) -> tuple[float, List[ValidationIssue]]:
        """Basic outline check as fallback."""
        issues = []
        essay_lower = essay.lower()
        
        if not outline:
            issues.append(self._create_issue(
                issue_type="missing_outline",
                severity=ValidationSeverity.MEDIUM,
                message="No outline provided for validation",
                text_excerpt="",
                suggestion="Provide outline structure for alignment check"
            ))
            return 0.5, issues
        
        # Check for presence of outline sections
        sections_found = 0
        total_sections = len(outline)
        
        for section_name, section_content in outline.items():
            if isinstance(section_content, str):
                # Simple keyword matching
                section_words = section_content.lower().split()
                common_words = [word for word in section_words if word in essay_lower and len(word) > 3]
                
                if len(common_words) >= 2:  # At least 2 significant words match
                    sections_found += 1
                else:
                    issues.append(self._create_issue(
                        issue_type="missing_section",
                        severity=ValidationSeverity.MEDIUM,
                        message=f"Outline section '{section_name}' may not be adequately covered",
                        text_excerpt="",
                        suggestion=f"Ensure essay addresses: {section_content}"
                    ))
        
        coverage_ratio = sections_found / total_sections if total_sections > 0 else 0.0
        return coverage_ratio, issues


# ---------------------------------------------------------------------------
# Final Polish Validator
# ---------------------------------------------------------------------------

class FinalPolishValidator(BaseValidator):
    """Comprehensive final quality checks."""
    
    def __init__(self, comprehensive: bool = True):
        super().__init__("final_polish", comprehensive=comprehensive)
        self.comprehensive = comprehensive
    
    def validate(self, essay: str, context: Dict[str, Any]) -> ValidationResult:
        """Validate essay for final polish and submission readiness."""
        start_time = time.time()
        issues = []
        error_info = None
        
        try:
            # Use LLM for comprehensive final polish checking
            llm = get_chat_llm()
            prompt = FINAL_POLISH_PROMPT.format(
                essay_text=essay,
                context=json.dumps(context, default=str)
            )
            llm_response = call_llm(llm, prompt)
            
            # Handle both string and dict responses (for testing)
            if isinstance(llm_response, dict):
                parsed_result = llm_response
            else:
                parsed_result = simple_json_parse(llm_response)
            
            # Check if parsing was successful
            if parsed_result and isinstance(parsed_result, dict) and "parse_error" not in parsed_result:
                # Parse LLM response
                overall_polish = parsed_result.get("overall_polish", 0.5)
                technical_issues = parsed_result.get("technical_issues", [])
                word_count_info = parsed_result.get("word_count", {})
                prompt_adherence = parsed_result.get("prompt_adherence", {})
                submission_ready = parsed_result.get("submission_ready", False)
                
                # Calculate overall score
                overall_score = overall_polish
                
                # Generate issues for technical problems
                for issue in technical_issues:
                    severity_map = {
                        "critical": ValidationSeverity.CRITICAL,
                        "high": ValidationSeverity.HIGH,
                        "medium": ValidationSeverity.MEDIUM,
                        "low": ValidationSeverity.LOW
                    }
                    
                    issues.append(ValidationIssue(
                        issue_type=issue.get("type", "technical_issue"),
                        severity=severity_map.get(issue.get("severity", "medium"), ValidationSeverity.MEDIUM),
                        message=issue.get("description", "Technical issue detected"),
                        text_excerpt=issue.get("text", ""),
                        line_number=issue.get("line_number"),
                        suggestion=issue.get("suggestion", "Fix technical issue")
                    ))
                
                # Check word count issues
                if isinstance(word_count_info, dict):
                    word_status = word_count_info.get("status", "unknown")
                    if word_status == "over":
                        issues.append(ValidationIssue(
                            issue_type="word_count_error",
                            severity=ValidationSeverity.HIGH,
                            message=f"Essay exceeds word limit: {word_count_info.get('actual', 0)} words",
                            text_excerpt="",
                            suggestion="Reduce word count to meet requirements"
                        ))
                    elif word_status == "under":
                        issues.append(ValidationIssue(
                            issue_type="word_count_warning",
                            severity=ValidationSeverity.MEDIUM,
                            message=f"Essay below recommended word count: {word_count_info.get('actual', 0)} words",
                            text_excerpt="",
                            suggestion="Consider expanding content if appropriate"
                        ))
                
                # Determine if passed
                passed = submission_ready and overall_score >= 0.8
                
            else:
                # Fallback to basic polish check
                print("Using fallback polish check")
                fallback_score, fallback_issues = self._basic_polish_check(essay, context)
                passed = fallback_score >= 0.8
                overall_score = fallback_score
                issues.extend(fallback_issues)
                
        except Exception as e:
            # LLM call failed, use fallback
            print(f"Final polish error: {e}")
            fallback_score, fallback_issues = self._basic_polish_check(essay, context)
            passed = fallback_score >= 0.8
            overall_score = fallback_score
            issues.extend(fallback_issues)
            error_info = str(e)
        
        return ValidationResult(
            validator_name=self.name,
            passed=passed,
            score=overall_score,
            issues=issues,
            execution_time=time.time() - start_time,
            metadata={"error": error_info}
        )
    
    def _basic_polish_check(self, essay: str, context: Dict[str, Any]) -> tuple[float, List[ValidationIssue]]:
        """Basic polish check as fallback."""
        issues = []
        
        # Check word count
        word_count = self._count_words(essay)
        word_limit = context.get("word_limit", 650)
        
        if word_count > word_limit * 1.1:  # 10% over limit
            issues.append(self._create_issue(
                issue_type="word_count_error",
                severity=ValidationSeverity.HIGH,
                message=f"Essay exceeds word limit: {word_count} words (limit: {word_limit})",
                text_excerpt="",
                suggestion="Reduce word count to meet requirements"
            ))
        
        # Basic grammar checks
        if essay.count("  ") > 0:  # Double spaces
            issues.append(self._create_issue(
                issue_type="formatting_error",
                severity=ValidationSeverity.LOW,
                message="Double spaces detected",
                text_excerpt="",
                suggestion="Remove extra spaces"
            ))
        
        # Check for very short paragraphs that might indicate formatting issues
        paragraphs = essay.split("\n\n")
        short_paragraphs = [p for p in paragraphs if len(p.strip()) < 50 and len(p.strip()) > 0]
        
        if len(short_paragraphs) > len(paragraphs) * 0.3:  # More than 30% short paragraphs
            issues.append(self._create_issue(
                issue_type="structure_issue",
                severity=ValidationSeverity.LOW,
                message="Many short paragraphs detected",
                text_excerpt="",
                suggestion="Consider combining or expanding short paragraphs"
            ))
        
        # Calculate score based on issues
        issue_penalty = len(issues) * 0.1
        validation_score = max(0.0, 1.0 - issue_penalty)
        
        return validation_score, issues


# ---------------------------------------------------------------------------
# Comprehensive Validation Pipeline
# ---------------------------------------------------------------------------

class QAValidationPipeline:
    """Comprehensive validation pipeline for essays."""
    
    def __init__(self):
        self.validators = [
            PlagiarismValidator(),
            ClicheDetectionValidator(),
            OutlineAlignmentValidator(),
            FinalPolishValidator()
        ]
    
    def run_validation(self, essay: str, context: Dict[str, Any]) -> ComprehensiveValidationResult:
        """Run comprehensive validation on essay."""
        start_time = time.time()
        
        validator_results = {}
        all_issues = []
        total_score = 0.0
        validators_run = 0
        
        # Run each validator
        for validator in self.validators:
            try:
                result = validator.validate(essay, context)
                validator_results[validator.name] = result
                all_issues.extend(result.issues)
                total_score += result.score
                validators_run += 1
                
                # Stop on critical failure
                critical_issues = [issue for issue in result.issues if issue.severity == ValidationSeverity.CRITICAL]
                if critical_issues:
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
            readiness_score=overall_score,
            is_ready_for_submission=overall_status == "pass",
            summary=f"Overall validation score: {overall_score:.2f}",
            passed_checks=recommendations,
            failed_checks=[] # No critical issues in this pipeline
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


# ---------------------------------------------------------------------------
# Tool Registration
# ---------------------------------------------------------------------------

@register_tool("plagiarism_check")
def plagiarism_check(essay: str, context: dict = None) -> dict:
    """Check essay for potential plagiarism."""
    if context is None:
        context = {}
    
    validator = PlagiarismValidator()
    result = validator.validate(essay, context)
    
    return result.model_dump()


@register_tool("cliche_detection")
def cliche_detection(essay: str, context: dict = None) -> dict:
    """Detect cliches in essay."""
    if context is None:
        context = {}
    
    validator = ClicheDetectionValidator()
    result = validator.validate(essay, context)
    
    return result.model_dump()


@register_tool("outline_alignment")
def outline_alignment(essay: str, context: dict = None) -> dict:
    """Check essay alignment with outline."""
    if context is None:
        context = {}
    
    validator = OutlineAlignmentValidator()
    result = validator.validate(essay, context)
    
    return result.model_dump()


@register_tool("final_polish")
def final_polish(essay: str, context: dict = None) -> dict:
    """Final polish validation."""
    if context is None:
        context = {}
    
    validator = FinalPolishValidator()
    result = validator.validate(essay, context)
    
    return result.model_dump()


@register_tool("comprehensive_validation")
class ComprehensiveValidationTool(ValidatedTool):
    """Run a final, comprehensive suite of validation checks on an essay.

    Args:
        essay_text (str): The full text of the essay to validate.
        essay_prompt (str): The prompt the essay is answering.
        outline (str): The essay's outline for structural checks.
    """
    name: str = "comprehensive_validation"
    description: str = "Run a final, comprehensive suite of validation checks on an essay."
    timeout: float = 60.0  # This is a complex, multi-check validation

    def _run(self, *, essay_text: str, essay_prompt: str, outline: str, **_: Any) -> Dict[str, Any]:
        essay_text = str(essay_text).strip()
        essay_prompt = str(essay_prompt).strip()
        outline = str(outline).strip()

        if not essay_text or not essay_prompt or not outline:
            raise ValueError("essay_text, essay_prompt, and outline must not be empty.")

        rendered_prompt = render_template(
            COMPREHENSIVE_VALIDATION_PROMPT,
            essay_text=essay_text,
            essay_prompt=essay_prompt,
            outline=outline,
        )

        llm = get_chat_llm(temperature=0.1)
        raw = call_llm(llm, rendered_prompt)

        parser = pydantic_parser(ComprehensiveValidationResult)
        parsed = safe_parse(parser, raw)
        
        return parsed.model_dump() 