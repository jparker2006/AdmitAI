"""essay_agent.tools.echo

Enhanced Echo tool with conversational feedback and progress tracking support.

The tool returns the provided message wrapped in a dict with additional
conversational context and progress information.
"""

from __future__ import annotations

from typing import Any, Dict, List
from datetime import datetime

# Note: use project ValidatedTool base for unified timeout & error handling
from essay_agent.tools.base import ValidatedTool
from essay_agent.tools import register_tool


@register_tool("echo")
class EchoTool(ValidatedTool):
    """Enhanced echo tool with conversational feedback.

    Returns the provided message with conversational context and progress
    information, making it useful for testing the conversational system
    and providing user feedback during tool execution.
    """

    name: str = "echo"
    description: str = (
        "Enhanced echo tool that returns messages with conversational context "
        "and progress tracking. Useful for testing conversational workflows."
    )

    # We return the value directly so LangChain does not attempt additional parsing
    return_direct: bool = True

    # ------------------------------------------------------------------
    # LangChain sync execution
    # ------------------------------------------------------------------
    def _run(self, message: str = "Hello, Essay Agent!", 
             conversational_context: Dict[str, Any] = None,
             progress_callback: Any = None,
             **kwargs: Any) -> Dict[str, Any]:
        """Enhanced synchronous run method with conversational support.

        Args:
            message: The text to echo back. If empty or whitespace only, a
                ValueError is raised.
            conversational_context: Optional context from conversation system
            progress_callback: Optional callback for progress updates
            **kwargs: Additional parameters for extensibility
        Returns:
            dict: Enhanced response with conversational context
        """
        message = str(message).strip()
        if not message:
            raise ValueError("Message must not be empty.")
        
        # Simulate progress tracking
        if progress_callback:
            progress_callback("Starting echo processing...")
        
        # Build enhanced response
        response = {
            "echo": message,
            "timestamp": datetime.now().isoformat(),
            "conversational_response": self._generate_conversational_response(message),
            "context": conversational_context or {},
            "tool_metadata": {
                "name": self.name,
                "description": self.description,
                "execution_time": 0.1,  # Simulated execution time
                "status": "success"
            }
        }
        
        # Add progress completion
        if progress_callback:
            progress_callback("Echo processing completed successfully")
        
        return response
    
    def _generate_conversational_response(self, message: str) -> str:
        """Generate a conversational response to the echoed message"""
        message_lower = message.lower()
        
        # Provide contextual responses based on message content
        if "hello" in message_lower or "hi" in message_lower:
            return "Hello! I'm here to help you with your essay writing. What would you like to work on?"
        elif "help" in message_lower:
            return "I can help you brainstorm ideas, create outlines, write drafts, revise content, and polish your essays. What specific help do you need?"
        elif "brainstorm" in message_lower:
            return "Great! I can help you brainstorm story ideas for your essay. What type of essay are you working on?"
        elif "outline" in message_lower:
            return "I can help you create a structured outline for your essay. Do you have a story or theme in mind?"
        elif "draft" in message_lower:
            return "I can help you write a compelling essay draft. Do you have an outline or specific ideas to start with?"
        elif "revise" in message_lower:
            return "I can help you revise your essay to make it stronger and more impactful. What areas would you like to improve?"
        elif "polish" in message_lower:
            return "I can help you polish your essay for final submission, including grammar, style, and length. Is your essay ready for final review?"
        elif "test" in message_lower:
            return "Echo tool is working perfectly! The conversational system is ready to help you with your essays."
        else:
            return f"I hear you saying: '{message}'. How can I help you with your essay writing today?"

    # ------------------------------------------------------------------
    # LangChain async execution
    # ------------------------------------------------------------------
    async def _arun(self, message: str = "Hello, Essay Agent!", 
                    conversational_context: Dict[str, Any] = None,
                    progress_callback: Any = None,
                    **kwargs: Any) -> Dict[str, Any]:
        """Enhanced async execution with conversational support."""
        # For now, delegate to sync version
        # TODO: Implement proper async execution in future
        return self._run(message, conversational_context, progress_callback, **kwargs)

    # ------------------------------------------------------------------
    # Enhanced call signatures for conversational system
    # ------------------------------------------------------------------
    def __call__(self, *args: Any, **kwargs: Any):  # type: ignore[override]
        """Enhanced invoke method with conversational support.

        Supports multiple invocation styles:
        1. ``tool()`` – uses the default greeting
        2. ``tool(message="Hi")`` – explicit keyword
        3. ``tool("Hi")`` – standard BaseTool interface
        4. ``tool(message="Hi", conversational_context={...})`` – with context
        """

        # Handle conversational context
        conversational_context = kwargs.pop("conversational_context", None)
        progress_callback = kwargs.pop("progress_callback", None)
        
        # Allow explicit "message" keyword
        if "message" in kwargs:
            if args:
                raise ValueError("Provide either positional 'tool_input' or 'message', not both.")
            return self._run(
                kwargs.pop("message"), 
                conversational_context=conversational_context,
                progress_callback=progress_callback,
                **kwargs
            )

        # No input provided – fall back to default
        if not args and not kwargs:
            return self._run(
                "Hello, Essay Agent!",
                conversational_context=conversational_context,
                progress_callback=progress_callback
            )

        # Handle positional arguments
        if args:
            return self._run(
                args[0],
                conversational_context=conversational_context,
                progress_callback=progress_callback,
                **kwargs
            )

        # Delegate to BaseTool's implementation
        return super().__call__(*args, **kwargs)
    
    def get_conversational_help(self) -> str:
        """Get help text for conversational interface"""
        return """Echo Tool Help:
        
The echo tool repeats your message back with conversational context. 
It's useful for testing the conversational system and understanding 
how messages flow through the essay writing workflow.

Examples:
• "Hello" - Get a greeting and introduction
• "Help me brainstorm" - Get guidance on brainstorming
• "Test the system" - Verify the conversational system is working

The echo tool provides contextual responses based on your message 
content and can help you understand how to interact with the essay 
writing system naturally.
"""

    def supports_conversational_mode(self) -> bool:
        """Indicate that this tool supports conversational mode"""
        return True 