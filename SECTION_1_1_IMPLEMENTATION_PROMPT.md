# 🎯 Implementation Prompt: Section 1.1 - Core Agent Structure

## 📋 **TASK OVERVIEW**

**Objective**: Create working agent class that replaces broken ReAct system  
**Time Estimate**: 4 hours  
**Files to Create**: `essay_agent/agent_autonomous.py`  
**Goal**: Replace the broken ReAct system with a working autonomous agent that can use tools

## 🔍 **BACKGROUND CONTEXT**

### **Current Problem**
The existing essay agent system has TWO architectures:
1. **✅ WORKING**: Legacy EssayAgent (`essay-agent write`) - produces complete essays
2. **❌ BROKEN**: EssayReActAgent (`essay-agent chat`) - fails at tool execution due to JSON parsing issues

The broken ReAct system:
- Fails to properly parse LLM responses for tool selection
- Defaults to conversation-only mode when tools should be used
- Has complex initialization with multiple components that don't integrate well

### **What We're Building**
A new `AutonomousEssayAgent` that:
- Uses a simple, reliable ReAct loop: observe → reason → act → respond
- Successfully executes tools from the existing registry (36+ tools available)
- Integrates with the CLI `essay-agent chat` command
- Has bulletproof error handling and logging

## 🏗️ **IMPLEMENTATION STEPS**

### **Step 1: Create AutonomousEssayAgent Class**
1. Create `essay_agent/agent_autonomous.py`
2. Import required dependencies:
   - `TOOL_REGISTRY` from `essay_agent.tools`
   - `SimpleMemory` from `essay_agent.memory.simple_memory`
   - `get_chat_llm` from `essay_agent.llm_client`
   - Basic logging and error handling utilities

### **Step 2: Implement Basic ReAct Loop**
1. `_observe()` - Extract context from memory and user input
2. `_reason()` - Simple tool selection logic (start with basic patterns)
3. `_act()` - Execute selected tool or default to conversation
4. `_respond()` - Generate natural language response

### **Step 3: CLI Integration**
1. Update `essay_agent/cli.py` to use `AutonomousEssayAgent` for chat command
2. Replace the broken `EssayReActAgent` import
3. Ensure compatibility with existing CLI structure

### **Step 4: Error Handling & Logging**
1. Add comprehensive error handling for tool execution
2. Implement logging for debugging tool selection
3. Graceful fallbacks when tools fail

### **Step 5: Tool Registry Connection**
1. Connect to existing `TOOL_REGISTRY` (36+ tools available)
2. Basic parameter mapping for tool execution
3. Handle tool results and integrate into response

## 💻 **CODE IMPLEMENTATION**

### **Main Agent Class (`essay_agent/agent_autonomous.py`)**

