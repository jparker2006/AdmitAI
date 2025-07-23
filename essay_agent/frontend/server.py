"""FastAPI server for essay agent debug frontend."""

import asyncio
import json
import logging
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from essay_agent.agent_autonomous import AutonomousEssayAgent
from essay_agent.memory.smart_memory import SmartMemory
from essay_agent.intelligence.context_engine import ContextEngine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global debug state
debug_state = {
    "chat_history": [],
    "memory_snapshots": [],
    "planner_calls": [],
    "tool_executions": [],
    "error_log": [],
    "agent_metrics": {}
}

app = FastAPI(title="Essay Agent Debug Frontend", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response models
class ChatRequest(BaseModel):
    message: str
    user_id: str = "debug_user"
    clear_history: bool = False

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
        
    async def handle_message(self, user_input: str) -> str:
        """Enhanced message handler with debug capture."""
        session_start = datetime.now()
        
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
            except Exception as e:
                turn_debug["errors"].append(f"Memory capture error: {str(e)}")
            
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
                
            return response
            
        except Exception as e:
            error_msg = f"Agent error: {str(e)}\n{traceback.format_exc()}"
            debug_state["error_log"].append({
                "timestamp": datetime.now().isoformat(),
                "error": error_msg,
                "user_input": user_input
            })
            return f"I encountered an error: {str(e)}"
    
    async def _handle_message_with_debug(self, user_input: str, turn_debug: Dict) -> str:
        """Handle message with debug information capture."""
        try:
            # Save user input immediately
            self.memory.add_message("user", user_input)
            
            # === OBSERVE with debug capture ===
            context = await self._observe(user_input)
            turn_debug["context_snapshot"] = self._sanitize_for_json(context)
            
            # === REASON with debug capture ===
            reasoning = await self._reason_with_debug(user_input, context, turn_debug)
            
            # === ACT with debug capture ===
            action_result = await self._act_with_debug(reasoning, user_input, turn_debug)
            
            # === RESPOND ===
            response = self._respond(action_result, user_input)
            
            # Save agent response
            self.memory.add_message("assistant", response)
            
            # Learning hook
            self.memory.learn({
                "user_input": user_input,
                "agent_response": response,
                "tool_result": action_result if isinstance(action_result, dict) else {},
            })
            
            # Enhanced response
            from essay_agent.agents.response_enhancer import ResponseEnhancer
            context_meta = {
                "college": self.memory.get("college", ""),
                "essay_prompt": self.memory.get("essay_prompt", ""),
            }
            politeness_level = int(os.getenv("ESSAY_AGENT_POLITENESS_LEVEL", "1"))
            enhanced = ResponseEnhancer.enhance(response, context=context_meta, politeness_level=politeness_level)
            
            return enhanced
            
        except Exception as e:
            turn_debug["errors"].append(f"Message handling error: {str(e)}")
            return f"I encountered an error: {str(e)}"
    
    async def _reason_with_debug(self, user_input: str, context: Dict, turn_debug: Dict) -> Dict:
        """Reasoning with debug capture."""
        try:
            # Capture planner prompt
            from essay_agent.planner_prompt import PlannerPrompt
            from essay_agent.tools import REGISTRY as _registry
            
            planner = PlannerPrompt(list(_registry.keys()))
            planner_ctx = {
                "last_tool": self.last_execution_tools[-1] if self.last_execution_tools else "none",
                "recent_chat": self.memory.get_recent_chat(k=3),
                "profile": {
                    "college": self.memory.get("college", ""),
                    "essay_prompt": self.memory.get("essay_prompt", ""),
                },
                "tool_stats": "",
                "failure_count": getattr(self, "_planner_failures", 0),
            }
            
            prompt_str = planner.build_prompt(user_input, planner_ctx)
            turn_debug["planner_prompt"] = prompt_str
            
            # Call the original reasoning
            reasoning = await super()._reason(user_input, context)
            
            # Capture the plan
            if reasoning.get("action") == "tool_plan":
                turn_debug["planner_response"] = reasoning.get("plan", [])
            
            return reasoning
            
        except Exception as e:
            turn_debug["errors"].append(f"Reasoning error: {str(e)}")
            return {"action": "conversation", "message": "Reasoning failed"}
    
    async def _act_with_debug(self, reasoning: Dict, user_input: str, turn_debug: Dict) -> Dict:
        """Action execution with debug capture."""
        try:
            if reasoning.get("action") == "tool_plan":
                plan_list = reasoning.get("plan", [])
                
                # Track each tool execution
                for i, step in enumerate(plan_list):
                    tool_debug = {
                        "step": i + 1,
                        "tool_name": step.get("tool"),
                        "tool_args": step.get("args", {}),
                        "start_time": datetime.now().isoformat(),
                        "success": False,
                        "result": None,
                        "error": None,
                        "execution_time": 0
                    }
                    
                    step_start = datetime.now()
                    try:
                        # Execute the orchestrator
                        orchestration_result = await self.orchestrator.execute_plan(
                            plan_list,
                            user_input=user_input,
                            context=self._latest_context or {},
                        )
                        
                        tool_debug["success"] = True
                        tool_debug["result"] = self._sanitize_for_json(orchestration_result)
                        
                    except Exception as e:
                        tool_debug["error"] = str(e)
                        turn_debug["errors"].append(f"Tool {step.get('tool')} failed: {str(e)}")
                    
                    tool_debug["execution_time"] = (datetime.now() - step_start).total_seconds()
                    turn_debug["tool_sequence"].append(tool_debug)
                
                # Return the orchestration result
                orchestration_result = await self.orchestrator.execute_plan(
                    plan_list,
                    user_input=user_input,
                    context=self._latest_context or {},
                )
                
                steps = orchestration_result.get("steps", [])
                if not steps:
                    return {"type": "conversation", "message": "No tools executed successfully"}
                
                self.last_execution_tools = [s["tool"] for s in steps]
                last_step = steps[-1]
                return {"type": "tool_result", "tool_name": last_step["tool"], "result": last_step["result"]}
            
            return await super()._act(reasoning, user_input)
            
        except Exception as e:
            turn_debug["errors"].append(f"Action error: {str(e)}")
            return {"type": "error", "message": str(e)}
    
    def _sanitize_for_json(self, obj: Any) -> Any:
        """Sanitize object for JSON serialization."""
        try:
            if isinstance(obj, dict):
                return {k: self._sanitize_for_json(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [self._sanitize_for_json(item) for item in obj]
            elif hasattr(obj, 'model_dump'):
                return obj.model_dump()
            elif hasattr(obj, '__dict__'):
                return str(obj)
            else:
                return obj
        except:
            return str(obj)

# Global agent instance
agent: Optional[DebugAgent] = None

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

@app.post("/api/setup", response_model=SetupResponse)
async def setup_session(request: SetupRequest):
    """Setup the essay writing session with prompt and school."""
    global agent
    
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
        
        # Save to agent memory
        agent.memory.save("essay_prompt", request.essay_prompt.strip())
        agent.memory.save("college", request.school.strip()) 
        agent.memory.save("onboarding_completed", True)
        
        # Add initial context to memory
        initial_context = f"User is working on an essay for {request.school}. Essay prompt: {request.essay_prompt.strip()}"
        agent.memory.add_message("system", initial_context)
        
        # Update debug state
        debug_state["memory_snapshots"].append({
            "essay_prompt": request.essay_prompt.strip(),
            "college": request.school.strip(),
            "onboarding_completed": True,
            "setup_timestamp": datetime.now().isoformat()
        })
        
        logger.info(f"Session setup completed for {request.school} essay")
        
        return SetupResponse(
            status="success",
            message=f"Essay session initialized for {request.school}. Ready to help with your essay!"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Setup endpoint error: {e}")
        raise HTTPException(status_code=500, detail=f"Setup failed: {str(e)}")

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Handle chat requests and return debug information."""
    global agent
    
    try:
        # Initialize or reset agent
        if agent is None or request.clear_history:
            agent = DebugAgent(request.user_id)
            if request.clear_history:
                debug_state.clear()
                debug_state.update({
                    "chat_history": [],
                    "memory_snapshots": [],
                    "planner_calls": [],
                    "tool_executions": [],
                    "error_log": [],
                    "agent_metrics": {}
                })
        
        # Process the message
        response = await agent.handle_message(request.message)
        
        # Prepare debug data
        debug_data = {
            "chat_history": debug_state["chat_history"][-10:],  # Last 10 exchanges
            "current_memory": debug_state["memory_snapshots"][-1] if debug_state["memory_snapshots"] else {},
            "recent_tools": debug_state["tool_executions"][-5:],  # Last 5 tool calls
            "recent_errors": debug_state["error_log"][-5:],  # Last 5 errors
            "agent_metrics": {
                "session_start": agent.session_start.isoformat(),
                "interaction_count": agent.interaction_count,
                "tools_used": list(set(agent.last_execution_tools)) if agent.last_execution_tools else []
            }
        }
        
        return ChatResponse(response=response, debug_data=debug_data)
        
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/debug/full-state")
async def get_full_debug_state():
    """Get complete debug state for detailed analysis."""
    return debug_state

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
        "agent_metrics": {}
    })
    return {"status": "cleared"}

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

# Static files for CSS/JS
frontend_dir = Path(__file__).parent
if (frontend_dir / "static").exists():
    app.mount("/static", StaticFiles(directory=str(frontend_dir / "static")), name="static")

def start_server(host: str = "127.0.0.1", port: int = 8000, reload: bool = True):
    """Start the debug frontend server."""
    print(f"🚀 Starting Essay Agent Debug Frontend at http://{host}:{port}")
    print("📊 Debug interface includes:")
    print("   • Chat interface with real-time agent interaction")
    print("   • Memory state visualization")
    print("   • Planner decision tracking")
    print("   • Tool execution monitoring")
    print("   • Error logging and debugging")
    
    uvicorn.run(
        "essay_agent.frontend.server:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )

if __name__ == "__main__":
    start_server() 