#!/usr/bin/env python3
"""
Tool Reliability Framework
==========================

Comprehensive system to ensure every tool reliably gets correct arguments
and produces consistent, validated outputs. Provides multiple layers of
protection against tool failures and inconsistencies.
"""

import asyncio
import json
import logging
import time
import traceback
from typing import Any, Dict, List, Optional, Type, Union
from dataclasses import dataclass
from enum import Enum
from pydantic import BaseModel, ValidationError

from essay_agent.tools import REGISTRY as TOOL_REGISTRY
from essay_agent.utils.arg_resolver import ArgResolver, MissingRequiredArgError
from essay_agent.prompts.example_registry import EXAMPLE_REGISTRY

logger = logging.getLogger(__name__)

class ReliabilityLevel(Enum):
    """Tool reliability assurance levels."""
    BASIC = "basic"           # Minimal validation
    STANDARD = "standard"     # Input/output validation
    STRICT = "strict"         # Full compliance checking
    PARANOID = "paranoid"     # Maximum validation + monitoring

@dataclass
class ToolExecution:
    """Record of tool execution with full context."""
    tool_name: str
    arguments: Dict[str, Any]
    execution_time: float
    success: bool
    output: Any
    error: Optional[str]
    validation_passed: bool
    reliability_issues: List[str]
    timestamp: float

