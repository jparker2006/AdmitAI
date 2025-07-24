"""FastAPI server for essay agent debug frontend."""

import asyncio
import json
import logging
import os
import sys
import traceback
import socket
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import uuid

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import uvicorn
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from essay_agent.agent_autonomous import AutonomousEssayAgent
from essay_agent.memory.smart_memory import SmartMemory
from essay_agent.intelligence.context_engine import ContextEngine
from essay_agent.state_manager import EssayStateManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def find_free_port(start_port: int = 8000, max_port: int = 8099) -> int:
    """Find an available port in the given range."""
    for port in range(start_port, max_port + 1):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.bind(('127.0.0.1', port))
                return port
        except OSError:
            continue
    raise OSError(f"No free ports found in range {start_port}-{max_port}")

# Enhanced debug state with real-time event streaming
debug_state = {
    "chat_history": [],
    "memory_snapshots": [],
    "planner_calls": [],
    "tool_executions": [],
    "error_log": [],
    "agent_metrics": {},
    "network_requests": [],
    "live_events": []  # For real-time streaming
}

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Remaining connections: {len(self.active_connections)}")
    
    async def broadcast(self, message: dict):
        """Broadcast debug event to all connected clients."""
        if not self.active_connections:
            return
            
        message_json = json.dumps(message, default=str)
        disconnected = []
        
        for connection in self.active_connections:
            try:
                await connection.send_text(message_json)
            except Exception as e:
                logger.warning(f"Failed to send to WebSocket: {e}")
                disconnected.append(connection)
        
        # Remove disconnected clients
        for conn in disconnected:
            self.active_connections.remove(conn)

manager = ConnectionManager()

async def emit_debug_event(event_type: str, data: dict):
    """Emit a debug event to all connected WebSocket clients."""
    event = {
        "timestamp": datetime.now().isoformat(),
        "event_type": event_type,
        "data": data,
        "session_id": str(uuid.uuid4())[:8]
    }
    
    debug_state["live_events"].append(event)
    
    # Keep only last 100 events
    if len(debug_state["live_events"]) > 100:
        debug_state["live_events"] = debug_state["live_events"][-100:]
    
    await manager.broadcast(event)

