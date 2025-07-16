"""Clarification tool for ambiguous user requests.

This tool helps provide clarifying questions when user input is vague
or ambiguous, improving conversation flow and user experience.
"""
from typing import Any, Dict
from essay_agent.tools.base import ValidatedTool
from essay_agent.tools import register_tool


@register_tool("clarify")
class ClarifyTool(ValidatedTool):
    """Ask clarifying questions when user request is ambiguous.
    
    This tool analyzes user input and generates appropriate clarifying
    questions to better understand their needs and intent.
    """

    name: str = "clarify"
    description: str = "Ask clarifying questions when user request is ambiguous"
    timeout: float = 10.0

    def _run(
        self,
        *,
        user_input: str,
        context: str = "",
        **_: Any,
    ) -> Dict[str, Any]:
        """Generate clarifying questions for ambiguous requests.
        
        Args:
            user_input: The user's original input that needs clarification
            context: Additional context about the conversation
            
        Returns:
            Dict containing clarifying questions and suggestions
        """
        user_input = str(user_input).strip()
        context = str(context).strip()
        
        if not user_input:
            return {
                "clarifying_questions": [
                    "What specific aspect of essay writing would you like help with?",
                    "Are you looking to brainstorm ideas, improve structure, or polish your draft?"
                ],
                "suggestions": [
                    "Try asking: 'Help me brainstorm ideas for my identity essay'",
                    "Try asking: 'How can I make this paragraph more vivid?'",
                    "Try asking: 'What's a good way to structure my challenge essay?'"
                ]
            }
        
        # Analyze user input for common ambiguous patterns
        lower_input = user_input.lower()
        
        if any(word in lower_input for word in ['help', 'what', 'how']) and len(user_input.split()) < 5:
            # Very short help requests
            questions = [
                "What specific type of essay are you working on? (identity, challenge, passion, etc.)",
                "Are you looking to brainstorm new ideas or improve existing content?",
                "Do you have a draft already, or are you starting from scratch?"
            ]
            suggestions = [
                "Be more specific about what you need help with",
                "Mention the essay prompt or type you're working on",
                "Share any content you'd like me to review or improve"
            ]
            
        elif 'essay' in lower_input and not any(word in lower_input for word in ['prompt', 'draft', 'outline', 'brainstorm']):
            # Generic essay mention without specifics
            questions = [
                "Which college essay prompt are you working on?",
                "What stage are you at - brainstorming, outlining, drafting, or revising?",
                "What specific challenge are you facing with your essay?"
            ]
            suggestions = [
                "Share your essay prompt so I can give targeted advice",
                "Tell me what part of the writing process you need help with",
                "Show me a paragraph or section you'd like feedback on"
            ]
            
        elif any(word in lower_input for word in ['better', 'improve', 'fix']) and 'this' in lower_input:
            # Wants to improve something but didn't specify what
            questions = [
                "What specific text or paragraph would you like me to help improve?",
                "What aspect needs improvement - clarity, impact, structure, or style?",
                "Are you trying to make it more engaging, more personal, or better structured?"
            ]
            suggestions = [
                "Paste the specific text you want me to review",
                "Describe what feels wrong or weak about the current version",
                "Tell me your goal - what should the improved version accomplish?"
            ]
            
        elif any(word in lower_input for word in ['story', 'experience', 'moment']) and len(user_input.split()) < 8:
            # Mentions story/experience but vaguely
            questions = [
                "What specific story or experience do you want to write about?",
                "What lesson or insight did you gain from this experience?",
                "How does this story connect to the essay prompt you're addressing?"
            ]
            suggestions = [
                "Describe the key moment or turning point in your story",
                "Explain why this experience was meaningful to you",
                "Share the essay prompt so I can help you connect your story to it"
            ]
            
        else:
            # General clarification
            questions = [
                "Could you provide more details about what you're trying to accomplish?",
                "What specific aspect of this would you like me to focus on?",
                "Is there a particular challenge or goal you're working toward?"
            ]
            suggestions = [
                "Try being more specific about your request",
                "Include relevant context about your essay or situation",
                "Ask about one specific thing at a time for the best help"
            ]
        
        return {
            "clarifying_questions": questions,
            "suggestions": suggestions,
            "response": f"I'd love to help you with that! To give you the best assistance, could you help me understand your needs better? {questions[0]}"
        } 