```python
"""Autonomous Essay Agent - Simple, Working ReAct Implementation

Replaces the broken EssayReActAgent with a reliable, tool-using agent.
"""
import asyncio
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from essay_agent.tools import REGISTRY as TOOL_REGISTRY
from essay_agent.memory.simple_memory import SimpleMemory
from essay_agent.llm_client import get_chat_llm
from essay_agent.utils.logging import debug_print

logger = logging.getLogger(__name__)


class AutonomousEssayAgent:
    """Simple, reliable autonomous essay agent with working tool execution."""
    
    def __init__(self, user_id: str):
        """Initialize the autonomous agent.
        
        Args:
            user_id: Unique identifier for the user
        """
        self.user_id = user_id
        self.tools = TOOL_REGISTRY
        self.memory = SimpleMemory(user_id)
        self.llm = get_chat_llm(temperature=0.7)
        
        # Simple performance tracking
        self.session_start = datetime.now()
        self.interaction_count = 0
        
        # Evaluation tracking (required by evaluation system)
        self.last_execution_tools = []
        self.last_memory_access = []
        
        logger.info(f"AutonomousEssayAgent initialized for user {user_id}")
    
    async def handle_message(self, user_input: str) -> str:
        """Main entry point - handle user message with ReAct loop.
        
        Args:
            user_input: User's message or request
            
        Returns:
            Agent's response
        """
        start_time = datetime.now()
        self.interaction_count += 1
        
        try:
            # ReAct Loop: Observe → Reason → Act → Respond
            context = self._observe(user_input)
            reasoning = await self._reason(user_input, context)
            action_result = await self._act(reasoning)
            response = self._respond(action_result, user_input)
            
            # Update memory with this interaction
            self._update_memory(user_input, response)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"Handled message in {execution_time:.2f}s")
            
            return response
            
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            return "I apologize, but I encountered an error. Let me try to help you in a different way. What would you like to work on with your essay?"
    
    def _observe(self, user_input: str) -> Dict[str, Any]:
        """Extract context from memory and current input.
        
        Args:
            user_input: Current user message
            
        Returns:
            Context dictionary with user profile, conversation history, etc.
        """
        # Load user profile from memory
        profile = self.memory.load(self.user_id)
        
        # Basic context extraction
        context = {
            "user_input": user_input,
            "user_profile": profile.model_dump() if hasattr(profile, 'model_dump') else {},
            "user_id": self.user_id,
            "session_info": {
                "interaction_count": self.interaction_count,
                "session_duration": (datetime.now() - self.session_start).total_seconds()
            }
        }
        
        # Track memory access for evaluation
        self.last_memory_access = ["user_profile", "session_info"]
        
        return context
    
    async def _reason(self, user_input: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Simple reasoning to decide what action to take.
        
        For now, uses basic pattern matching. Will be enhanced in Section 1.2.
        
        Args:
            user_input: User's message
            context: Context from _observe()
            
        Returns:
            Reasoning result with action to take
        """
        user_input_lower = user_input.lower()
        
        # Simple tool selection logic
        if any(word in user_input_lower for word in ["brainstorm", "ideas", "topics"]):
            return {
                "action": "tool_execution",
                "tool_name": "brainstorm",
                "reasoning": "User is asking for brainstorming help"
            }
        elif any(word in user_input_lower for word in ["outline", "structure", "organize"]):
            return {
                "action": "tool_execution", 
                "tool_name": "outline",
                "reasoning": "User needs help with essay structure"
            }
        elif any(word in user_input_lower for word in ["draft", "write", "essay"]):
            return {
                "action": "tool_execution",
                "tool_name": "draft", 
                "reasoning": "User wants to draft their essay"
            }
        elif any(word in user_input_lower for word in ["revise", "improve", "better"]):
            return {
                "action": "tool_execution",
                "tool_name": "revise",
                "reasoning": "User wants to revise their work"
            }
        elif any(word in user_input_lower for word in ["polish", "final", "submit"]):
            return {
                "action": "tool_execution",
                "tool_name": "polish",
                "reasoning": "User is ready for final polishing"
            }
        else:
            return {
                "action": "conversation",
                "reasoning": "General conversation or clarification needed"
            }
    
    async def _act(self, reasoning: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the chosen action (tool or conversation).
        
        Args:
            reasoning: Result from _reason() 
            
        Returns:
            Action result
        """
        if reasoning.get("action") == "tool_execution":
            return await self._execute_tool(reasoning)
        else:
            return await self._execute_conversation(reasoning)
    
    async def _execute_tool(self, reasoning: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool from the registry.
        
        Args:
            reasoning: Reasoning result with tool information
            
        Returns:
            Tool execution result
        """
        tool_name = reasoning.get("tool_name")
        
        if tool_name not in self.tools:
            logger.warning(f"Tool {tool_name} not found in registry")
            return {
                "type": "error",
                "message": f"I don't have access to the {tool_name} tool right now. Let me help you in another way."
            }
        
        try:
            # Basic tool parameter mapping (will be enhanced in Section 1.3)
            tool_params = self._build_tool_params(tool_name)
            
            # Execute tool
            logger.info(f"Executing tool: {tool_name}")
            result = await self.tools.acall(tool_name, **tool_params)
            
            # Track tool usage for evaluation
            self.last_execution_tools = [tool_name]
            
            return {
                "type": "tool_result",
                "tool_name": tool_name,
                "result": result
            }
            
        except Exception as e:
            logger.error(f"Tool execution failed for {tool_name}: {e}")
            return {
                "type": "error", 
                "message": f"I had trouble using the {tool_name} tool. Let me try to help you directly."
            }
    
    def _build_tool_params(self, tool_name: str) -> Dict[str, Any]:
        """Build basic parameters for tool execution.
        
        Args:
            tool_name: Name of tool to execute
            
        Returns:
            Parameters dictionary for tool
        """
        # Basic parameter mapping - will be enhanced in Section 1.3
        profile = self.memory.load(self.user_id)
        
        base_params = {
            "user_id": self.user_id,
            "profile": profile.model_dump() if hasattr(profile, 'model_dump') else str(profile)
        }
        
        # Tool-specific parameters
        if tool_name == "brainstorm":
            base_params.update({
                "essay_prompt": "Help me brainstorm essay ideas",  # Will be extracted from context later
            })
        elif tool_name == "outline":
            base_params.update({
                "story": "User's selected story",  # Will be extracted from context later
                "prompt": "Essay prompt",
                "word_count": 650
            })
        
        return base_params
    
    async def _execute_conversation(self, reasoning: Dict[str, Any]) -> Dict[str, Any]:
        """Handle conversational response when no tool is needed.
        
        Args:
            reasoning: Reasoning result
            
        Returns:
            Conversation result
        """
        return {
            "type": "conversation",
            "message": "I'm here to help you with your essay. What specific aspect would you like to work on? I can help with brainstorming ideas, creating outlines, drafting, revising, or polishing your essay."
        }
    
    def _respond(self, action_result: Dict[str, Any], user_input: str) -> str:
        """Generate natural language response from action result.
        
        Args:
            action_result: Result from _act()
            user_input: Original user input
            
        Returns:
            Natural language response
        """
        result_type = action_result.get("type")
        
        if result_type == "tool_result":
            tool_name = action_result.get("tool_name")
            result = action_result.get("result")
            
            # Format tool result into natural response
            if tool_name == "brainstorm":
                return f"Here are some essay ideas I brainstormed for you:\n\n{result}"
            elif tool_name == "outline":
                return f"I've created an outline for your essay:\n\n{result}"
            elif tool_name == "draft":
                return f"Here's a draft of your essay:\n\n{result}"
            else:
                return f"I used the {tool_name} tool and here's what I found:\n\n{result}"
                
        elif result_type == "conversation":
            return action_result.get("message", "How can I help you with your essay?")
            
        elif result_type == "error":
            return action_result.get("message", "I encountered an error, but I'm still here to help!")
            
        else:
            return "I'm here to help you with your essay writing. What would you like to work on?"
    
    def _update_memory(self, user_input: str, response: str) -> None:
        """Update memory with this interaction.
        
        Args:
            user_input: User's input
            response: Agent's response
        """
        try:
            # Basic memory update - will be enhanced in Section 2
            # For now, just ensure the SimpleMemory system works
            profile = self.memory.load(self.user_id)
            # Memory updating will be implemented in Section 2.2
            logger.debug(f"Memory updated for user {self.user_id}")
        except Exception as e:
            logger.warning(f"Memory update failed: {e}")


# For evaluation system compatibility
async def create_autonomous_agent(user_id: str) -> AutonomousEssayAgent:
    """Factory function for creating autonomous agents."""
    return AutonomousEssayAgent(user_id)
```