app = FastAPI(title="Essay Agent Debug Frontend", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Enhanced logging middleware
@app.middleware("http")
async def debug_logging_middleware(request, call_next):
    start_time = datetime.now()
    
    # Log request
    await emit_debug_event("http_request", {
        "method": request.method,
        "url": str(request.url),
        "headers": dict(request.headers)
    })
    
    try:
        response = await call_next(request)
        
        # Log response
        duration = (datetime.now() - start_time).total_seconds()
        await emit_debug_event("http_response", {
            "method": request.method,
            "url": str(request.url),
            "status_code": response.status_code,
            "duration_seconds": duration
        })
        
        return response
        
    except Exception as e:
        # Log error
        duration = (datetime.now() - start_time).total_seconds()
        await emit_debug_event("http_error", {
            "method": request.method,
            "url": str(request.url),
            "error": str(e),
            "duration_seconds": duration,
            "traceback": traceback.format_exc()
        })
        raise

# Request/Response models
class ChatRequest(BaseModel):
    message: str
    user_id: str = "debug_user"
    clear_history: bool = False
    essay_context: Optional[dict] = None

class ChatResponse(BaseModel):
    response: str
    debug_data: Dict[str, Any]

class SetupRequest(BaseModel):
    essay_prompt: str
    school: str
    user_id: str = "debug_user"

class SetupResponse(BaseModel):
    status: str
    message: str

class DebugAgent(AutonomousEssayAgent):
    """Enhanced agent that captures debug information."""
    
    def __init__(self, user_id: str):
        super().__init__(user_id)
        self.debug_session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_start = datetime.now()
        self.interaction_count = 0
        self.last_execution_tools = []
        
    async def handle_message(self, user_input: str) -> str:
        """Enhanced message handler with comprehensive debug capture."""
        session_start = datetime.now()
        self.interaction_count += 1
        
        await emit_debug_event("agent_message_start", {
            "user_input": user_input,
            "user_id": self.user_id,
            "interaction_count": self.interaction_count
        })
        
        try:
            # Clear any previous turn debug data
            turn_debug = {
                "timestamp": session_start.isoformat(),
                "user_input": user_input,
                "memory_before": {},
                "context_snapshot": {},
                "planner_prompt": "",
                "planner_response": "",
                "tool_sequence": [],
                "memory_after": {},
                "errors": [],
                "performance": {}
            }
            
            # Capture memory state before
            try:
                turn_debug["memory_before"] = {
                    "working_memory": self.memory.get_recent_chat(k=5),
                    "profile": self.memory.get("college", "No college set"),
                    "essay_prompt": self.memory.get("essay_prompt", "No prompt set"),
                    "conversation_count": len(self.memory.get_recent_chat(k=100))
                }
                
                await emit_debug_event("memory_snapshot", {
                    "type": "before_processing",
                    "data": turn_debug["memory_before"]
                })
                
            except Exception as e:
                error_msg = f"Memory capture error: {str(e)}"
                turn_debug["errors"].append(error_msg)
                await emit_debug_event("agent_error", {
                    "type": "memory_capture",
                    "error": error_msg,
                    "traceback": traceback.format_exc()
                })
            
            # Hook into the original handle_message but capture intermediate steps
            response = await self._handle_message_with_debug(user_input, turn_debug)
            
            # Capture final state
            turn_debug["agent_response"] = response
            turn_debug["performance"]["total_time"] = (datetime.now() - session_start).total_seconds()
            
            # Store in global debug state
            debug_state["chat_history"].append({
                "user": user_input,
                "agent": response,
                "timestamp": session_start.isoformat()
            })
            
            debug_state["memory_snapshots"].append(turn_debug["memory_before"])
            debug_state["tool_executions"].extend(turn_debug["tool_sequence"])
            
            if turn_debug["errors"]:
                debug_state["error_log"].extend(turn_debug["errors"])
            
            await emit_debug_event("agent_message_complete", {
                "user_input": user_input,
                "agent_response": response,
                "performance": turn_debug["performance"],
                "tools_used": self.last_execution_tools
            })
                
            return response
            
        except Exception as e:
            error_msg = f"Agent error: {str(e)}\n{traceback.format_exc()}"
            debug_state["error_log"].append({
                "timestamp": datetime.now().isoformat(),
                "error": error_msg,
                "user_input": user_input
            })
            
            await emit_debug_event("agent_error", {
                "type": "message_handling",
                "error": str(e),
                "user_input": user_input,
                "traceback": traceback.format_exc()
            })
            
            return f"I encountered an error: {str(e)}"
    
    async def _handle_message_with_debug(self, user_input: str, turn_debug: Dict) -> str:
        """Handle message with debug information capture."""
        try:
            # Save user input immediately
            self.memory.add_message("user", user_input)
            
            # === OBSERVE with debug capture ===
            await emit_debug_event("agent_observe_start", {"user_input": user_input})
            context = await self._observe(user_input)
            turn_debug["context_snapshot"] = self._sanitize_for_json(context)
            await emit_debug_event("agent_observe_complete", {"context": turn_debug["context_snapshot"]})
            
            # === REASON with debug capture ===
            await emit_debug_event("agent_reason_start", {"context": turn_debug["context_snapshot"]})
            reasoning = await self._reason_with_debug(user_input, context, turn_debug)
            await emit_debug_event("agent_reason_complete", {"reasoning": reasoning})
            
            # === ACT with debug capture ===
            await emit_debug_event("agent_act_start", {"reasoning": reasoning})
            action_result = await self._act_with_debug(reasoning, user_input, turn_debug)
            await emit_debug_event("agent_act_complete", {"action_result": action_result})
            
            # === RESPOND ===
            response = await self._respond(action_result, user_input)
            
            # Save agent response
            self.memory.add_message("assistant", response)
            
            # Learning hook
            self.memory.learn({
                "user_input": user_input,
                "agent_response": response,
                "tool_result": action_result if isinstance(action_result, dict) else {},
            })
            
            # Enhanced response
            try:
                from essay_agent.agents.response_enhancer import ResponseEnhancer
                context_meta = {
                    "college": self.memory.get("college", ""),
                    "essay_prompt": self.memory.get("essay_prompt", ""),
                }
                politeness_level = int(os.getenv("ESSAY_AGENT_POLITENESS_LEVEL", "1"))
                enhanced = ResponseEnhancer.enhance(response, context=context_meta, politeness_level=politeness_level)
                
                await emit_debug_event("response_enhanced", {
                    "original": response,
                    "enhanced": enhanced,
                    "politeness_level": politeness_level
                })
                
                return enhanced
            except Exception as e:
                await emit_debug_event("response_enhancement_error", {
                    "error": str(e),
                    "fallback_response": response
                })
                return response
            
        except Exception as e:
            error_msg = f"Message handling error: {str(e)}"
            turn_debug["errors"].append(error_msg)
            await emit_debug_event("agent_error", {
                "type": "message_handling_detailed",
                "error": error_msg,
                "traceback": traceback.format_exc()
            })
            return f"I encountered an error: {str(e)}"
    
    async def _reason_with_debug(self, user_input: str, context: Dict, turn_debug: Dict) -> Dict:
        """Reasoning with debug capture."""
        try:
            # Import tool names for planner
            from essay_agent.tools import REGISTRY as TOOL_REGISTRY
            from essay_agent.planner_prompt import PlannerPrompt
            
            # Initialize planner with available tool names
            tool_names = list(TOOL_REGISTRY.keys())
            planner = PlannerPrompt(tool_names)
            
            # Build planner context
            planner_context = {
                "recent_chat": self.memory.get_recent_chat(k=5) if hasattr(self.memory, 'get_recent_chat') else [],
                "last_tool": getattr(self, 'last_execution_tools', [])[-1] if getattr(self, 'last_execution_tools', []) else "none",
                "profile": {
                    "college": self.memory.get("college", "") if hasattr(self.memory, 'get') else "",
                    "essay_prompt": self.memory.get("essay_prompt", "") if hasattr(self.memory, 'get') else "",
                    "preferred_word_count": 650
                },
                "tool_stats": "",
                "failure_count": 0
            }
            
            # Build prompt
            prompt_str = planner.build_prompt(user_input, planner_context)
            
            await emit_debug_event("planner_prompt_build", {
                "user_input": user_input,
                "context": planner_context,
                "prompt": prompt_str[:500] + "..." if len(prompt_str) > 500 else prompt_str
            })
            
            # Get LLM response (with offline fallback)
            import os
            offline = os.getenv("ESSAY_AGENT_OFFLINE_TEST") == "1"
            if offline:
                plan_list = planner.parse_response("{}", offline=True)
                raw_response = "OFFLINE_MODE"
            else:
                try:
                    from essay_agent.llm_client import get_chat_llm
                    llm = get_chat_llm()
                    raw_response = await llm.apredict(prompt_str)
                except Exception as exc:
                    raw_response = "{}"
                plan_list = planner.parse_response(raw_response, offline=False)
            
            # Convert plan list to reasoning format expected by _act_with_debug
            reasoning = {
                "action": "tool_plan",
                "plan": plan_list,
                "raw_response": raw_response,
                "planner_context": planner_context
            }
            
            turn_debug["planner_prompt"] = prompt_str[:500] + "..." if len(prompt_str) > 500 else prompt_str
            turn_debug["planner_response"] = self._sanitize_for_json(reasoning)
            
            await emit_debug_event("planner_response", {
                "reasoning": reasoning,
                "tools_planned": plan_list,
                "plan_count": len(plan_list)
            })
            
            return reasoning
            
        except Exception as e:
            error_msg = f"Reasoning error: {str(e)}"
            turn_debug["errors"].append(error_msg)
            await emit_debug_event("planner_error", {
                "error": error_msg,
                "traceback": traceback.format_exc()
            })
            # Return fallback reasoning in the expected format
            fallback_plan = [{"tool": "chat_response", "args": {"message": user_input}}]
            return {
                "action": "tool_plan",
                "plan": fallback_plan,
                "raw_response": "FALLBACK_MODE",
                "planner_context": {}
            }
    
    async def _act_with_debug(self, reasoning: Dict, user_input: str, turn_debug: Dict) -> Any:
        """Action execution with debug capture."""
        try:
            # Use the agent's properly initialized orchestrator instead of creating a new one
            orchestrator = self.orchestrator
            
            self.last_execution_tools = []
            
            if isinstance(reasoning, dict) and "plan" in reasoning:
                plan_steps = reasoning["plan"]
                if isinstance(plan_steps, list):
                    for step in plan_steps:
                        # Ensure step is a dictionary
                        if isinstance(step, dict):
                            tool_name = step.get("tool", "unknown")
                            tool_args = step.get("args", {})
                        elif isinstance(step, str):
                            # Handle case where step is a string
                            tool_name = "chat_response"
                            tool_args = {"message": step}
                        else:
                            # Handle other unexpected types
                            tool_name = "chat_response"
                            tool_args = {"message": str(step)}
                        
                        start_time = datetime.now()
                        
                        try:
                            from essay_agent.tools.integration import execute_tool, build_params
                            
                            # Build complete parameters using the same logic as autonomous agent
                            # CRITICAL FIX: Pass full context snapshot (with user_profile) instead of just tool_args
                            context_snapshot = await self.ctx_engine.snapshot(user_input)
                            full_context = context_snapshot.model_dump()
                            
                            full_params = build_params(
                                tool_name, 
                                user_id=self.user_id, 
                                user_input=user_input, 
                                context=full_context  # Fixed: was tool_args, now full context
                            )
                            
                            # Enhanced parameter mapping for specific tools
                            full_params = self._enhance_tool_parameters(
                                tool_name, full_params, tool_args, user_input
                            )
                            
                            await emit_debug_event("tool_execution_start", {
                                "tool": tool_name,
                                "raw_args": tool_args,
                                "resolved_args": self._sanitize_for_json(full_params)
                            })
                            
                            result = await execute_tool(tool_name, **full_params)
                            execution_time = (datetime.now() - start_time).total_seconds()
                            
                            tool_execution = {
                                "tool": tool_name,
                                "tool_name": tool_name,  # Frontend expects tool_name field
                                "tool_args": self._sanitize_for_json(full_params),  # Frontend expects tool_args
                                "args": self._sanitize_for_json(full_params),
                                "result": self._sanitize_for_json(result),
                                "execution_time": execution_time,
                                "success": True
                            }
                            
                            turn_debug["tool_sequence"].append(tool_execution)
                            self.last_execution_tools.append(tool_name)
                            
                            await emit_debug_event("tool_execution_complete", tool_execution)
                            
                        except Exception as tool_error:
                            execution_time = (datetime.now() - start_time).total_seconds()
                            
                            tool_execution = {
                                "tool": tool_name,
                                "tool_name": tool_name,  # Frontend expects tool_name field
                                "tool_args": self._sanitize_for_json(full_params) if 'full_params' in locals() else tool_args,  # Frontend expects tool_args
                                "args": self._sanitize_for_json(full_params) if 'full_params' in locals() else tool_args,
                                "error": str(tool_error),
                                "execution_time": execution_time,
                                "success": False
                            }
                            
                            turn_debug["tool_sequence"].append(tool_execution)
                            
                            await emit_debug_event("tool_execution_error", {
                                **tool_execution,
                                "traceback": traceback.format_exc()
                            })
            
            # Return the last successful result in the correct format for _respond
            if turn_debug["tool_sequence"]:
                last_result = turn_debug["tool_sequence"][-1]
                # Return structured action_result like the parent _act method
                if isinstance(last_result, dict) and last_result.get("success"):
                    return {
                        "type": "tool_result",
                        "tool_name": last_result.get("tool", "unknown"),
                        "result": last_result.get("result", {})
                    }
                else:
                    # Handle failed tools
                    return {
                        "type": "error",
                        "message": f"Tool execution failed: {last_result.get('error', 'Unknown error')}"
                    }
            
            return {
                "type": "conversation",
                "message": "No tools were executed for this request."
            }
            
        except Exception as e:
            error_msg = f"Action execution error: {str(e)}"
            turn_debug["errors"].append(error_msg)
            await emit_debug_event("action_execution_error", {
                "error": error_msg,
                "traceback": traceback.format_exc()
            })
            return {
                "type": "error",
                "message": f"Action failed: {str(e)}"
            }
    
    def _enhance_tool_parameters(self, tool_name: str, base_params: Dict[str, Any], 
                                raw_args: Dict[str, Any], user_input: str) -> Dict[str, Any]:
        """Enhance tool parameters with specific mappings for different tools."""
        enhanced_params = dict(base_params)
        
        # Tool-specific parameter mappings
        if tool_name in ["brainstorm_specific", "brainstorm"]:
            # These tools need 'topic' or 'user_input' 
            if 'topic' not in enhanced_params and 'user_input' not in enhanced_params:
                # Try to get topic from raw args, or use user_input as fallback
                enhanced_params['topic'] = raw_args.get('topic') or raw_args.get('prompt') or user_input
                enhanced_params['user_input'] = user_input
        
        elif tool_name in ["classify_prompt", "prompt_classifier"]:
            # These tools don't need additional parameters - they generate theme as output
            pass
        
        elif tool_name in ["suggest_strategy"]:
            # Strategy tools need both essay_prompt and profile
            if 'profile' not in enhanced_params:
                enhanced_params['profile'] = self._get_user_profile_string()
        
        elif tool_name in ["chat_response"]:
            # Chat response tools need message
            if 'message' not in enhanced_params:
                enhanced_params['message'] = raw_args.get('message') or user_input
        
        # Always ensure user_id is present
        enhanced_params['user_id'] = self.user_id
        
        return enhanced_params
    
    def _get_user_profile_string(self) -> str:
        """Get user profile as a string for tools that need it."""
        try:
            profile = self.memory.get_user_profile() if hasattr(self.memory, 'get_user_profile') else {}
            if isinstance(profile, dict):
                return f"User: {profile.get('name', 'Student')}, Interests: {', '.join(profile.get('interests', []))}"
            return str(profile) if profile else "Student profile"
        except Exception:
            return "Student profile"
    
    def _sanitize_for_json(self, data: Any) -> Any:
        """Sanitize data for JSON serialization."""
        if isinstance(data, dict):
            return {k: self._sanitize_for_json(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._sanitize_for_json(item) for item in data]
        elif hasattr(data, 'model_dump'):
            return data.model_dump()
        elif hasattr(data, '__dict__'):
            return str(data)
        else:
            return data

# Global agent instance
agent: Optional[DebugAgent] = None

async def process_message_with_unified_state(
    user_id: str, 
    message: str, 
    essay_context: dict
) -> str:
    """Process message using unified state approach with enhanced debugging."""
    global agent
    
    try:
        # Emit debug event for unified state processing
        await emit_debug_event("unified_state_processing_start", {
            "user_id": user_id,
            "message": message,
            "essay_context": essay_context
        })
        
        # Initialize agent if needed (use the updated AutonomousEssayAgent)
        if agent is None or agent.user_id != user_id:
            # Use regular AutonomousEssayAgent instead of DebugAgent for unified state
            from essay_agent.agent_autonomous import AutonomousEssayAgent
            agent = AutonomousEssayAgent(user_id)
            
            # Set up essay context in agent memory
            if essay_context.get('college'):
                agent.memory.set("college", essay_context['college'])
            if essay_context.get('essay_prompt'):
                agent.memory.set("essay_prompt", essay_context['essay_prompt'])
        
        # Process message through updated agent (now supports unified state)
        response = await agent.handle_message(message)
        
        # Load state for debugging info
        from essay_agent.state_manager import EssayStateManager
        manager = EssayStateManager()
        state = manager.load_state(user_id, "current")
        
        # Emit completion event with state info
        await emit_debug_event("unified_state_processing_complete", {
            "user_id": user_id,
            "response_length": len(response),
            "state_summary": state.get_context_summary() if state else {},
            "tools_used": agent.last_execution_tools if hasattr(agent, 'last_execution_tools') else []
        })
        
        return response
        
    except Exception as e:
        await emit_debug_event("unified_state_processing_error", {
            "user_id": user_id,
            "error": str(e),
            "traceback": traceback.format_exc()
        })
        
        # Fallback to regular response
        return f"I encountered an issue processing your request. Let me try to help: {message}"

# Global essay context tracking
current_essay_context = {
    "user_id": None,
    "college": None,
    "essay_id": None,
    "essay_title": None
}

async def setup_agent_context(agent: DebugAgent, user_id: str, essay_context: dict):
    """Set up agent with user profile and essay context."""
    try:
        # Load user profile
        user_profile_file = Path(f"memory_store/{user_id}.json")
        if user_profile_file.exists():
            with open(user_profile_file, 'r') as f:
                profile_data = json.load(f)
            
            # Extract key user information
            user_info = profile_data.get("user_info", {})
            academic_profile = profile_data.get("academic_profile", {})
            core_values = profile_data.get("core_values", [])
            
            # Set up memory with user context
            if hasattr(agent, 'memory'):
                # CRITICAL: Set essay context in memory for contextual composition
                if essay_context:
                    if essay_context.get('college'):
                        agent.memory.set("college", essay_context['college'])
                        logger.info(f"✅ Set college: {essay_context['college']}")
                    if essay_context.get('essay_prompt'):
                        agent.memory.set("essay_prompt", essay_context['essay_prompt'])
                        logger.info(f"✅ Set essay prompt: {essay_context['essay_prompt'][:50]}...")
                
                # Add user profile context
                # Safely process core values - handle both dict and string formats
                safe_core_values = []
                for v in core_values[:3]:
                    if isinstance(v, dict):
                        safe_core_values.append(v.get('value', str(v)))
                    else:
                        safe_core_values.append(str(v))
                
                profile_context = f"""
User Profile - {user_info.get('name', user_id)}:
- Academic: GPA {academic_profile.get('gpa', 'N/A')}, {', '.join(academic_profile.get('courses', [])[:3])}
- Target Colleges: {', '.join(user_info.get('college_list', [])[:3])}
- Core Values: {', '.join(safe_core_values)}
"""
                
                # Add essay context if available
                if essay_context and essay_context.get('college') and essay_context.get('essay_title'):
                    essay_context_str = f"""
Current Essay Context:
- College: {essay_context['college']}
- Essay: {essay_context['essay_title']}
- User ID: {essay_context['user_id']}
"""
                    profile_context += essay_context_str
                
                # Store context in agent memory
                agent.memory.add_chat_turn(
                    {"human": "Context setup"},
                    {"ai": f"Understood. I'm helping {user_info.get('name', user_id)} with their essay work. {profile_context}"}
                )
                
                logger.info(f"✅ Agent context setup complete for {user_id}")
            
    except Exception as e:
        logger.warning(f"Could not fully setup agent context for {user_id}: {e}")

async def build_contextualized_message(message: str, user_id: str, essay_context: dict) -> str:
    """Build a contextualized message with essay and user context."""
    try:
        # Start with the original message
        contextualized = message
        
        # Add essay context if available
        if essay_context and essay_context.get('college') and essay_context.get('essay_title'):
            context_prefix = f"[Working on '{essay_context['essay_title']}' for {essay_context['college']}] "
            contextualized = context_prefix + message
        
        return contextualized
        
    except Exception as e:
        logger.warning(f"Error building contextualized message: {e}")
        return message

@app.post("/api/switch-essay")
async def switch_essay(request: dict):
    """Switch to a specific essay context and load its conversation history."""
    global agent, current_essay_context
    
    try:
        user_id = request.get("user_id")
        college = request.get("college") 
        essay_id = request.get("essay_id", "current")
        essay_title = request.get("essay_title", "Current Essay")
        
        if not user_id or not college:
            raise HTTPException(status_code=400, detail="user_id and college are required")
        
        # Update current context
        current_essay_context.update({
            "user_id": user_id,
            "college": college,
            "essay_id": essay_id,
            "essay_title": essay_title
        })
        
        # Initialize agent for this user if needed
        if agent is None or agent.user_id != user_id:
            agent = DebugAgent(user_id)
        
        # Load essay-specific conversation history
        conversation_file = Path(f"memory_store/{user_id}_{college}_{essay_id}.conv.json")
        essay_chat_history = []
        
        if conversation_file.exists():
            try:
                with open(conversation_file, 'r') as f:
                    conv_data = json.load(f)
                essay_chat_history = conv_data.get("chat_history", [])
                logger.info(f"Loaded {len(essay_chat_history)} messages for {user_id}/{college}/{essay_id}")
            except Exception as e:
                logger.warning(f"Could not load conversation for {user_id}/{college}/{essay_id}: {e}")
        
        # Clear global debug state and load essay-specific history
        debug_state["chat_history"] = essay_chat_history
        debug_state["memory_snapshots"] = []
        debug_state["tool_executions"] = []
        debug_state["error_log"] = []
        
        return {
            "status": "success",
            "message": f"Switched to {essay_title} for {college}",
            "context": current_essay_context,
            "chat_history": essay_chat_history,
            "conversation_length": len(essay_chat_history)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error switching essay context: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/current-essay")
async def get_current_essay():
    """Get the currently active essay context."""
    return {
        "context": current_essay_context,
        "has_active_essay": bool(current_essay_context.get("user_id"))
    }

async def save_essay_conversation_internal():
    """Internal function to save conversation to essay-specific file."""
    try:
        if not current_essay_context.get("user_id"):
            return
        
        user_id = current_essay_context["user_id"]
        college = current_essay_context.get("college", "default")
        essay_id = current_essay_context.get("essay_id", "current")
        
        conversation_file = Path(f"memory_store/{user_id}_{college}_{essay_id}.conv.json")
        
        # Save current debug chat history to essay-specific file
        conv_data = {
            "chat_history": debug_state["chat_history"],
            "context": current_essay_context,
            "last_updated": datetime.now().isoformat()
        }
        
        with open(conversation_file, 'w') as f:
            json.dump(conv_data, f, indent=2)
        
        logger.info(f"✅ Auto-saved conversation to {conversation_file}")
        
    except Exception as e:
        logger.warning(f"Error auto-saving conversation: {e}")

@app.post("/api/save-essay-conversation")
async def save_essay_conversation():
    """Save current conversation to essay-specific file."""
    try:
        if not current_essay_context.get("user_id"):
            return {"status": "no_context", "message": "No active essay context"}
        
        user_id = current_essay_context["user_id"]
        college = current_essay_context["college"]
        essay_id = current_essay_context["essay_id"]
        
        conversation_file = Path(f"memory_store/{user_id}_{college}_{essay_id}.conv.json")
        
        # Save current debug chat history to essay-specific file
        conv_data = {
            "chat_history": debug_state["chat_history"],
            "context": current_essay_context,
            "last_updated": datetime.now().isoformat()
        }
        
        with open(conversation_file, 'w') as f:
            json.dump(conv_data, f, indent=2)
        
        return {
            "status": "saved",
            "message": f"Conversation saved for {current_essay_context['essay_title']}",
            "file": str(conversation_file)
        }
        
    except Exception as e:
        logger.error(f"Error saving essay conversation: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/", response_class=HTMLResponse)
async def get_frontend():
    """Serve the main debug interface."""
    frontend_dir = Path(__file__).parent
    html_file = frontend_dir / "index.html"
    
    if html_file.exists():
        return FileResponse(html_file)
    else:
        # Return a basic HTML page if the file doesn't exist yet
        return HTMLResponse("""
        <!DOCTYPE html>
        <html>
        <head><title>Essay Agent Debug</title></head>
        <body>
            <h1>Essay Agent Debug Interface</h1>
            <p>Frontend files not found. Please create index.html.</p>
        </body>
        </html>
        """)

@app.get("/api/users")
async def get_users():
    """Get list of existing users from memory store."""
    try:
        memory_dir = Path("memory_store")
        if not memory_dir.exists():
            return {"users": []}
        
        users = []
        
        # Scan for .json files (user profiles)
        for json_file in memory_dir.glob("*.json"):
            user_id = json_file.stem
            
            # Skip conversation files and lock files
            if ".conv" in user_id or ".lock" in user_id:
                continue
                
            try:
                # Load user profile to get name and info
                with open(json_file, 'r') as f:
                    profile_data = json.load(f)
                
                user_info = profile_data.get("user_info", {})
                name = user_info.get("name", user_id)
                
                # Get essay prompt and college if exists in model_extra
                essay_prompt = profile_data.get("essay_prompt", "")
                college = profile_data.get("college", "")
                
                # Check model_extra for additional fields
                model_extra = profile_data.get("model_extra", {})
                if not essay_prompt:
                    essay_prompt = model_extra.get("essay_prompt", "")
                if not college:
                    college = model_extra.get("college", "")
                
                # Extract essay history and college work for file system display
                essay_history = profile_data.get("essay_history", [])
                college_story_usage = profile_data.get("college_story_usage", {})
                
                # Build essay portfolio structure
                essay_portfolio = {}
                
                # Add current active essay if exists
                if essay_prompt and college:
                    if college not in essay_portfolio:
                        essay_portfolio[college] = []
                    essay_portfolio[college].append({
                        "title": "Current Essay",
                        "prompt": essay_prompt[:80] + "..." if len(essay_prompt) > 80 else essay_prompt,
                        "status": "active",
                        "type": "essay"
                    })
                
                # Add historical essays
                for essay in essay_history:
                    essay_college = essay.get("college", "Unknown")
                    if essay_college not in essay_portfolio:
                        essay_portfolio[essay_college] = []
                    essay_portfolio[essay_college].append({
                        "title": essay.get("title", "Untitled Essay"),
                        "prompt": essay.get("prompt", "")[:80] + "..." if len(essay.get("prompt", "")) > 80 else essay.get("prompt", ""),
                        "status": essay.get("status", "draft"),
                        "type": "essay",
                        "word_count": essay.get("word_count", 0),
                        "last_modified": essay.get("last_modified", "")
                    })
                
                # Add story usage by college
                for college_name, stories in college_story_usage.items():
                    if college_name not in essay_portfolio:
                        essay_portfolio[college_name] = []
                    
                    if isinstance(stories, dict):
                        for story_name, usage_info in stories.items():
                            essay_portfolio[college_name].append({
                                "title": story_name,
                                "prompt": f"Used in {usage_info.get('essay_type', 'essay')}",
                                "status": "used",
                                "type": "story"
                            })
                    elif isinstance(stories, list):
                        for story in stories:
                            essay_portfolio[college_name].append({
                                "title": story,
                                "prompt": "Personal story",
                                "status": "used", 
                                "type": "story"
                            })
                
                users.append({
                    "user_id": user_id,
                    "name": name if name and name != user_id else f"User {user_id[:8]}...",
                    "essay_prompt": essay_prompt[:100] + "..." if len(essay_prompt) > 100 else essay_prompt,
                    "college": college,
                    "has_data": bool(essay_prompt or college or profile_data.get("defining_moments")),
                    "essay_portfolio": essay_portfolio,
                    "stats": {
                        "total_essays": len(essay_history) + (1 if essay_prompt else 0),
                        "colleges": list(essay_portfolio.keys()),
                        "last_active": model_extra.get("last_modified", "")
                    }
                })
                
            except (json.JSONDecodeError, Exception):
                # Skip corrupted files
                continue
        
        # Sort by user_id for consistency
        users.sort(key=lambda x: x["user_id"])
        
        return {"users": users}
        
    except Exception as e:
        logger.error(f"Error getting users: {e}")
        return {"users": []}

@app.post("/api/setup", response_model=SetupResponse)
async def setup_session(request: SetupRequest):
    """Setup the essay writing session with prompt and school."""
    global agent, current_essay_context
    
    try:
        # Validate inputs
        if not request.essay_prompt.strip():
            raise HTTPException(status_code=400, detail="Essay prompt is required")
        
        if not request.school.strip():
            raise HTTPException(status_code=400, detail="School name is required")
        
        # Check word count (rough estimate: avg 5 chars per word)
        estimated_words = len(request.essay_prompt.split())
        if estimated_words > 650:
            raise HTTPException(status_code=400, detail=f"Essay prompt too long ({estimated_words} words). Please keep it under 650 words.")
        
        # Initialize agent if needed
        if agent is None:
            agent = DebugAgent(request.user_id)
        
        # CRITICAL: Update current_essay_context for chat endpoint
        current_essay_context.update({
            "user_id": request.user_id,
            "college": request.school.strip(),
            "essay_prompt": request.essay_prompt.strip(),
            "essay_title": f"{request.school} Challenge Essay",
            "essay_id": "current"
        })
        
        # Save to agent memory using SmartMemory API
        from essay_agent.memory.smart_memory import SmartMemory
        memory = SmartMemory(request.user_id)
        memory.set("essay_prompt", request.essay_prompt.strip())
        memory.set("college", request.school.strip())
        memory.set("onboarding_completed", True)
        memory.save()
        
        # CRITICAL: Set up agent context properly
        await setup_agent_context(agent, request.user_id, current_essay_context)
        
        # Add initial context to conversation memory
        initial_context = f"User is working on an essay for {request.school}. Essay prompt: {request.essay_prompt.strip()}"
        if hasattr(agent, 'memory') and hasattr(agent.memory, 'add_chat_turn'):
            agent.memory.add_chat_turn(
                {"human": f"Setup: {request.essay_prompt.strip()}"}, 
                {"ai": f"Ready to help with your {request.school} essay!"}
            )
        else:
            # Fallback: just save the context as a note
            memory.set("initial_context", initial_context)
        
        # Update debug state
        debug_state["memory_snapshots"].append({
            "essay_prompt": request.essay_prompt.strip(),
            "college": request.school.strip(),
            "onboarding_completed": True,
            "setup_timestamp": datetime.now().isoformat()
        })
        
        logger.info(f"Session setup completed for {request.school} essay")
        
        return SetupResponse(status="success", message=f"Setup complete for {request.school} essay")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Setup endpoint error: {e}")
        raise HTTPException(status_code=500, detail=f"Setup failed: {str(e)}")

# WebSocket endpoint for real-time debug streaming
@app.websocket("/ws/debug")
async def websocket_debug_stream(websocket: WebSocket):
    """WebSocket endpoint for real-time debug event streaming."""
    await manager.connect(websocket)
    
    try:
        # Send initial state
        await websocket.send_text(json.dumps({
            "event_type": "initial_state",
            "data": {
                "debug_state": debug_state,
                "connection_count": len(manager.active_connections)
            },
            "timestamp": datetime.now().isoformat()
        }, default=str))
        
        # Keep connection alive and handle incoming messages
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle client commands
                if message.get("type") == "ping":
                    await websocket.send_text(json.dumps({
                        "event_type": "pong",
                        "timestamp": datetime.now().isoformat()
                    }))
                elif message.get("type") == "get_full_state":
                    await websocket.send_text(json.dumps({
                        "event_type": "full_state_response",
                        "data": debug_state,
                        "timestamp": datetime.now().isoformat()
                    }, default=str))
                    
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.warning(f"WebSocket message handling error: {e}")
                
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(websocket)

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Handle chat requests with unified state approach."""
    global current_essay_context
    
    await emit_debug_event("chat_request_received", {
        "user_id": request.user_id,
        "message_length": len(request.message),
        "has_essay_context": bool(request.essay_context),
        "clear_history": request.clear_history
    })
    
    try:
        # Update current essay context if provided
        if request.essay_context:
            current_essay_context.update(request.essay_context)
            await emit_debug_event("essay_context_updated", {
                "context": current_essay_context
            })
        
        # Clear debug state if requested
        if request.clear_history:
            debug_state.clear()
            debug_state.update({
                "chat_history": [],
                "memory_snapshots": [],
                "planner_calls": [],
                "tool_executions": [],
                "error_log": [],
                "agent_metrics": {},
                "network_requests": [],
                "live_events": []
            })
            await emit_debug_event("debug_state_cleared", {})
        
        # Add essay context to the message if available
        contextualized_message = await build_contextualized_message(
            request.message, 
            request.user_id, 
            current_essay_context
        )
        
        await emit_debug_event("message_contextualized", {
            "original": request.message,
            "contextualized": contextualized_message
        })
        
        # Use the unified state approach directly
        response = await process_message_with_unified_state(
            request.user_id,
            contextualized_message,
            current_essay_context
        )
        
        # Prepare debug data
        debug_data = {
            "chat_history": debug_state["chat_history"][-10:],  # Last 10 exchanges
            "current_memory": debug_state["memory_snapshots"][-1] if debug_state["memory_snapshots"] else {},
            "recent_tools": debug_state["tool_executions"][-5:],  # Last 5 tool calls
            "recent_errors": debug_state["error_log"][-5:],  # Last 5 errors
            "agent_metrics": {
                "approach": "unified_state",
                "timestamp": datetime.now().isoformat()
            },
            "live_events": debug_state["live_events"][-10:]  # Last 10 events
        }
        
        # Add chat exchange to debug state with context
        debug_state["chat_history"].append({
            "user": request.message,
            "agent": response,
            "timestamp": datetime.now().isoformat(),
            "essay_context": current_essay_context.copy() if current_essay_context else None
        })
        
        # Auto-save to essay-specific conversation file
        await save_essay_conversation_internal()
        
        await emit_debug_event("chat_response_complete", {
            "response_length": len(response),
            "debug_data_size": len(str(debug_data)),
            "approach": "unified_state"
        })
        
        return ChatResponse(response=response, debug_data=debug_data)
        
    except Exception as e:
        error_details = {
            "error": str(e),
            "traceback": traceback.format_exc(),
            "user_input": request.message
        }
        
        await emit_debug_event("chat_endpoint_error", error_details)
        logger.error(f"Chat endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Enhanced debug endpoints
@app.get("/debug/full-state")
async def get_full_debug_state():
    """Get complete debug state for detailed analysis."""
    await emit_debug_event("debug_state_requested", {
        "requestor": "api"
    })
    return debug_state

@app.get("/debug/live-events")
async def get_live_events(limit: int = 50):
    """Get recent live debug events."""
    events = debug_state["live_events"][-limit:]
    return {"events": events, "total_count": len(debug_state["live_events"])}

@app.get("/debug/errors")
async def get_recent_errors(limit: int = 20):
    """Get recent error details."""
    errors = debug_state["error_log"][-limit:]
    return {"errors": errors, "total_count": len(debug_state["error_log"])}

@app.get("/debug/tools/executions")
async def get_tool_executions(limit: int = 30):
    """Get recent tool execution details."""
    executions = debug_state["tool_executions"][-limit:]
    return {"executions": executions, "total_count": len(debug_state["tool_executions"])}

@app.get("/debug/memory/snapshots")
async def get_memory_snapshots(limit: int = 10):
    """Get recent memory snapshots."""
    snapshots = debug_state["memory_snapshots"][-limit:]
    return {"snapshots": snapshots, "total_count": len(debug_state["memory_snapshots"])}

@app.post("/debug/tools/manual")
async def manual_tool_execution(request: dict):
    """Manually execute a tool for testing."""
    try:
        # Extract tool_name and tool_args from request body
        tool_name = request.get("tool_name")
        tool_args = request.get("tool_args", {})
        
        if not tool_name:
            raise HTTPException(status_code=400, detail="tool_name is required")
        
        start_time = datetime.now()
        
        await emit_debug_event("manual_tool_execution_start", {
            "tool": tool_name,
            "args": tool_args
        })
        
        # Check if this is a unified state tool
        state_based_tools = ['smart_brainstorm', 'smart_outline', 'smart_polish', 'essay_chat']
        
        if tool_name in state_based_tools:
            # Use unified state approach
            from essay_agent.state_manager import EssayStateManager
            from essay_agent.tools.independent_tools import SmartBrainstormTool, SmartOutlineTool, SmartPolishTool, EssayChatTool
            
            # Map tool names to classes
            tool_classes = {
                'smart_brainstorm': SmartBrainstormTool,
                'smart_outline': SmartOutlineTool, 
                'smart_polish': SmartPolishTool,
                'essay_chat': EssayChatTool
            }
            
            # Get or create state for Alex Kim (default test user)
            user_id = tool_args.get('user_id', 'alex_kim')
            manager = EssayStateManager()
            state = manager.load_state(user_id, "current")
            
            if not state:
                # Create test state with provided args
                essay_prompt = tool_args.get('prompt', 'Tell me about a time you faced a challenge, setback, or failure. How did it affect you, and what did you learn from the experience?')
                college = tool_args.get('context', 'Stanford').replace(' Challenge Essay', '').replace(' Essay', '')
                
                state = manager.create_new_essay(
                    user_id=user_id,
                    essay_prompt=essay_prompt,
                    college=college,
                    word_limit=650
                )
            
            # Update state with any additional context from args
            if tool_args.get('selected_text'):
                state.selected_text = tool_args['selected_text']
            if tool_args.get('user_input'):
                state.last_user_input = tool_args['user_input']
            
            # Execute the tool with state
            tool_class = tool_classes[tool_name]
            tool = tool_class()
            result = tool._run(state)
            
            # Save updated state
            manager.save_state(state)
            
        else:
            # Use old approach for legacy tools
            from essay_agent.tools.smart_orchestrator import SmartOrchestrator
            orchestrator = SmartOrchestrator()
            result = await orchestrator.execute_tool(tool_name, tool_args)
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        execution_result = {
            "tool": tool_name,
            "args": tool_args,
            "result": result,
            "execution_time": execution_time,
            "success": True,
            "timestamp": start_time.isoformat(),
            "approach": "unified_state" if tool_name in state_based_tools else "legacy"
        }
        
        await emit_debug_event("manual_tool_execution_complete", execution_result)
        
        return execution_result
        
    except Exception as e:
        execution_time = (datetime.now() - start_time).total_seconds()
        
        execution_result = {
            "tool": tool_name,
            "args": tool_args,
            "error": str(e),
            "traceback": traceback.format_exc(),
            "execution_time": execution_time,
            "success": False,
            "timestamp": start_time.isoformat()
        }
        
        await emit_debug_event("manual_tool_execution_error", execution_result)
        
        raise HTTPException(status_code=500, detail=execution_result)

@app.post("/debug/memory/inspect")
async def inspect_memory_state(user_id: str = "debug_user"):
    """Inspect current memory state for a user."""
    try:
        from essay_agent.memory.smart_memory import SmartMemory
        memory = SmartMemory(user_id)
        
        memory_data = {
            "user_id": user_id,
            "profile_data": None,
            "recent_chat": [],
            "key_values": {
                "college": "Not set",
                "essay_prompt": "Not set", 
                "onboarding_completed": False
            }
        }
        
        # Safely load profile data
        try:
            profile_data = memory.load_user_profile()
            memory_data["profile_data"] = profile_data if profile_data else {}
        except Exception as e:
            memory_data["profile_data"] = {"error": f"Failed to load profile: {str(e)}"}
        
        # Safely get recent chat
        try:
            recent_chat = memory.get_recent_chat(k=10)
            memory_data["recent_chat"] = recent_chat if recent_chat else []
        except Exception as e:
            memory_data["recent_chat"] = [f"Failed to load chat: {str(e)}"]
        
        # Safely get key values
        try:
            memory_data["key_values"]["college"] = memory.get("college", "Not set")
        except Exception as e:
            memory_data["key_values"]["college"] = f"Error: {str(e)}"
            
        try:
            memory_data["key_values"]["essay_prompt"] = memory.get("essay_prompt", "Not set")
        except Exception as e:
            memory_data["key_values"]["essay_prompt"] = f"Error: {str(e)}"
            
        try:
            memory_data["key_values"]["onboarding_completed"] = memory.get("onboarding_completed", False)
        except Exception as e:
            memory_data["key_values"]["onboarding_completed"] = f"Error: {str(e)}"
        
        await emit_debug_event("memory_inspection", {
            "user_id": user_id,
            "memory_size": len(str(memory_data))
        })
        
        return memory_data
        
    except Exception as e:
        error_details = {
            "user_id": user_id,
            "error": str(e),
            "traceback": traceback.format_exc()
        }
        
        await emit_debug_event("memory_inspection_error", error_details)
        
        # Return a safe error response instead of raising
        return {
            "user_id": user_id,
            "error": f"Memory inspection failed: {str(e)}",
            "profile_data": None,
            "recent_chat": [],
            "key_values": {
                "college": "Error loading",
                "essay_prompt": "Error loading",
                "onboarding_completed": False
            }
        }

@app.post("/debug/clear")
async def clear_debug_state():
    """Clear all debug state."""
    global agent
    agent = None
    debug_state.clear()
    debug_state.update({
        "chat_history": [],
        "memory_snapshots": [],
        "planner_calls": [],
        "tool_executions": [],
        "error_log": [],
        "agent_metrics": {},
        "network_requests": [],
        "live_events": []
    })
    
    await emit_debug_event("debug_state_cleared_manual", {
        "timestamp": datetime.now().isoformat()
    })
    
    return {"status": "cleared"}

@app.get("/debug/agent/state")
async def get_agent_state():
    """Get current agent internal state."""
    global agent
    
    if agent is None:
        return {"agent": None, "status": "not_initialized"}
    
    try:
        agent_state = {
            "user_id": agent.user_id,
            "session_start": agent.session_start.isoformat(),
            "interaction_count": agent.interaction_count,
            "last_execution_tools": agent.last_execution_tools,
            "debug_session_id": agent.debug_session_id,
            "memory_status": "available" if hasattr(agent, 'memory') else "not_available"
        }
        
        if hasattr(agent, 'memory'):
            try:
                agent_state["memory_summary"] = {
                    "recent_chat_count": len(agent.memory.get_recent_chat(k=100)),
                    "college": agent.memory.get("college", "Not set"),
                    "essay_prompt_set": bool(agent.memory.get("essay_prompt")),
                    "onboarding_completed": agent.memory.get("onboarding_completed", False)
                }
            except Exception as e:
                agent_state["memory_error"] = str(e)
        
        await emit_debug_event("agent_state_inspection", {
            "user_id": agent.user_id,
            "interaction_count": agent.interaction_count
        })
        
        return {"agent": agent_state, "status": "active"}
        
    except Exception as e:
        await emit_debug_event("agent_state_inspection_error", {
            "error": str(e)
        })
        raise HTTPException(status_code=500, detail=f"Agent state inspection failed: {str(e)}")

@app.get("/debug/tools")
async def get_available_tools():
    """Get list of all available tools with their descriptions."""
    from essay_agent.tools import REGISTRY
    
    tools_info = {}
    for name, tool in REGISTRY.items():
        tools_info[name] = {
            "name": name,
            "description": getattr(tool, 'description', 'No description'),
            "timeout": getattr(tool, 'timeout', None)
        }
    
    return {"tools": tools_info, "count": len(tools_info)}

# ============= UNIFIED STATE-BASED CHAT ENDPOINT =============

@app.post("/chat/unified")
async def unified_chat(request: dict):
    """
    Unified chat endpoint that uses the EssayStateManager and state-based tools.
    
    This replaces the old tool calling approach with the new unified state system.
    """
    try:
        user_id = request.get("user_id", "alex_kim")
        message = request.get("message", "")
        
        # Emit debug event
        await emit_debug_event("unified_chat_start", {
            "user_id": user_id,
            "message": message
        })
        
        # Use the unified state approach
        from essay_agent.state_manager import cursor_sidebar_agent
        
        response = cursor_sidebar_agent(user_id, message)
        
        # Emit completion event
        await emit_debug_event("unified_chat_complete", {
            "user_id": user_id,
            "response_length": len(response.get("response", ""))
        })
        
        return {
            "success": True,
            "response": response.get("response", ""),
            "state_summary": response.get("state_summary", {}),
            "debug_info": {
                "approach": "unified_state",
                "tools_used": response.get("tools_used", []),
                "context_used": response.get("context_used", {})
            }
        }
        
    except Exception as e:
        await emit_debug_event("unified_chat_error", {
            "user_id": request.get("user_id", "unknown"),
            "error": str(e)
        })
        
        return {
            "success": False,
            "error": str(e),
            "debug_info": {
                "approach": "unified_state",
                "error_type": type(e).__name__
            }
        }

@app.post("/tools/unified/{tool_name}")
async def execute_unified_tool(tool_name: str, request: dict):
    """
    Execute tools using the unified state approach.
    
    This endpoint properly loads the EssayAgentState and calls tools with it.
    """
    try:
        user_id = request.get("user_id", "alex_kim")
        
        # Load the unified state
        from essay_agent.state_manager import EssayStateManager
        manager = EssayStateManager()
        state = manager.load_state(user_id, "current")
        
        if not state:
            return {
                "success": False,
                "error": f"No active essay session found for user {user_id}",
                "debug_info": {"missing_state": True}
            }
        
        # Get the tool from registry
        from essay_agent.tools import REGISTRY as TOOL_REGISTRY
        if tool_name not in TOOL_REGISTRY:
            return {
                "success": False,
                "error": f"Tool {tool_name} not found in registry",
                "debug_info": {"available_tools": list(TOOL_REGISTRY.keys())}
            }
        
        tool = TOOL_REGISTRY[tool_name]
        
        # Emit debug event
        await emit_debug_event("unified_tool_start", {
            "tool_name": tool_name,
            "user_id": user_id,
            "state_summary": state.get_context_summary()
        })
        
        # Execute tool with unified state
        start_time = datetime.now()
        result = tool._run(state)
        execution_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # Save updated state
        manager.save_state(state)
        
        # Emit completion event
        await emit_debug_event("unified_tool_complete", {
            "tool_name": tool_name,
            "user_id": user_id,
            "execution_time_ms": execution_time,
            "result_keys": list(result.keys()) if isinstance(result, dict) else []
        })
        
        return {
            "success": True,
            "result": result,
            "execution_time_ms": execution_time,
            "state_summary": state.get_context_summary(),
            "debug_info": {
                "approach": "unified_state",
                "tool_name": tool_name,
                "state_updated": True
            }
        }
        
    except Exception as e:
        await emit_debug_event("unified_tool_error", {
            "tool_name": tool_name,
            "user_id": request.get("user_id", "unknown"),
            "error": str(e)
        })
        
        return {
            "success": False,
            "error": str(e),
            "debug_info": {
                "approach": "unified_state",
                "tool_name": tool_name,
                "error_type": type(e).__name__
            }
        }

# ============= STATE INSPECTION ENDPOINTS =============

@app.get("/state/{user_id}")
async def get_user_state(user_id: str):
    """
    View complete essay state for debugging.
    
    Shows the full EssayAgentState for a user including:
    - Essay context (prompt, college, word limit)
    - User profile data
    - Chat history and tool calls
    - Current draft and outline
    - Suggestions and context
    """
    try:
        manager = EssayStateManager()
        state = manager.load_state(user_id, "current")
        
        if not state:
            return {
                "error": "No active essay found",
                "user_id": user_id,
                "available_actions": [
                    "POST /state/{user_id}/create - Create new essay session",
                    "GET /debug/users - View all users"
                ]
            }
        
        # Emit debug event
        await emit_debug_event("state_inspection", {
            "user_id": user_id,
            "session_id": state.session_id,
            "has_draft": state.has_draft(),
            "word_count": state.get_word_count()
        })
        
        return {
            "user_id": user_id,
            "session_id": state.session_id,
            "state_summary": state.get_context_summary(),
            "essay_context": {
                "prompt": state.essay_prompt,
                "college": state.college,
                "word_limit": state.word_limit,
                "current_word_count": state.get_word_count()
            },
            "user_profile": state.user_profile,
            "essay_content": {
                "current_draft": state.current_draft,
                "outline": state.outline,
                "brainstormed_ideas": state.brainstormed_ideas,
                "selected_story": state.selected_story
            },
            "interaction_data": {
                "chat_history": state.chat_history[-10:],  # Last 10 messages
                "tool_calls": state.tool_calls[-5:],       # Last 5 tool calls
                "suggestions": [s for s in state.suggestions if not s.get("completed", False)],
                "current_focus": state.current_focus,
                "selected_text": state.selected_text
            },
            "metadata": {
                "created_at": state.created_at.isoformat(),
                "updated_at": state.updated_at.isoformat(),
                "total_chat_messages": len(state.chat_history),
                "total_tool_calls": len(state.tool_calls),
                "total_versions": len(state.versions)
            }
        }
        
    except Exception as e:
        await emit_debug_event("state_inspection_error", {
            "user_id": user_id,
            "error": str(e)
        })
        raise HTTPException(status_code=500, detail=f"State inspection failed: {str(e)}")

@app.post("/state/{user_id}/update")
async def update_user_state(user_id: str, updates: dict):
    """
    Test state updates from cursor sidebar.
    
    Simulates cursor interactions like:
    - Text selection: {"selected_text": "paragraph to polish"}
    - Focus change: {"current_focus": "revising"}
    - Draft updates: {"current_draft": "new essay content"}
    """
    try:
        manager = EssayStateManager()
        state = manager.load_state(user_id, "current")
        
        if not state:
            return {"error": "No active essay found", "user_id": user_id}
        
        # Apply updates to state
        updates_applied = []
        if "selected_text" in updates:
            state.selected_text = updates["selected_text"]
            updates_applied.append("selected_text")
        
        if "current_focus" in updates:
            state.current_focus = updates["current_focus"]
            updates_applied.append("current_focus")
        
        if "current_draft" in updates:
            state.update_draft(updates["current_draft"], "Updated from frontend")
            updates_applied.append("current_draft")
        
        if "last_user_input" in updates:
            state.last_user_input = updates["last_user_input"]
            updates_applied.append("last_user_input")
        
        # Save updated state
        manager.save_state(state)
        
        # Emit debug event
        await emit_debug_event("state_updated", {
            "user_id": user_id,
            "updates_applied": updates_applied,
            "new_context": state.get_context_summary()
        })
        
        return {
            "success": True,
            "user_id": user_id,
            "updates_applied": updates_applied,
            "new_state_summary": state.get_context_summary(),
            "message": f"Applied {len(updates_applied)} updates to essay state"
        }
        
    except Exception as e:
        await emit_debug_event("state_update_error", {
            "user_id": user_id,
            "error": str(e)
        })
        raise HTTPException(status_code=500, detail=f"State update failed: {str(e)}")

@app.post("/state/{user_id}/create")
async def create_new_essay_session(user_id: str, essay_data: dict):
    """
    Create new essay session for testing.
    
    Required fields:
    - essay_prompt: str
    - college: str (optional)
    - word_limit: int (optional, default 650)
    """
    try:
        manager = EssayStateManager()
        
        # Extract essay data
        essay_prompt = essay_data.get("essay_prompt")
        if not essay_prompt:
            raise HTTPException(status_code=400, detail="essay_prompt is required")
        
        college = essay_data.get("college", "")
        word_limit = essay_data.get("word_limit", 650)
        
        # Create new essay session
        state = manager.create_new_essay(
            user_id=user_id,
            essay_prompt=essay_prompt,
            college=college,
            word_limit=word_limit
        )
        
        # Add user profile if provided
        if "user_profile" in essay_data:
            state.user_profile = essay_data["user_profile"]
            manager.save_state(state)
        
        # Emit debug event
        await emit_debug_event("new_essay_created", {
            "user_id": user_id,
            "session_id": state.session_id,
            "college": college,
            "prompt_length": len(essay_prompt)
        })
        
        return {
            "success": True,
            "user_id": user_id,
            "session_id": state.session_id,
            "essay_context": {
                "prompt": essay_prompt,
                "college": college,
                "word_limit": word_limit
            },
            "state_summary": state.get_context_summary(),
            "message": f"Created new essay session for {user_id}"
        }
        
    except Exception as e:
        await emit_debug_event("essay_creation_error", {
            "user_id": user_id,
            "error": str(e)
        })
        raise HTTPException(status_code=500, detail=f"Essay creation failed: {str(e)}")

@app.get("/debug/users")
async def list_all_users():
    """List all users with essay sessions."""
    try:
        manager = EssayStateManager()
        memory_store_path = manager.memory_store_path
        
        users = []
        for item in memory_store_path.iterdir():
            if item.is_file() and item.name.endswith('.json'):
                # Check if it's a state file
                try:
                    with open(item, 'r') as f:
                        data = json.load(f)
                    if 'user_id' in data and 'essay_prompt' in data:
                        users.append({
                            "user_id": data['user_id'],
                            "file": item.name,
                            "college": data.get('college', ''),
                            "word_count": len(data.get('current_draft', '').split()) if data.get('current_draft') else 0,
                            "updated_at": data.get('updated_at', ''),
                            "has_profile": bool(data.get('user_profile', {}))
                        })
                except:
                    continue
        
        return {
            "users": users,
            "count": len(users),
            "memory_store_path": str(memory_store_path)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"User listing failed: {str(e)}")

@app.get("/state/{user_id}/context")
async def get_cursor_context(user_id: str, selected_text: str = "", user_input: str = ""):
    """
    Get complete context for cursor sidebar agent.
    
    This endpoint simulates what the cursor sidebar would receive.
    """
    try:
        manager = EssayStateManager()
        context = manager.get_context_for_cursor(user_id, selected_text, user_input)
        
        # Emit debug event
        await emit_debug_event("cursor_context_request", {
            "user_id": user_id,
            "has_selected_text": bool(selected_text),
            "has_user_input": bool(user_input),
            "has_active_essay": context.get("has_active_essay", False)
        })
        
        return context
        
    except Exception as e:
        await emit_debug_event("cursor_context_error", {
            "user_id": user_id,
            "error": str(e)
        })
        raise HTTPException(status_code=500, detail=f"Context retrieval failed: {str(e)}")

@app.get("/debug/agent-state/{user_id}")
async def get_agent_state_debug(user_id: str):
    """Get complete EssayAgentState for debug visualization."""
    try:
        from essay_agent.state_manager import EssayStateManager
        
        manager = EssayStateManager()
        state = manager.load_state(user_id, "current")
        
        if not state:
            return {
                "has_state": False,
                "user_id": user_id,
                "message": "No active essay session found"
            }
        
        # Emit debug event
        await emit_debug_event("agent_state_debug_view", {
            "user_id": user_id,
            "state_id": state.session_id,
            "word_count": state.get_word_count()
        })
        
        return {
            "has_state": True,
            "user_id": user_id,
            "session_id": state.session_id,
            
            # Core essay context
            "essay_context": {
                "prompt": state.essay_prompt,
                "college": state.college,
                "word_limit": state.word_limit,
                "essay_type": state.essay_type,
                "current_word_count": state.get_word_count(),
                "word_percentage": round((state.get_word_count() / state.word_limit) * 100, 1) if state.word_limit > 0 else 0
            },
            
            # User profile (structured)  
            "user_profile": {
                "basic_info": state.user_profile.get("user_info", {}),
                "academic_profile": state.user_profile.get("academic_profile", {}),
                "core_values": state.user_profile.get("core_values", []),
                "defining_moments": state.user_profile.get("defining_moments", []),
                "profile_completeness": len(state.user_profile.keys()) if state.user_profile else 0
            },
            
            # Current context & focus
            "current_context": {
                "selected_text": state.selected_text,
                "current_focus": state.current_focus,
                "last_user_input": state.last_user_input,
                "primary_text": state.primary_text,
                "working_notes": state.working_notes,
                "content_types": list(state.content_library.keys()),
                "activities_done": [activity["action"] for activity in state.activity_log[-5:]] if state.activity_log else []
            },
            
            # Flexible content library
            "content_library": {
                category: {
                    "count": len(content) if isinstance(content, list) else 1,
                    "latest": content[-1] if isinstance(content, list) and content else content,
                    "total_items": len(content) if isinstance(content, list) else 1
                }
                for category, content in state.content_library.items()
            },
            
            # Activity timeline
            "activity_timeline": state.activity_log[-10:] if state.activity_log else [],
            
            # Quick summary for display
            "quick_summary": state.get_context_summary()
        }
        
    except Exception as e:
        await emit_debug_event("agent_state_debug_error", {
            "user_id": user_id,
            "error": str(e)
        })
        raise HTTPException(status_code=500, detail=f"Failed to get agent state: {str(e)}")

# Static files for CSS/JS
frontend_dir = Path(__file__).parent
if (frontend_dir / "static").exists():
    app.mount("/static", StaticFiles(directory=str(frontend_dir / "static")), name="static")

def start_server(host: str = "127.0.0.1", port: int = 8000, reload: bool = True):
    """Start the debug frontend server with automatic port detection."""
    # Try to find an available port if the default is taken
    try:
        actual_port = find_free_port(port, port + 20)
        if actual_port != port:
            logger.info(f"Port {port} is busy, using port {actual_port} instead")
            port = actual_port
    except OSError as e:
        logger.error(f"Could not find free port: {e}")
        raise
    
    print(f"🚀 Starting Essay Agent Debug Frontend at http://{host}:{port}")
    print("📊 Debug interface includes:")
    print("   • User selection from 5 evaluation profiles")
    print("   • Chat interface with real-time agent interaction")
    print("   • Memory state visualization")
    print("   • Planner decision tracking")
    print("   • Tool execution monitoring")
    print("   • Error logging and debugging")
    
    try:
        uvicorn.run(
            "essay_agent.frontend.server:app",
            host=host,
            port=port,
            reload=reload,
            log_level="info"
        )
    except OSError as e:
        if "Address already in use" in str(e):
            logger.error(f"Port {port} is still in use. Try a different port or kill existing processes.")
            # Try one more time with a different port
            backup_port = find_free_port(port + 1, port + 50)
            logger.info(f"Retrying with port {backup_port}")
            uvicorn.run(
                "essay_agent.frontend.server:app",
                host=host,
                port=backup_port,
                reload=reload,
                log_level="info"
            )
        else:
            raise

if __name__ == "__main__":
    start_server() 