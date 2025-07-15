"""Expected responses and validation patterns for testing

Defines expected outputs for different tools and conversation patterns.
"""

from typing import Dict, List, Any, Optional, Callable
import re

# Expected response patterns for different tools
EXPECTED_RESPONSES = {
    "brainstorm": {
        "structure": {
            "stories": {
                "type": "list",
                "min_items": 3,
                "max_items": 5,
                "item_structure": {
                    "title": {"type": "string", "min_length": 5},
                    "description": {"type": "string", "min_length": 20},
                    "themes": {"type": "list", "min_items": 1}
                }
            }
        },
        "validation_rules": [
            lambda result: len(result.get("stories", [])) >= 3,
            lambda result: all(len(story.get("title", "")) > 5 for story in result.get("stories", [])),
            lambda result: all(len(story.get("description", "")) > 20 for story in result.get("stories", []))
        ],
        "display_patterns": [
            r"Story Ideas Generated",
            r"\d+\. \*\*.*\*\*",  # Numbered stories with bold titles
            r"Which story interests you"
        ]
    },

    "outline": {
        "structure": {
            "outline": {
                "type": "dict_or_string",
                "required_sections": ["hook", "context", "conflict", "growth", "reflection"]
            }
        },
        "validation_rules": [
            lambda result: "outline" in result,
            lambda result: len(str(result.get("outline", ""))) > 50,
        ],
        "display_patterns": [
            r"Essay Outline Created",
            r"Ready to help you draft"
        ]
    },

    "draft": {
        "structure": {
            "draft": {
                "type": "string",
                "min_length": 100,
                "word_count_tolerance": 0.15  # 15% tolerance
            }
        },
        "validation_rules": [
            lambda result: "draft" in result,
            lambda result: len(result.get("draft", "").split()) > 50,
            lambda result: len(result.get("draft", "")) > 100
        ],
        "display_patterns": [
            r"Essay Draft Completed",
            r"\(\d+ words\)",
            r"Would you like me to revise"
        ]
    },

    "revise": {
        "structure": {
            "revised_draft": {
                "type": "string", 
                "min_length": 100
            }
        },
        "validation_rules": [
            lambda result: "revised_draft" in result,
            lambda result: len(result.get("revised_draft", "")) > 100
        ],
        "display_patterns": [
            r"Essay Revised",
            r"improved based on your feedback"
        ]
    },

    "polish": {
        "structure": {
            "final_draft": {
                "type": "string",
                "min_length": 100
            }
        },
        "validation_rules": [
            lambda result: "final_draft" in result,
            lambda result: len(result.get("final_draft", "")) > 100
        ],
        "display_patterns": [
            r"Essay Polished",
            r"ready for submission"
        ]
    }
}

# Conversation flow expectations
CONVERSATION_PATTERNS = {
    "successful_brainstorm": {
        "user_input_patterns": [
            "brainstorm",
            "ideas",
            "stories",
            "help me think"
        ],
        "expected_agent_behavior": [
            "recognizes brainstorm intent",
            "executes brainstorm tool",
            "displays story ideas",
            "asks for user selection"
        ],
        "response_validation": [
            lambda resp: "Story Ideas" in resp,
            lambda resp: "Which story" in resp,
            lambda resp: len(re.findall(r"\d+\.", resp)) >= 3
        ]
    },

    "successful_draft": {
        "user_input_patterns": [
            "write a draft",
            "create essay", 
            "draft this",
            "write my essay"
        ],
        "expected_agent_behavior": [
            "recognizes draft intent",
            "executes draft tool",
            "displays word count",
            "offers revision options"
        ],
        "response_validation": [
            lambda resp: "Draft Completed" in resp,
            lambda resp: "words" in resp,
            lambda resp: "revise" in resp.lower()
        ]
    },

    "error_recovery": {
        "user_input_patterns": [
            "",
            "???",
            "invalid request"
        ],
        "expected_agent_behavior": [
            "provides helpful guidance",
            "asks clarifying questions",
            "suggests valid actions"
        ],
        "response_validation": [
            lambda resp: len(resp) > 20,
            lambda resp: "?" in resp or "help" in resp.lower()
        ]
    }
}

# Quality validation patterns
QUALITY_EXPECTATIONS = {
    "word_count_accuracy": {
        "target_tolerance": 0.10,  # 10% tolerance for word count
        "validation": lambda target, actual: abs(actual - target) / target <= 0.10
    },

    "keyword_coverage": {
        "minimum_coverage": 0.3,  # 30% of prompt keywords should appear
        "validation": lambda keywords, text: sum(1 for kw in keywords if kw.lower() in text.lower()) / len(keywords) >= 0.3
    },

    "response_time": {
        "tool_execution": {
            "brainstorm": 15.0,  # seconds
            "outline": 10.0,
            "draft": 45.0,
            "revise": 30.0,
            "polish": 30.0
        },
        "conversation_response": 5.0
    },

    "structural_integrity": {
        "essay_structure": [
            "introduction/hook",
            "body content", 
            "conclusion/reflection"
        ],
        "paragraph_count": {"min": 3, "max": 8},
        "sentence_variety": True
    }
}