### **CLI Integration (`essay_agent/cli.py` modifications)**

Find the section that imports and uses `EssayReActAgent` and replace it:

```python
# Replace this import:
# from essay_agent.agent.core.react_agent import EssayReActAgent

# With this:
from essay_agent.agent_autonomous import AutonomousEssayAgent

# Then in the chat command function, replace:
# agent = EssayReActAgent(user_id=args.user)

# With:
agent = AutonomousEssayAgent(user_id=args.user)
```

## 🧪 **TESTING STRATEGY**

### **Manual Testing**
```bash
# Test basic functionality
essay-agent chat --user test_user

# Try different types of requests
essay-agent chat --user test_user --message "Help me brainstorm essay ideas"
essay-agent chat --user test_user --message "I need help with my outline"
essay-agent chat --user test_user --message "Can you help me draft my essay?"
```

### **Evaluation Testing**
```bash
# Check tool registry integration
essay-agent eval --user test_user

# Test with evaluation scenarios
essay-agent eval-conversation CONV-001-new-user-stanford-identity
```

## ✅ **SUCCESS CRITERIA**

1. **Agent responds to messages**: No crashes, returns meaningful responses
2. **Occasionally uses tools**: At least 50% of appropriate requests trigger tool execution
3. **CLI integration works**: `essay-agent chat` command functions properly
4. **Basic error handling**: Graceful failures, no system crashes
5. **Tool registry connection**: Can access and execute tools from existing registry

## 🎯 **DELIVERABLE**

A working `AutonomousEssayAgent` that:
- ✅ Responds to chat messages
- ✅ Successfully uses tools 50%+ of the time (compared to 0% for broken system)
- ✅ No more JSON parsing failures
- ✅ Basic error handling working
- ✅ Integrates with existing CLI and evaluation system

This agent will be the foundation for all subsequent sections, where we'll add context intelligence, better reasoning, and advanced features.

## 🔧 **IMPLEMENTATION NOTES**

1. **Keep it simple**: This is Section 1.1 - focus on basic functionality
2. **Use existing systems**: Leverage SimpleMemory, TOOL_REGISTRY, existing CLI structure
3. **Add logging**: Include debug logging for troubleshooting
4. **Error recovery**: Always provide fallback responses
5. **Evaluation compatibility**: Maintain attributes needed by evaluation system

## 📁 **FILE STRUCTURE**

```
essay_agent/
├── agent_autonomous.py          # ← CREATE THIS (main implementation)
├── cli.py                       # ← MODIFY (update imports and chat command)
└── tools/                       # ← USE EXISTING (TOOL_REGISTRY)
    └── __init__.py              # Contains REGISTRY with 36+ tools
```

**Ready to implement! This will replace the broken ReAct system with a working autonomous agent.** 