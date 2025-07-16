"""Tool analyzer for context-based tool recommendations.

This module provides intelligent analysis of user intent and context
to recommend the most relevant tools for the current situation.
"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Set, Tuple, Optional
from dataclasses import asdict

from pydantic import BaseModel, Field

from essay_agent.llm_client import get_chat_llm
from essay_agent.agent.tools.tool_registry import EnhancedToolRegistry
from essay_agent.agent.tools.tool_descriptions import ToolDescription, format_tools_for_llm


class UserIntent(BaseModel):
    """Structured representation of user intent."""
    primary_intent: str = Field(description="Main intent category")
    secondary_intents: List[str] = Field(default_factory=list, description="Additional intent categories")
    confidence: float = Field(description="Confidence in intent classification (0-1)")
    essay_phase: str = Field(description="Current essay writing phase")
    specific_request: str = Field(description="Specific user request details")
    urgency: str = Field(description="Low, Medium, or High")


class ToolRecommendation(BaseModel):
    """Tool recommendation with reasoning."""
    tool_name: str
    confidence_score: float = Field(ge=0.0, le=1.0)
    reasoning: str
    estimated_tokens: int
    priority: str = Field(description="High, Medium, or Low")


class ContextAnalysis(BaseModel):
    """Analysis of current context and state."""
    available_data: List[str] = Field(description="Available data elements")
    completed_tools: List[str] = Field(description="Tools already executed")
    missing_dependencies: List[str] = Field(description="Missing required dependencies")
    workflow_progress: str = Field(description="Progress through essay workflow")


class ToolAnalyzer:
    """Analyzes context to recommend relevant tools using LLM reasoning."""
    
    def __init__(self, registry: Optional[EnhancedToolRegistry] = None):
        """Initialize tool analyzer.
        
        Args:
            registry: Enhanced tool registry (uses global instance if None)
        """
        if registry is None:
            from essay_agent.agent.tools.tool_registry import ENHANCED_REGISTRY
            registry = ENHANCED_REGISTRY
        
        self.registry = registry
        self.llm = get_chat_llm()
        
        # Common intent patterns
        self.intent_patterns = {
            "brainstorming": ["ideas", "brainstorm", "stories", "think", "topics", "help me come up with"],
            "structuring": ["outline", "organize", "structure", "plan", "layout"],
            "drafting": ["write", "draft", "compose", "create essay", "generate"],
            "revising": ["improve", "revise", "fix", "better", "change", "edit"],
            "polishing": ["polish", "final", "grammar", "style", "perfect", "ready"],
            "evaluation": ["score", "rate", "assess", "feedback", "quality", "good"],
            "analysis": ["analyze", "check", "validate", "review", "examine"]
        }
    
    def analyze_user_intent(self, 
                           message: str, 
                           conversation_history: List[str] = None) -> UserIntent:
        """Determine user intent from message using LLM analysis.
        
        Args:
            message: User's message
            conversation_history: Previous conversation context
            
        Returns:
            Structured user intent analysis
        """
        # First try pattern matching for speed
        quick_intent = self._quick_intent_analysis(message)
        
        # Use LLM for complex cases or confirmation
        if quick_intent["confidence"] < 0.8 or conversation_history:
            return self._llm_intent_analysis(message, conversation_history, quick_intent)
        
        return UserIntent(**quick_intent)
    
    def _quick_intent_analysis(self, message: str) -> Dict[str, Any]:
        """Quick pattern-based intent analysis."""
        message_lower = message.lower()
        intent_scores = {}
        
        # Score each intent based on keyword presence
        for intent, keywords in self.intent_patterns.items():
            score = sum(1 for keyword in keywords if keyword in message_lower)
            if score > 0:
                intent_scores[intent] = score / len(keywords)
        
        if not intent_scores:
            return {
                "primary_intent": "unknown",
                "secondary_intents": [],
                "confidence": 0.3,
                "essay_phase": "unknown",
                "specific_request": message,
                "urgency": "Medium"
            }
        
        # Get top intent
        primary_intent = max(intent_scores, key=intent_scores.get)
        confidence = intent_scores[primary_intent]
        
        # Get secondary intents
        secondary_intents = [
            intent for intent, score in intent_scores.items() 
            if intent != primary_intent and score > 0.2
        ]
        
        # Map intent to essay phase
        phase_mapping = {
            "brainstorming": "brainstorming",
            "structuring": "structuring", 
            "drafting": "drafting",
            "revising": "revising",
            "polishing": "polishing",
            "evaluation": "revising",
            "analysis": "evaluation"
        }
        
        return {
            "primary_intent": primary_intent,
            "secondary_intents": secondary_intents,
            "confidence": min(confidence * 2, 1.0),  # Boost confidence for clear matches
            "essay_phase": phase_mapping.get(primary_intent, "unknown"),
            "specific_request": message,
            "urgency": "High" if any(word in message_lower for word in ["urgent", "deadline", "asap", "quickly"]) else "Medium"
        }
    
    def _llm_intent_analysis(self, 
                            message: str,
                            conversation_history: Optional[List[str]] = None,
                            quick_analysis: Optional[Dict[str, Any]] = None) -> UserIntent:
        """Use LLM for detailed intent analysis."""
        
        context_prompt = f"""