# Mock LLM responses for testing
MOCK_LLM_RESPONSES = {
    "brainstorm_response": {
        "stories": [
            {
                "title": "Leading Robotics Team to Victory",
                "description": "Overcame technical setbacks and team conflicts to win regional championship",
                "themes": ["leadership", "perseverance", "teamwork"]
            },
            {
                "title": "Teaching Math to Struggling Students", 
                "description": "Developed innovative tutoring methods that helped students improve grades",
                "themes": ["teaching", "innovation", "impact"]
            },
            {
                "title": "Building Community Garden",
                "description": "Organized neighborhood project that brought together diverse community",
                "themes": ["community", "leadership", "environmental"]
            }
        ]
    },

    "outline_response": {
        "outline": {
            "hook": "The moment I realized our robot would never work...",
            "context": "Leading the robotics team through a challenging season",
            "conflict": "Technical failures and team disagreements threatened our chances",
            "growth": "Learning to adapt strategy and unite the team", 
            "reflection": "True leadership means turning obstacles into opportunities"
        }
    },

    "draft_response": {
        "draft": "The whirring sound of motors and clicking of keyboards filled our workspace as my robotics team frantically prepared for the regional championship. As team captain, I watched our months of work potentially crumble when our main drive system failed just days before competition. The frustration was palpable – some teammates wanted to give up, others blamed each other for the setbacks. In that moment, I realized that technical skills alone wouldn't lead us to victory; we needed unity and creative problem-solving. I called an emergency team meeting and proposed we completely redesign our approach, focusing on our strengths rather than trying to fix our weaknesses. Through collaborative brainstorming and late-night work sessions, we developed an innovative solution that not only worked but exceeded our original design. When we won the regional championship, it wasn't just because of our robot – it was because we had learned to work together, adapt under pressure, and turn obstacles into opportunities. This experience taught me that true leadership isn't about having all the answers, but about bringing out the best in others and staying resilient when faced with challenges."
    }
}

def get_expected_response(tool_name: str) -> Optional[Dict[str, Any]]:
    """Get expected response pattern for a tool"""
    return EXPECTED_RESPONSES.get(tool_name)

def validate_tool_response(tool_name: str, result: Dict[str, Any]) -> List[str]:
    """Validate a tool response against expected patterns"""
    errors = []
    expectations = get_expected_response(tool_name)
    
    if not expectations:
        return ["Unknown tool type for validation"]
    
    # Run validation rules
    for rule in expectations.get("validation_rules", []):
        try:
            if not rule(result):
                errors.append(f"Validation rule failed for {tool_name}")
        except Exception as e:
            errors.append(f"Validation error: {str(e)}")
    
    return errors

def validate_conversation_response(pattern_name: str, response: str) -> List[str]:
    """Validate a conversation response against expected patterns"""
    errors = []
    pattern = CONVERSATION_PATTERNS.get(pattern_name)
    
    if not pattern:
        return ["Unknown conversation pattern"]
    
    # Run response validation
    for validator in pattern.get("response_validation", []):
        try:
            if not validator(response):
                errors.append(f"Response validation failed for {pattern_name}")
        except Exception as e:
            errors.append(f"Response validation error: {str(e)}")
    
    return errors

def validate_display_format(tool_name: str, display_text: str) -> List[str]:
    """Validate that tool results are displayed correctly"""
    errors = []
    expectations = get_expected_response(tool_name)
    
    if not expectations:
        return ["Unknown tool for display validation"]
    
    # Check display patterns
    for pattern in expectations.get("display_patterns", []):
        if not re.search(pattern, display_text, re.IGNORECASE):
            errors.append(f"Missing display pattern: {pattern}")
    
    return errors

# Helper functions for test setup
def create_mock_tool_result(tool_name: str, success: bool = True) -> Dict[str, Any]:
    """Create a mock tool result for testing"""
    if not success:
        return {
            "ok": None,
            "error": f"Mock {tool_name} tool failure"
        }
    
    mock_response = MOCK_LLM_RESPONSES.get(f"{tool_name}_response", {})
    return {
        "ok": mock_response,
        "error": None
    }

def get_word_count_target(prompt_id: str) -> int:
    """Get expected word count for a prompt"""
    from .prompts import get_prompt_by_id
    prompt = get_prompt_by_id(prompt_id)
    return prompt["word_limit"] if prompt else 650 