class ToolReliabilityManager:
    """
    Comprehensive tool reliability management system.
    
    Ensures:
    1. All tools receive correct, validated arguments
    2. All tools produce expected output formats
    3. Failures are handled gracefully with fallbacks
    4. Monitoring and alerting for reliability issues
    """
    
    def __init__(self, reliability_level: ReliabilityLevel = ReliabilityLevel.STANDARD):
        self.reliability_level = reliability_level
        self.arg_resolver = ArgResolver()
        self.execution_history: List[ToolExecution] = []
        self.failure_counts: Dict[str, int] = {}
        self.success_counts: Dict[str, int] = {}
        
        # Load expected output schemas
        self.expected_schemas = self._load_expected_schemas()
        
        # Reliability thresholds
        self.max_failures_per_tool = 3
        self.min_success_rate = 0.95
        
    def _load_expected_schemas(self) -> Dict[str, Any]:
        """Load expected output schemas from example_registry.py."""
        schemas = {}
        for tool_name, example_output in EXAMPLE_REGISTRY.items():
            try:
                parsed = json.loads(example_output)
                schemas[tool_name] = self._extract_schema(parsed)
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON in example_registry for {tool_name}")
                schemas[tool_name] = None
        return schemas
    
    def _extract_schema(self, example: Any) -> Dict[str, str]:
        """Extract schema structure from example output."""
        if isinstance(example, dict):
            return {key: type(value).__name__ for key, value in example.items()}
        elif isinstance(example, list):
            return {"type": "list", "min_length": 1}
        else:
            return {"type": type(example).__name__}
    
    async def execute_tool_safely(
        self, 
        tool_name: str, 
        context: Dict[str, Any],
        user_input: str = "",
        fallback_enabled: bool = True
    ) -> Dict[str, Any]:
        """
        Execute a tool with comprehensive reliability measures.
        
        Args:
            tool_name: Name of tool to execute
            context: Full context including user profile, essay state, etc.
            user_input: User's current input
            fallback_enabled: Whether to use fallbacks on failure
            
        Returns:
            Standardized tool result with reliability metadata
        """
        start_time = time.time()
        execution_record = ToolExecution(
            tool_name=tool_name,
            arguments={},
            execution_time=0,
            success=False,
            output=None,
            error=None,
            validation_passed=False,
            reliability_issues=[],
            timestamp=start_time
        )
        
        try:
            # Phase 1: Argument Resolution & Validation
            arguments = await self._resolve_and_validate_arguments(
                tool_name, context, user_input, execution_record
            )
            
            # Phase 2: Pre-execution Checks
            if not await self._pre_execution_checks(tool_name, arguments, execution_record):
                if fallback_enabled:
                    return await self._execute_fallback(tool_name, context, execution_record)
                else:
                    raise RuntimeError(f"Pre-execution checks failed for {tool_name}")
            
            # Phase 3: Tool Execution
            result = await self._execute_tool_core(tool_name, arguments, execution_record)
            
            # Phase 4: Output Validation & Standardization
            validated_result = await self._validate_and_standardize_output(
                tool_name, result, execution_record
            )
            
            # Phase 5: Post-execution Reliability Checks
            await self._post_execution_checks(tool_name, validated_result, execution_record)
            
            # Record success
            execution_record.success = True
            execution_record.output = validated_result
            execution_record.execution_time = time.time() - start_time
            self._record_success(tool_name)
            
            logger.info(f"✅ {tool_name} executed reliably in {execution_record.execution_time:.2f}s")
            return self._format_success_result(validated_result, execution_record)
            
        except Exception as e:
            # Record failure and attempt recovery
            execution_record.error = str(e)
            execution_record.execution_time = time.time() - start_time
            self._record_failure(tool_name, str(e))
            
            logger.error(f"❌ {tool_name} failed: {e}")
            
            if fallback_enabled:
                return await self._execute_fallback(tool_name, context, execution_record)
            else:
                return self._format_error_result(str(e), execution_record)
        
        finally:
            self.execution_history.append(execution_record)
            await self._cleanup_execution(execution_record)
    
    async def _resolve_and_validate_arguments(
        self, 
        tool_name: str, 
        context: Dict[str, Any], 
        user_input: str,
        execution_record: ToolExecution
    ) -> Dict[str, Any]:
        """Resolve and validate all tool arguments."""
        try:
            # Use enhanced ArgResolver
            arguments = self.arg_resolver.resolve(
                tool_name,
                planner_args={},
                context=context,
                user_input=user_input,
                verbose=False
            )
            
            # Add user_id if not present
            arguments.setdefault("user_id", context.get("user_id", "default_user"))
            
            # Validate argument types and constraints
            validated_args = await self._validate_argument_types(tool_name, arguments)
            
            execution_record.arguments = validated_args
            return validated_args
            
        except MissingRequiredArgError as e:
            execution_record.reliability_issues.append(f"Missing required arguments: {e}")
            raise RuntimeError(f"Argument resolution failed: {e}")
        except Exception as e:
            execution_record.reliability_issues.append(f"Argument validation failed: {e}")
            raise RuntimeError(f"Argument validation failed: {e}")
    
    async def _validate_argument_types(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Validate argument types and apply constraints."""
        validated = arguments.copy()
        
        # Common argument validations
        if "essay_text" in validated:
            text = validated["essay_text"]
            if not isinstance(text, str) or not text.strip():
                raise ValueError("essay_text must be non-empty string")
            if len(text) > 10000:  # Reasonable limit
                validated["essay_text"] = text[:10000] + "..."
                logger.warning(f"Truncated essay_text for {tool_name}")
        
        if "word_count" in validated:
            word_count = validated["word_count"]
            if not isinstance(word_count, int) or word_count <= 0:
                validated["word_count"] = 650  # Default
                logger.warning(f"Invalid word_count for {tool_name}, using default")
        
        if "essay_prompt" in validated:
            prompt = validated["essay_prompt"]
            if not isinstance(prompt, str) or not prompt.strip():
                raise ValueError("essay_prompt must be non-empty string")
        
        return validated
    
    async def _pre_execution_checks(
        self, 
        tool_name: str, 
        arguments: Dict[str, Any],
        execution_record: ToolExecution
    ) -> bool:
        """Perform pre-execution reliability checks."""
        checks_passed = True
        
        # Check if tool exists in registry
        if tool_name not in TOOL_REGISTRY:
            execution_record.reliability_issues.append(f"Tool {tool_name} not in registry")
            checks_passed = False
        
        # Check failure rate threshold
        if self._get_failure_rate(tool_name) > (1 - self.min_success_rate):
            execution_record.reliability_issues.append(f"Tool {tool_name} has high failure rate")
            if self.reliability_level in [ReliabilityLevel.STRICT, ReliabilityLevel.PARANOID]:
                checks_passed = False
        
        # Check argument completeness
        try:
            from essay_agent.tools import get_required_args
            required_args = get_required_args(tool_name)
            missing = [arg for arg in required_args if arg not in arguments]
            if missing:
                execution_record.reliability_issues.append(f"Missing required args: {missing}")
                checks_passed = False
        except ImportError:
            pass  # Tool introspection not available
        
        return checks_passed
    
    async def _execute_tool_core(
        self, 
        tool_name: str, 
        arguments: Dict[str, Any],
        execution_record: ToolExecution
    ) -> Any:
        """Execute the actual tool with timeout and error handling."""
        tool = TOOL_REGISTRY[tool_name]
        
        # Set reasonable timeout
        timeout = getattr(tool, 'timeout', 45.0)
        
        try:
            if hasattr(tool, 'ainvoke'):
                result = await asyncio.wait_for(
                    tool.ainvoke(**arguments), 
                    timeout=timeout
                )
            else:
                # Run sync tool in executor
                loop = asyncio.get_running_loop()
                result = await asyncio.wait_for(
                    loop.run_in_executor(None, lambda: tool(**arguments)),
                    timeout=timeout
                )
            
            return result
            
        except asyncio.TimeoutError:
            raise RuntimeError(f"Tool {tool_name} timed out after {timeout}s")
        except Exception as e:
            raise RuntimeError(f"Tool execution failed: {e}")
    
    async def _validate_and_standardize_output(
        self, 
        tool_name: str, 
        result: Any,
        execution_record: ToolExecution
    ) -> Dict[str, Any]:
        """Validate output format and standardize structure."""
        # Handle ValidatedTool wrapper format
        if isinstance(result, dict) and "ok" in result:
            actual_result = result["ok"]
            error = result.get("error")
            if error:
                raise RuntimeError(f"Tool returned error: {error}")
        else:
            actual_result = result
        
        # Validate against expected schema
        if tool_name in self.expected_schemas:
            schema = self.expected_schemas[tool_name]
            if schema and not self._validate_against_schema(actual_result, schema):
                execution_record.reliability_issues.append("Output format mismatch")
                if self.reliability_level == ReliabilityLevel.STRICT:
                    raise RuntimeError(f"Output format validation failed for {tool_name}")
        
        # Standardize output format
        standardized = {
            "tool_name": tool_name,
            "success": True,
            "result": actual_result,
            "error": None,
            "metadata": {
                "execution_time": execution_record.execution_time,
                "reliability_level": self.reliability_level.value,
                "validation_passed": True
            }
        }
        
        execution_record.validation_passed = True
        return standardized
    
    def _validate_against_schema(self, result: Any, schema: Dict[str, str]) -> bool:
        """Validate result against expected schema."""
        if schema.get("type") == "list":
            return isinstance(result, list) and len(result) >= schema.get("min_length", 0)
        
        if isinstance(result, dict) and isinstance(schema, dict):
            # Check if result has expected keys with correct types
            for key, expected_type in schema.items():
                if key == "type":
                    continue
                if key not in result:
                    return False
                # Basic type checking
                if expected_type == "str" and not isinstance(result[key], str):
                    return False
                elif expected_type == "int" and not isinstance(result[key], int):
                    return False
                elif expected_type == "float" and not isinstance(result[key], (int, float)):
                    return False
        
        return True
    
    async def _post_execution_checks(
        self, 
        tool_name: str, 
        result: Dict[str, Any],
        execution_record: ToolExecution
    ) -> None:
        """Perform post-execution reliability checks."""
        # Check result completeness
        if not result.get("result"):
            execution_record.reliability_issues.append("Empty or null result")
        
        # Check for common issues
        result_data = result.get("result", {})
        if isinstance(result_data, dict):
            # Check for error indicators
            if "error" in result_data and result_data["error"]:
                execution_record.reliability_issues.append(f"Result contains error: {result_data['error']}")
            
            # Check for placeholder/stub content
            if isinstance(result_data, dict) and "stub" in str(result_data).lower():
                execution_record.reliability_issues.append("Result appears to be stub/placeholder")
    
    async def _execute_fallback(
        self, 
        tool_name: str, 
        context: Dict[str, Any],
        execution_record: ToolExecution
    ) -> Dict[str, Any]:
        """Execute fallback strategy when primary execution fails."""
        logger.warning(f"🔄 Executing fallback for {tool_name}")
        
        # Try alternative tools for common functions
        fallback_tools = self._get_fallback_tools(tool_name)
        
        for fallback_tool in fallback_tools:
            if fallback_tool in TOOL_REGISTRY:
                try:
                    return await self.execute_tool_safely(
                        fallback_tool, context, fallback_enabled=False
                    )
                except Exception:
                    continue
        
        # Generate generic fallback response
        fallback_result = self._generate_generic_fallback(tool_name, context)
        
        return {
            "tool_name": tool_name,
            "success": False,
            "result": fallback_result,
            "error": f"Primary execution failed, using fallback",
            "metadata": {
                "execution_time": execution_record.execution_time,
                "reliability_level": self.reliability_level.value,
                "validation_passed": False,
                "fallback_used": True
            }
        }
    
    def _get_fallback_tools(self, tool_name: str) -> List[str]:
        """Get list of fallback tools for a given tool."""
        fallback_map = {
            "brainstorm": ["suggest_stories", "story_development"],
            "suggest_stories": ["brainstorm", "brainstorm_specific"],
            "outline": ["outline_generator", "structure_validator"],
            "draft": ["expand_outline_section", "rewrite_paragraph"],
            "revise": ["improve_selection", "enhance_vocabulary"],
            "polish": ["fix_grammar", "optimize_word_count"],
            "essay_scoring": ["weakness_highlight", "alignment_check"]
        }
        return fallback_map.get(tool_name, [])
    
    def _generate_generic_fallback(self, tool_name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate generic fallback response based on tool type."""
        if "brainstorm" in tool_name:
            return {
                "stories": [
                    {
                        "title": "Personal Challenge",
                        "description": "A meaningful challenge that led to growth",
                        "prompt_fit": "Shows resilience and learning"
                    }
                ]
            }
        elif "outline" in tool_name:
            return {
                "outline": {
                    "hook": "A moment that changed everything",
                    "context": "Setting and background",
                    "conflict": "The central challenge",
                    "growth": "How you responded and grew",
                    "reflection": "What you learned"
                }
            }
        elif "draft" in tool_name:
            return {
                "draft": "This is a placeholder draft. The writing tool encountered an issue, but your essay development can continue with manual input or alternative tools."
            }
        else:
            return {
                "message": f"The {tool_name} tool is temporarily unavailable. Please try again or use an alternative approach."
            }
    
    def _format_success_result(self, result: Dict[str, Any], execution_record: ToolExecution) -> Dict[str, Any]:
        """Format successful tool execution result."""
        return result
    
    def _format_error_result(self, error: str, execution_record: ToolExecution) -> Dict[str, Any]:
        """Format error result with debugging information."""
        return {
            "tool_name": execution_record.tool_name,
            "success": False,
            "result": None,
            "error": error,
            "metadata": {
                "execution_time": execution_record.execution_time,
                "reliability_level": self.reliability_level.value,
                "validation_passed": False,
                "reliability_issues": execution_record.reliability_issues
            }
        }
    
    def _record_success(self, tool_name: str) -> None:
        """Record successful tool execution."""
        self.success_counts[tool_name] = self.success_counts.get(tool_name, 0) + 1
    
    def _record_failure(self, tool_name: str, error: str) -> None:
        """Record failed tool execution."""
        self.failure_counts[tool_name] = self.failure_counts.get(tool_name, 0) + 1
        logger.error(f"Tool failure recorded: {tool_name} - {error}")
    
    def _get_failure_rate(self, tool_name: str) -> float:
        """Get failure rate for a specific tool."""
        failures = self.failure_counts.get(tool_name, 0)
        successes = self.success_counts.get(tool_name, 0)
        total = failures + successes
        return failures / total if total > 0 else 0.0
    
    async def _cleanup_execution(self, execution_record: ToolExecution) -> None:
        """Cleanup after tool execution."""
        # Trim execution history if it gets too large
        if len(self.execution_history) > 1000:
            self.execution_history = self.execution_history[-500:]
    
    def get_reliability_report(self) -> Dict[str, Any]:
        """Generate comprehensive reliability report."""
        total_executions = len(self.execution_history)
        successful_executions = sum(1 for e in self.execution_history if e.success)
        
        tool_stats = {}
        for tool_name in TOOL_REGISTRY.keys():
            tool_executions = [e for e in self.execution_history if e.tool_name == tool_name]
            if tool_executions:
                successes = sum(1 for e in tool_executions if e.success)
                tool_stats[tool_name] = {
                    "executions": len(tool_executions),
                    "successes": successes,
                    "success_rate": successes / len(tool_executions),
                    "avg_execution_time": sum(e.execution_time for e in tool_executions) / len(tool_executions),
                    "reliability_issues": sum(len(e.reliability_issues) for e in tool_executions)
                }
        
        return {
            "overall_stats": {
                "total_executions": total_executions,
                "successful_executions": successful_executions,
                "overall_success_rate": successful_executions / total_executions if total_executions > 0 else 0,
                "reliability_level": self.reliability_level.value
            },
            "tool_stats": tool_stats,
            "problematic_tools": [
                name for name, stats in tool_stats.items() 
                if stats["success_rate"] < self.min_success_rate
            ]
        }

# Global reliability manager instance
_reliability_manager = None

def get_reliability_manager(level: ReliabilityLevel = ReliabilityLevel.STANDARD) -> ToolReliabilityManager:
    """Get global reliability manager instance."""
    global _reliability_manager
    if _reliability_manager is None:
        _reliability_manager = ToolReliabilityManager(level)
    return _reliability_manager

async def execute_tool_reliably(
    tool_name: str,
    context: Dict[str, Any],
    user_input: str = "",
    reliability_level: ReliabilityLevel = ReliabilityLevel.STANDARD
) -> Dict[str, Any]:
    """
    Execute a tool with comprehensive reliability measures.
    
    This is the main entry point for reliable tool execution.
    """
    manager = get_reliability_manager(reliability_level)
    return await manager.execute_tool_safely(tool_name, context, user_input) 