Analyze the user's intent from their message about essay writing assistance.

User message: "{message}"

"""
        
        if conversation_history:
            context_prompt += f"""
Recent conversation context:
{chr(10).join(conversation_history[-3:])}

"""
        
        if quick_analysis:
            context_prompt += f"""
Initial analysis suggests: {quick_analysis.get('primary_intent', 'unknown')}

"""
        
        analysis_prompt = context_prompt + """
Classify the user's intent and provide structured analysis:

Intent categories:
- brainstorming: Generating ideas, stories, topics
- structuring: Creating outlines, organizing content
- drafting: Writing initial content, expanding ideas
- revising: Improving content, fixing issues
- polishing: Final refinement, style, grammar
- evaluation: Scoring, feedback, assessment
- analysis: Checking, validating, reviewing

Essay phases:
- brainstorming: Initial idea generation
- structuring: Organizing ideas into outline
- drafting: Writing first draft
- revising: Improving content and structure
- polishing: Final language refinement

Provide analysis in this exact JSON format:
{
    "primary_intent": "category_name",
    "secondary_intents": ["category1", "category2"],
    "confidence": 0.85,
    "essay_phase": "phase_name", 
    "specific_request": "detailed request description",
    "urgency": "High/Medium/Low"
}
"""
        
        try:
            response = self.llm.invoke([{"role": "user", "content": analysis_prompt}])
            
            # Parse JSON response
            analysis_data = json.loads(response.content.strip())
            
            return UserIntent(**analysis_data)
            
        except (json.JSONDecodeError, Exception) as e:
            # Fallback to quick analysis if LLM fails
            return UserIntent(**(quick_analysis or {
                "primary_intent": "unknown",
                "secondary_intents": [],
                "confidence": 0.4,
                "essay_phase": "unknown", 
                "specific_request": message,
                "urgency": "Medium"
            }))
    
    def analyze_context(self, 
                       available_data: Dict[str, Any],
                       completed_tools: List[str] = None,
                       conversation_state: Dict[str, Any] = None) -> ContextAnalysis:
        """Analyze current context and available data.
        
        Args:
            available_data: Dictionary of available data (user_profile, essay_prompt, etc.)
            completed_tools: List of tools already executed
            conversation_state: Current conversation state
            
        Returns:
            Context analysis with recommendations
        """
        if completed_tools is None:
            completed_tools = []
            
        # Determine available data types
        data_types = []
        if available_data.get("user_profile"):
            data_types.append("user_profile")
        if available_data.get("essay_prompt"):
            data_types.append("essay_prompt") 
        if available_data.get("stories"):
            data_types.append("stories")
        if available_data.get("outline"):
            data_types.append("outline")
        if available_data.get("draft"):
            data_types.append("draft")
        if available_data.get("revisions"):
            data_types.append("revisions")
            
        # Check for missing dependencies
        completed_set = set(completed_tools)
        missing_deps = []
        
        # Core workflow dependencies
        workflow_deps = {
            "outline": ["brainstorm"],
            "draft": ["outline"],
            "revise": ["draft"],
            "polish": ["revise"]
        }
        
        for tool, deps in workflow_deps.items():
            if tool not in completed_set:
                missing = [dep for dep in deps if dep not in completed_set]
                if missing:
                    missing_deps.extend(missing)
        
        # Determine workflow progress
        workflow_tools = ["brainstorm", "outline", "draft", "revise", "polish"]
        completed_workflow = [tool for tool in workflow_tools if tool in completed_set]
        
        if not completed_workflow:
            progress = "0% - Not started"
        elif len(completed_workflow) == len(workflow_tools):
            progress = "100% - Complete"
        else:
            percentage = (len(completed_workflow) / len(workflow_tools)) * 100
            last_completed = completed_workflow[-1]
            progress = f"{percentage:.0f}% - Last: {last_completed}"
        
        return ContextAnalysis(
            available_data=data_types,
            completed_tools=completed_tools,
            missing_dependencies=list(set(missing_deps)),
            workflow_progress=progress
        )
    
    def recommend_tools(self, 
                       intent: UserIntent,
                       context: ContextAnalysis,
                       max_recommendations: int = 5) -> List[ToolRecommendation]:
        """Recommend tools based on intent and context.
        
        Args:
            intent: User intent analysis
            context: Context analysis
            max_recommendations: Maximum number of tools to recommend
            
        Returns:
            List of tool recommendations with reasoning
        """
        recommendations = []
        
        # Get tools for current phase
        phase_tools = self.registry.get_tools_for_phase(intent.essay_phase)
        
        # Get tools by intent category
        if intent.primary_intent in ["brainstorming"]:
            intent_tools = self.registry.get_tools_by_category("brainstorming")
            intent_tools.extend(self.registry.get_tools_by_category("core_workflow"))
        elif intent.primary_intent in ["structuring"]:
            intent_tools = self.registry.get_tools_by_category("structure")
        elif intent.primary_intent in ["drafting"]:
            intent_tools = self.registry.get_tools_by_category("writing")
        elif intent.primary_intent in ["revising"]:
            intent_tools = self.registry.get_tools_by_category("evaluation")
            intent_tools.extend(self.registry.get_tools_by_category("writing"))
        elif intent.primary_intent in ["polishing"]:
            intent_tools = self.registry.get_tools_by_category("polish")
        else:
            intent_tools = []
        
        # Combine and deduplicate
        candidate_tools = {tool.name: tool for tool in phase_tools + intent_tools}
        
        # Filter by available data requirements
        available_data_set = set(context.available_data)
        executable_tools = []
        
        for tool in candidate_tools.values():
            # Check if requirements are met
            requirements_met = all(
                req in available_data_set or req in ["essay_prompt", "user_profile"] 
                for req in tool.input_requirements
            )
            
            # Skip if already completed (unless it's repeatable)
            repeatable_tools = ["brainstorm", "suggest_stories", "word_count", "echo"]
            if tool.name in context.completed_tools and tool.name not in repeatable_tools:
                continue
                
            if requirements_met:
                executable_tools.append(tool)
        
        # Score and rank tools
        for tool in executable_tools:
            confidence_score = self._calculate_tool_confidence(tool, intent, context)
            priority = self._determine_priority(tool, intent, context)
            reasoning = self._generate_reasoning(tool, intent, context)
            
            recommendations.append(ToolRecommendation(
                tool_name=tool.name,
                confidence_score=confidence_score,
                reasoning=reasoning,
                estimated_tokens=tool.estimated_tokens,
                priority=priority
            ))
        
        # Sort by confidence and priority
        recommendations.sort(
            key=lambda x: (x.priority == "High", x.confidence_score),
            reverse=True
        )
        
        return recommendations[:max_recommendations]
    
    def _calculate_tool_confidence(self, 
                                  tool: ToolDescription, 
                                  intent: UserIntent,
                                  context: ContextAnalysis) -> float:
        """Calculate confidence score for tool recommendation."""
        base_confidence = tool.confidence_threshold
        
        # Boost for exact intent match
        if intent.primary_intent in tool.when_to_use.lower():
            base_confidence += 0.2
            
        # Boost for phase alignment
        phase_boost = {
            "brainstorming": {"brainstorming": 0.3, "core_workflow": 0.2},
            "structuring": {"structure": 0.3, "core_workflow": 0.2},
            "drafting": {"writing": 0.3, "core_workflow": 0.2},
            "revising": {"evaluation": 0.3, "writing": 0.2},
            "polishing": {"polish": 0.3, "validation": 0.2}
        }
        
        boost = phase_boost.get(intent.essay_phase, {}).get(tool.category, 0)
        base_confidence += boost
        
        # Reduce for missing dependencies
        if any(dep not in context.completed_tools for dep in tool.dependencies):
            base_confidence -= 0.2
        
        # Boost for workflow tools in sequence
        workflow_order = ["brainstorm", "outline", "draft", "revise", "polish"]
        if tool.name in workflow_order:
            expected_next = None
            for i, wf_tool in enumerate(workflow_order):
                if wf_tool not in context.completed_tools:
                    expected_next = wf_tool
                    break
            
            if tool.name == expected_next:
                base_confidence += 0.3
        
        return min(base_confidence, 1.0)
    
    def _determine_priority(self, 
                           tool: ToolDescription,
                           intent: UserIntent, 
                           context: ContextAnalysis) -> str:
        """Determine priority level for tool."""
        # High priority for urgent requests
        if intent.urgency == "High":
            return "High"
            
        # High priority for next workflow step
        workflow_order = ["brainstorm", "outline", "draft", "revise", "polish"]
        for tool_name in workflow_order:
            if tool_name not in context.completed_tools:
                if tool.name == tool_name:
                    return "High"
                break
        
        # Medium priority for phase-aligned tools
        if tool.category == intent.essay_phase:
            return "Medium"
            
        return "Low"
    
    def _generate_reasoning(self, 
                           tool: ToolDescription,
                           intent: UserIntent,
                           context: ContextAnalysis) -> str:
        """Generate reasoning for tool recommendation."""
        reasons = []
        
        # Intent alignment
        if intent.primary_intent in tool.when_to_use.lower():
            reasons.append(f"Directly addresses your '{intent.primary_intent}' request")
        
        # Phase alignment
        if tool.category == intent.essay_phase:
            reasons.append(f"Appropriate for {intent.essay_phase} phase")
            
        # Workflow progression
        workflow_order = ["brainstorm", "outline", "draft", "revise", "polish"]
        if tool.name in workflow_order:
            for i, wf_tool in enumerate(workflow_order):
                if wf_tool not in context.completed_tools:
                    if tool.name == wf_tool:
                        reasons.append("Next step in essay workflow")
                    break
        
        # Dependencies satisfied
        if all(dep in context.completed_tools for dep in tool.dependencies):
            reasons.append("All prerequisites completed")
        elif tool.dependencies:
            missing = [dep for dep in tool.dependencies if dep not in context.completed_tools]
            reasons.append(f"Requires: {', '.join(missing)}")
        
        return "; ".join(reasons) if reasons else "General utility for essay writing"
    
    def explain_recommendation(self, 
                              tool_name: str,
                              intent: UserIntent,
                              context: ContextAnalysis) -> str:
        """Generate detailed explanation for a specific tool recommendation.
        
        Args:
            tool_name: Name of the tool to explain
            intent: User intent analysis
            context: Context analysis
            
        Returns:
            Detailed explanation string
        """
        tool_desc = self.registry.get_description(tool_name)
        if not tool_desc:
            return f"Tool '{tool_name}' not found."
        
        explanation = f"""
**{tool_desc.name}** - {tool_desc.description}

**Why this tool is recommended:**
- **Purpose**: {tool_desc.purpose}
- **Best used when**: {tool_desc.when_to_use}
- **Your request**: "{intent.specific_request}"
- **Current phase**: {intent.essay_phase}

**What you'll need:**
- Required inputs: {', '.join(tool_desc.input_requirements)}
- Available data: {', '.join(context.available_data)}

**What you'll get:**
- Output: {tool_desc.output_format}
- Estimated effort: ~{tool_desc.estimated_tokens} tokens

**Example usage:** {tool_desc.example_usage}
"""
        
        if tool_desc.dependencies:
            explanation += f"\n**Prerequisites:** {', '.join(tool_desc.dependencies)}"
        
        return explanation.strip()


def create_tool_analyzer(registry: Optional[EnhancedToolRegistry] = None) -> ToolAnalyzer:
    """Factory function to create a ToolAnalyzer instance."""
    return ToolAnalyzer(registry) 