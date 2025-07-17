"""Dynamic prompt construction with context awareness.

This module provides sophisticated prompt building capabilities that integrate
with the agent's memory system and tool registry to create optimized,
context-aware prompts for the ReAct agent.
"""
from typing import Dict, List, Any, Optional, Union, Tuple
import logging
import asyncio
from datetime import datetime

from .prompts import (
    ADVANCED_REASONING_PROMPT,
    ENHANCED_CONVERSATION_PROMPT,
    TOOL_SPECIFIC_PROMPTS,
    ERROR_RECOVERY_STRATEGIES,
    PERFORMANCE_OPTIMIZED_PROMPTS,
    format_context_for_reasoning,
    format_tool_descriptions,
    inject_memory_context,
    select_reasoning_template,
    get_performance_context
)

# Import memory components (these will be available after TASK-003)
try:
    from ..memory.agent_memory import AgentMemory
    from ..memory.context_retrieval import ContextRetriever
    from ..tools.tool_descriptions import TOOL_DESCRIPTIONS
except ImportError:
    # Graceful degradation for testing or incomplete setup
    AgentMemory = None
    ContextRetriever = None
    TOOL_DESCRIPTIONS = {}

logger = logging.getLogger(__name__)


class PromptBuilder:
    """Dynamic prompt construction with context awareness.
    
    This class builds optimized prompts by analyzing user context, memory patterns,
    tool availability, and performance metrics to create the most effective
    reasoning prompts for the ReAct agent.
    """
    
    def __init__(self, memory: Optional[Any] = None, tool_registry: Optional[Dict] = None):
        """Initialize the prompt builder.
        
        Args:
            memory: AgentMemory instance for context retrieval
            tool_registry: Tool registry dictionary with available tools
        """
        self.memory = memory
        self.tool_registry = tool_registry or TOOL_DESCRIPTIONS
        self.context_injector = ContextInjector()
        self._token_limits = {
            'gpt-4': 8192,
            'gpt-3.5-turbo': 4096,
            'default': 4096
        }
        
        logger.info("PromptBuilder initialized with %d tools", len(self.tool_registry))
    
    async def build_reasoning_prompt(
        self, 
        user_input: str, 
        context: Dict[str, Any],
        model: str = 'default',
        prompt_type: str = 'default'
    ) -> Dict[str, Any]:
        """Build a dynamic reasoning prompt optimized for the current context.
        
        Args:
            user_input: The user's input message
            context: Context dictionary from memory system
            model: LLM model name for token optimization
            prompt_type: Type of prompt to build (default, action_reasoning, etc.)
            
        Returns:
            Optimized reasoning prompt string
        """
        try:
            # 1. Select optimal template based on context
            task_type = self._determine_task_type(user_input, context)
            base_template = select_reasoning_template(task_type, context)
            
            # 2. Safely inject context with defaults
            safe_context = self._inject_context_safely(context)
            
            # 3. Gather context components with error handling
            conversation_context = await self._get_conversation_context(safe_context)
            memory_context = await self._get_memory_context(safe_context)
            user_state = self._format_user_state(safe_context)
            tool_descriptions = format_tool_descriptions(self.tool_registry)
            performance_context = await self._get_performance_context(safe_context)
            
            # 4. Create formatting dictionary with all required keys
            format_dict = {
                'conversation_context': conversation_context,
                'memory_context': memory_context,
                'user_state': user_state,
                'tool_descriptions': tool_descriptions,
                'performance_context': performance_context,
                'user_input': user_input,
                'user_profile': safe_context.get('user_profile', 'No profile available'),
                'current_task': safe_context.get('current_task', 'essay_assistance'),
                'essay_phase': safe_context.get('essay_phase', 'unknown'),
                'context': safe_context
            }
            
            # 5. Inject context into template with safe formatting
            prompt = self._safe_format_template(base_template, format_dict)
            
            # 4. Optimize for token limits
            optimized_prompt = self.optimize_for_tokens(prompt, model)
            
            logger.debug("Built reasoning prompt: %d characters, task_type=%s", 
                        len(optimized_prompt), task_type)
            
            return {
                "prompt": optimized_prompt,
                "version": prompt_type,
                "task_type": task_type
            }
            
        except Exception as e:
            logger.error("Error building reasoning prompt: %s", e)
            # Fallback to basic template
            fallback_prompt = ADVANCED_REASONING_PROMPT.format(
                conversation_context="Context unavailable",
                memory_context="Memory unavailable", 
                user_state="State unavailable",
                tool_descriptions=format_tool_descriptions(self.tool_registry),
                performance_context="Performance data unavailable",
                user_input=user_input
            )
            return {
                "prompt": fallback_prompt,
                "version": "fallback",
                "task_type": "unknown"
            }
    
    async def build_tool_prompt(
        self, 
        tool_name: str, 
        context: Dict[str, Any],
        base_args: Optional[Dict] = None
    ) -> str:
        """Build a tool-specific prompt with context enhancement.
        
        Args:
            tool_name: Name of the tool to execute
            context: Context dictionary for tool execution
            base_args: Base arguments for the tool
            
        Returns:
            Enhanced tool prompt string
        """
        try:
            # Get tool-specific context enhancement
            tool_context = TOOL_SPECIFIC_PROMPTS.get(tool_name, "")
            
            # Build enhanced prompt with context
            memory_context = await self._get_memory_context(context)
            user_profile = context.get('user_profile', {})
            
            enhanced_prompt = f"""
{tool_context}

MEMORY CONTEXT:
{memory_context}

USER PROFILE:
{self._format_user_profile(user_profile)}

TOOL ARGS:
{base_args or {}}

Execute the {tool_name} tool with enhanced context awareness.
"""
            
            logger.debug("Built tool prompt for %s: %d characters", tool_name, len(enhanced_prompt))
            return enhanced_prompt.strip()
            
        except Exception as e:
            logger.error("Error building tool prompt for %s: %s", tool_name, e)
            return f"Execute {tool_name} tool with args: {base_args or {}}"
    
    async def build_error_recovery_prompt(self, error_context: Dict[str, Any]) -> str:
        """Build an error recovery prompt with sophisticated context analysis.
        
        Args:
            error_context: Dictionary containing error information and context
            
        Returns:
            Error recovery prompt string
        """
        try:
            error_type = self._classify_error(error_context.get('error', ''))
            recovery_strategy = ERROR_RECOVERY_STRATEGIES.get(error_type, ERROR_RECOVERY_STRATEGIES['tool_failure'])
            
            # Enhance with context
            context = error_context.get('context', {})
            memory_context = await self._get_memory_context(context)
            
            prompt = recovery_strategy.format(
                tool_name=error_context.get('tool_name', 'unknown'),
                error_message=error_context.get('error', 'Unknown error'),
                context=format_context_for_reasoning(context),
                memory_context=memory_context
            )
            
            logger.debug("Built error recovery prompt: %d characters, error_type=%s", 
                        len(prompt), error_type)
            
            return prompt
            
        except Exception as e:
            logger.error("Error building recovery prompt: %s", e)
            return ERROR_RECOVERY_STRATEGIES['tool_failure'].format(
                tool_name=error_context.get('tool_name', 'unknown'),
                error_message=str(e),
                context="Context unavailable",
                memory_context="Memory unavailable"
            )
    
    def inject_context(self, template: str, context: Dict[str, Any]) -> str:
        """Inject context data into a prompt template.
        
        Args:
            template: Prompt template with placeholders
            context: Context data to inject
            
        Returns:
            Template with context injected
        """
        return self.context_injector.inject_all_context(template, context)
    
    def optimize_for_tokens(self, prompt: str, model: str = 'default') -> str:
        """Optimize prompt length for the specified model's token limits.
        
        Args:
            prompt: The prompt to optimize
            model: Model name for token limit lookup
            
        Returns:
            Optimized prompt string
        """
        try:
            # Estimate tokens (rough approximation: 1 token ≈ 4 characters)
            estimated_tokens = len(prompt) // 4
            token_limit = self._token_limits.get(model, self._token_limits['default'])
            
            # Reserve 25% for response
            max_prompt_tokens = int(token_limit * 0.75)
            
            if estimated_tokens <= max_prompt_tokens:
                return prompt
            
            # Intelligent truncation - preserve structure
            return self._truncate_intelligently(prompt, max_prompt_tokens * 4)
            
        except Exception as e:
            logger.error("Error optimizing prompt for tokens: %s", e)
            return prompt
    
    def _determine_task_type(self, user_input: str, context: Dict[str, Any]) -> str:
        """Determine the type of task based on user input and context.
        
        ENHANCED VERSION: Promotes tool diversity by analyzing conversation flow
        and preventing over-reliance on any single tool.
        
        Args:
            user_input: User's input message
            context: Context dictionary
            
        Returns:
            Task type string that encourages appropriate tool progression
        """
        lower_input = user_input.lower()
        
        # Check conversation history for tool diversity analysis
        recent_tools = self._get_recent_tools_used(context)
        brainstorm_count = recent_tools.count('brainstorm')
        
        # CRITICAL FIX: Prevent brainstorm over-usage by promoting progression
        if brainstorm_count >= 2:
            # Force progression to next logical step
            if any(word in lower_input for word in ['outline', 'structure', 'organize']):
                return 'outlining'
            elif any(word in lower_input for word in ['write', 'draft', 'create']):
                return 'drafting'
            elif 'story' in lower_input or 'experience' in lower_input:
                return 'story_development'  # Use story development instead of more brainstorming
            else:
                return 'tool_selection'  # Force intelligent tool selection
        
        # Original classification logic with enhancements
        if any(word in lower_input for word in ['help', 'stuck', 'confused', 'don\'t know']):
            return 'support_needed'
        elif any(word in lower_input for word in ['outline', 'structure', 'organize']):
            return 'outlining'
        elif any(word in lower_input for word in ['write', 'draft', 'paragraph', 'essay']):
            return 'drafting'
        elif any(word in lower_input for word in ['revise', 'improve', 'fix', 'better']):
            return 'revision'
        elif any(word in lower_input for word in ['polish', 'final', 'ready', 'submit']):
            return 'polishing'
        elif any(word in lower_input for word in ['story', 'experience', 'moment', 'develop']):
            return 'story_development'
        elif any(word in lower_input for word in ['brainstorm', 'ideas', 'topics']) and brainstorm_count == 0:
            return 'brainstorming'  # Only allow if no recent brainstorming
        elif '?' in user_input:
            return 'conversation'
        else:
            return 'tool_selection'
    
    def _get_recent_tools_used(self, context: Dict[str, Any]) -> List[str]:
        """Extract recently used tools from context for diversity analysis."""
        tools = []
        
        # Check conversation history for tool usage
        conversation_history = context.get('conversation_history', [])
        if isinstance(conversation_history, list):
            for turn in conversation_history[-5:]:  # Last 5 turns
                if isinstance(turn, dict) and turn.get('type') == 'ai':
                    tool_calls = turn.get('tool_calls', [])
                    for tool_call in tool_calls:
                        if isinstance(tool_call, dict) and 'function' in tool_call:
                            tools.append(tool_call['function'].get('name', ''))
        
        # Also check memory for recent tool executions
        if self.memory and hasattr(self.memory, 'recent_tool_executions'):
            try:
                recent_executions = self.memory.recent_tool_executions[-5:]  # Last 5
                for execution in recent_executions:
                    if hasattr(execution, 'tool_name'):
                        tools.append(execution.tool_name)
                    elif isinstance(execution, dict):
                        tools.append(execution.get('tool_name', ''))
            except Exception:
                pass
        
        return tools
    
    def _inject_context_safely(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Safely inject context with comprehensive defaults and validation.
        
        Args:
            context: Raw context dictionary from memory system
            
        Returns:
            Safely processed context with all required fields and defaults
        """
        safe_context = context.copy() if context else {}
        
        # CRITICAL FIX: Ensure all template variables have safe defaults
        required_defaults = {
            # Core context fields
            'user_profile': {},
            'conversation_history': [],
            'tool_outputs': {},
            'user_state': {},
            'performance_context': {},
            'memory_context': {},
            'conversation_context': {},
            
            # User profile fields
            'user_id': 'unknown_user',
            'user_name': 'Student',
            'academic_interests': [],
            'core_values': [],
            'defining_moments': [],
            'essay_history': [],
            
            # Conversation fields
            'recent_messages': [],
            'current_phase': 'planning',
            'current_essay': {},
            'word_limit': 650,
            
            # Tool execution fields
            'recent_tools': [],
            'tool_usage_stats': {},
            'last_tool_result': None,
            
            # Memory fields
            'semantic_memories': [],
            'reasoning_chains': [],
            'pattern_insights': [],
            
            # Performance fields
            'execution_times': {},
            'success_rates': {},
            'optimization_suggestions': []
        }
        
        # Apply defaults for missing fields
        for key, default_value in required_defaults.items():
            if key not in safe_context:
                safe_context[key] = default_value
            elif safe_context[key] is None:
                safe_context[key] = default_value
        
        # NESTED SAFETY: Ensure nested dictionaries are safe
        if isinstance(safe_context.get('user_profile'), dict):
            profile_defaults = {
                'name': safe_context.get('user_name', 'Student'),
                'core_values': [],
                'defining_moments': [],
                'academic_interests': [],
                'writing_style': 'authentic',
                'experience_level': 'intermediate'
            }
            
            for key, default in profile_defaults.items():
                if key not in safe_context['user_profile']:
                    safe_context['user_profile'][key] = default
        
        # CONVERSATION HISTORY SAFETY: Ensure proper format
        if not isinstance(safe_context.get('conversation_history'), list):
            safe_context['conversation_history'] = []
        
        # Ensure conversation entries have required fields
        safe_history = []
        for entry in safe_context['conversation_history']:
            if isinstance(entry, dict):
                safe_entry = {
                    'user': entry.get('user', ''),
                    'agent': entry.get('agent', ''),
                    'timestamp': entry.get('timestamp', 'recent')
                }
                safe_history.append(safe_entry)
        safe_context['conversation_history'] = safe_history
        
        # TOOL OUTPUTS SAFETY: Ensure proper format
        if not isinstance(safe_context.get('tool_outputs'), dict):
            safe_context['tool_outputs'] = {}
        
        # PERFORMANCE CONTEXT SAFETY: Ensure metrics are numbers
        perf_context = safe_context.get('performance_context', {})
        if not isinstance(perf_context, dict):
            perf_context = {}
        
        perf_defaults = {
            'average_response_time': 2.5,
            'success_rate': 0.85,
            'total_interactions': 1,
            'recent_tool_success': True
        }
        
        for key, default in perf_defaults.items():
            if key not in perf_context:
                perf_context[key] = default
            elif not isinstance(perf_context[key], (int, float, bool)):
                perf_context[key] = default
        
        safe_context['performance_context'] = perf_context
        
        return safe_context
    
    async def _get_conversation_context(self, context: Dict[str, Any]) -> str:
        """Get formatted conversation context with error handling.
        
        Args:
            context: Safe context dictionary
            
        Returns:
            Formatted conversation context string
        """
        try:
            conversation_history = context.get('conversation_history', [])
            
            if not conversation_history:
                return "No previous conversation context available."
            
            # Format recent conversation turns
            formatted_turns = []
            for turn in conversation_history[-3:]:  # Last 3 turns
                if isinstance(turn, dict):
                    user_msg = str(turn.get('user', '')).strip()
                    agent_msg = str(turn.get('agent', '')).strip()
                    
                    if user_msg and agent_msg:
                        formatted_turns.append(f"User: {user_msg}")
                        formatted_turns.append(f"Agent: {agent_msg}")
            
            if formatted_turns:
                return "RECENT CONVERSATION:\n" + "\n".join(formatted_turns)
            else:
                return "Conversation started but no complete turns yet."
                
        except Exception as e:
            logger.error(f"Error formatting conversation context: {e}")
            return "Conversation context temporarily unavailable."
    
    async def _get_memory_context(self, context: Dict[str, Any]) -> str:
        """Get formatted memory context with error handling.
        
        Args:
            context: Safe context dictionary
            
        Returns:
            Formatted memory context string
        """
        try:
            user_profile = context.get('user_profile', {})
            
            memory_parts = []
            
            # Add user profile summary
            if isinstance(user_profile, dict):
                name = user_profile.get('name', 'Student')
                memory_parts.append(f"USER: {name}")
                
                # Add core values
                core_values = user_profile.get('core_values', [])
                if core_values:
                    if isinstance(core_values[0], dict):
                        values_list = [cv.get('value', '') for cv in core_values if cv.get('value')]
                    else:
                        values_list = [str(cv) for cf in core_values if cv]
                    
                    if values_list:
                        memory_parts.append(f"VALUES: {', '.join(values_list[:3])}")  # Top 3
                
                # Add defining moments
                defining_moments = user_profile.get('defining_moments', [])
                if defining_moments:
                    if isinstance(defining_moments[0], dict):
                        moments_list = [dm.get('title', '') for dm in defining_moments if dm.get('title')]
                    else:
                        moments_list = [str(dm) for dm in defining_moments if dm]
                    
                    if moments_list:
                        memory_parts.append(f"KEY EXPERIENCES: {', '.join(moments_list[:2])}")  # Top 2
            
            # Add recent tool usage
            recent_tools = context.get('recent_tools', [])
            if recent_tools:
                memory_parts.append(f"RECENT TOOLS: {', '.join(recent_tools[-3:])}")
            
            if memory_parts:
                return "MEMORY CONTEXT:\n" + "\n".join(memory_parts)
            else:
                return "Building memory context from new interactions."
                
        except Exception as e:
            logger.error(f"Error formatting memory context: {e}")
            return "Memory context temporarily unavailable."
    
    def _format_user_state(self, context: Dict[str, Any]) -> str:
        """Format user state with error handling.
        
        Args:
            context: Safe context dictionary
            
        Returns:
            Formatted user state string
        """
        try:
            state_parts = []
            
            # Current essay phase
            current_phase = context.get('current_phase', 'planning')
            state_parts.append(f"PHASE: {current_phase}")
            
            # Word count progress
            current_essay = context.get('current_essay', {})
            if isinstance(current_essay, dict):
                word_count = current_essay.get('word_count', 0)
                word_limit = context.get('word_limit', 650)
                if word_count > 0:
                    completion = (word_count / word_limit) * 100
                    state_parts.append(f"PROGRESS: {word_count}/{word_limit} words ({completion:.0f}%)")
                else:
                    state_parts.append(f"TARGET: {word_limit} words")
            
            # Recent activity
            recent_tools = context.get('recent_tools', [])
            if recent_tools:
                last_tool = recent_tools[-1] if recent_tools else 'none'
                state_parts.append(f"LAST ACTION: {last_tool}")
            
            return "USER STATE:\n" + "\n".join(state_parts)
            
        except Exception as e:
            logger.error(f"Error formatting user state: {e}")
            return "USER STATE: Active session in progress"
    
    async def _get_performance_context(self, context: Dict[str, Any]) -> str:
        """Get formatted performance context with error handling.
        
        Args:
            context: Safe context dictionary
            
        Returns:
            Formatted performance context string
        """
        try:
            performance = context.get('performance_context', {})
            
            if not isinstance(performance, dict):
                return "PERFORMANCE: Session starting"
            
            perf_parts = []
            
            # Response timing
            avg_time = performance.get('average_response_time', 0)
            if avg_time > 0:
                perf_parts.append(f"AVG RESPONSE: {avg_time:.1f}s")
            
            # Success rate
            success_rate = performance.get('success_rate', 0)
            if success_rate > 0:
                perf_parts.append(f"SUCCESS RATE: {success_rate*100:.0f}%")
            
            # Total interactions
            interactions = performance.get('total_interactions', 0)
            if interactions > 0:
                perf_parts.append(f"INTERACTIONS: {interactions}")
            
            # Recent tool success
            recent_success = performance.get('recent_tool_success', None)
            if recent_success is not None:
                status = "✓" if recent_success else "✗"
                perf_parts.append(f"LAST TOOL: {status}")
            
            if perf_parts:
                return "PERFORMANCE:\n" + "\n".join(perf_parts)
            else:
                return "PERFORMANCE: Initializing session metrics"
                
        except Exception as e:
            logger.error(f"Error formatting performance context: {e}")
            return "PERFORMANCE: Metrics temporarily unavailable"
    
    def _format_user_profile(self, profile: Dict[str, Any]) -> str:
        """Format user profile information."""
        if not profile:
            return "No user profile available."
        
        profile_parts = []
        
        for key in ['name', 'grade_level', 'writing_experience', 'goals']:
            if key in profile:
                profile_parts.append(f"{key.replace('_', ' ').title()}: {profile[key]}")
        
        return '\n'.join(profile_parts)
    
    def _safe_format_template(self, template: str, format_dict: Dict[str, Any]) -> str:
        """Safely format template with error handling for missing keys.
        
        Args:
            template: Template string to format
            format_dict: Dictionary with formatting values
            
        Returns:
            Formatted template string
        """
        try:
            return template.format(**format_dict)
        except KeyError as e:
            logger.warning(f"Missing template key {e}, using fallback formatting")
            # Try formatting with a subset of available keys
            import re
            
            # Find all template variables
            template_vars = re.findall(r'\{(\w+)\}', template)
            
            # Create safe format dict with only available keys
            safe_format_dict = {}
            for var in template_vars:
                if var in format_dict:
                    safe_format_dict[var] = format_dict[var]
                else:
                    # Provide fallback values for common missing keys
                    fallbacks = {
                        'user_profile': 'No profile available',
                        'conversation_context': 'No conversation history',
                        'memory_context': 'No memory context',
                        'user_state': 'User state unavailable',
                        'performance_context': 'No performance data',
                        'tool_descriptions': 'Tools available',
                        'user_input': format_dict.get('user_input', 'No input provided'),
                        'context': format_dict.get('context', {}),
                        'current_task': 'essay_assistance',
                        'essay_phase': 'unknown'
                    }
                    safe_format_dict[var] = fallbacks.get(var, f'[{var} unavailable]')
            
            return template.format(**safe_format_dict)
        except Exception as e:
            logger.error(f"Template formatting failed: {e}")
            # Return a basic fallback prompt
            return f"""
TASK: Help with essay writing

USER INPUT: {format_dict.get('user_input', 'No input provided')}

CONTEXT: {format_dict.get('context', {})}

TOOLS AVAILABLE: {format_dict.get('tool_descriptions', 'Standard essay tools')}

Please analyze the user's request and provide appropriate assistance.
"""
    
    def _classify_error(self, error_message: str) -> str:
        """Classify error type for appropriate recovery strategy."""
        error_lower = error_message.lower()
        
        if 'timeout' in error_lower or 'connection' in error_lower:
            return 'tool_failure'
        elif 'validation' in error_lower or 'invalid' in error_lower:
            return 'unclear_intent'
        elif 'missing' in error_lower or 'required' in error_lower:
            return 'context_missing'
        else:
            return 'tool_failure'
    
    def _truncate_intelligently(self, prompt: str, max_chars: int) -> str:
        """Intelligently truncate prompt while preserving structure."""
        if len(prompt) <= max_chars:
            return prompt
        
        # Try to preserve the end of the prompt (which has the user input and format instructions)
        lines = prompt.split('\n')
        
        # Always keep the last 10 lines (format instructions, user input)
        essential_lines = lines[-10:]
        remaining_chars = max_chars - len('\n'.join(essential_lines))
        
        # Fill remaining space with earlier content
        truncated_lines = []
        current_chars = 0
        
        for line in lines[:-10]:
            if current_chars + len(line) + 1 <= remaining_chars:
                truncated_lines.append(line)
                current_chars += len(line) + 1
            else:
                truncated_lines.append("[... content truncated for length ...]")
                break
        
        return '\n'.join(truncated_lines + essential_lines)


class ContextInjector:
    """Intelligent context injection and formatting.
    
    This class handles the sophisticated formatting and injection of various
    context types into prompt templates with optimization for readability
    and LLM comprehension.
    """
    
    def __init__(self):
        """Initialize the context injector."""
        self.max_context_length = 2000  # Characters per context section
        logger.debug("ContextInjector initialized")
    
    def format_conversation_context(self, history: List[Dict[str, Any]]) -> str:
        """Format conversation history for optimal LLM context.
        
        Args:
            history: List of conversation exchanges
            
        Returns:
            Formatted conversation context string
        """
        if not history:
            return "No conversation history available."
        
        formatted_lines = ["RECENT CONVERSATION:"]
        
        for i, exchange in enumerate(history[-5:], 1):  # Last 5 exchanges
            user_msg = exchange.get('user', 'N/A')
            agent_msg = exchange.get('agent', 'N/A')
            
            # Truncate long messages
            user_msg = self._truncate_message(user_msg, 100)
            agent_msg = self._truncate_message(agent_msg, 150)
            
            formatted_lines.append(f"  {i}. User: {user_msg}")
            formatted_lines.append(f"     Agent: {agent_msg}")
        
        return '\n'.join(formatted_lines)
    
    def format_memory_context(self, memories: Dict[str, Any]) -> str:
        """Format memory data for prompt injection.
        
        Args:
            memories: Memory data dictionary
            
        Returns:
            Formatted memory context string
        """
        if not memories:
            return "No memory context available."
        
        context_parts = []
        
        # Format different memory types
        if 'recent_stories' in memories:
            stories = memories['recent_stories'][:3]  # Top 3 stories
            context_parts.append("RECENT STORIES:")
            for story in stories:
                title = story.get('title', 'Untitled')
                context_parts.append(f"  - {title}")
        
        if 'writing_patterns' in memories:
            patterns = memories['writing_patterns'][:3]  # Top 3 patterns
            context_parts.append("\nWRITING PATTERNS:")
            for pattern in patterns:
                context_parts.append(f"  - {pattern}")
        
        if 'user_preferences' in memories:
            prefs = memories['user_preferences']
            context_parts.append("\nUSER PREFERENCES:")
            for key, value in list(prefs.items())[:3]:
                context_parts.append(f"  {key}: {value}")
        
        return '\n'.join(context_parts)
    
    def format_tool_context(self, tools: List[Dict[str, Any]]) -> str:
        """Format tool information for context injection.
        
        Args:
            tools: List of available tools
            
        Returns:
            Formatted tool context string
        """
        if not tools:
            return "No tools available."
        
        # Group by category and prioritize
        tool_lines = ["AVAILABLE TOOLS:"]
        
        for tool in tools[:8]:  # Limit to 8 most relevant tools
            name = tool.get('name', 'unknown')
            description = tool.get('description', 'No description')
            confidence = tool.get('confidence_threshold', 0.7)
            
            # Truncate description
            description = self._truncate_message(description, 80)
            
            tool_lines.append(f"  • {name}: {description} (confidence: {confidence})")
        
        return '\n'.join(tool_lines)
    
    def format_performance_context(self, patterns: Dict[str, Any]) -> str:
        """Format performance patterns for context injection.
        
        Args:
            patterns: Performance pattern data
            
        Returns:
            Formatted performance context string
        """
        if not patterns:
            return "No performance patterns available."
        
        context_lines = ["PERFORMANCE INSIGHTS:"]
        
        if 'success_rate' in patterns:
            context_lines.append(f"  Overall Success: {patterns['success_rate']:.1%}")
        
        if 'best_tools' in patterns:
            best_tools = patterns['best_tools'][:3]
            context_lines.append(f"  Best Tools: {', '.join(best_tools)}")
        
        if 'common_patterns' in patterns:
            common = patterns['common_patterns'][:2]
            context_lines.append("  Common Patterns:")
            for pattern in common:
                context_lines.append(f"    - {pattern}")
        
        return '\n'.join(context_lines)
    
    def inject_all_context(self, template: str, context: Dict[str, Any]) -> str:
        """Inject all available context into a template.
        
        Args:
            template: Template string with placeholders
            context: Context data dictionary
            
        Returns:
            Template with all context injected
        """
        try:
            # Prepare context components
            conversation_context = self.format_conversation_context(
                context.get('conversation_history', [])
            )
            memory_context = self.format_memory_context(
                context.get('memory_data', {})
            )
            tool_context = self.format_tool_context(
                context.get('available_tools', [])
            )
            performance_context = self.format_performance_context(
                context.get('performance_patterns', {})
            )
            user_state = context.get('user_state', 'Unknown state')
            
            # Inject into template
            injected = template.format(
                conversation_context=conversation_context,
                memory_context=memory_context,
                tool_context=tool_context,
                performance_context=performance_context,
                user_state=user_state,
                user_profile=context.get('user_profile', {}),
                **context  # Include any other context keys
            )
            
            return injected
            
        except Exception as e:
            logger.error("Error injecting context: %s", e)
            # Return template with basic context
            return template.format(
                conversation_context="Context injection failed",
                memory_context="Memory unavailable",
                tool_context="Tools unavailable", 
                performance_context="Performance data unavailable",
                user_state="State unavailable",
                user_profile={},
                **{k: str(v) for k, v in context.items() if isinstance(k, str)}
            )
    
    def _truncate_message(self, message: str, max_length: int) -> str:
        """Truncate a message to maximum length with ellipsis."""
        if len(message) <= max_length:
            return message
        return message[:max_length-3] + "..." 