"""Test scenarios for conversation flow testing

Combines profiles, prompts, and validation patterns into structured test cases.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from .profiles import TEST_PROFILES, get_profile_by_type
from .prompts import ESSAY_PROMPTS, get_prompt_by_id, PROMPT_SETS
from .responses import validate_tool_response, validate_conversation_response

@dataclass
class TestScenario:
    """A complete test scenario with profile, prompt, and validation"""
    id: str
    name: str
    description: str
    profile_type: str
    prompt_id: str
    test_type: str  # "happy_path", "error_recovery", "edge_case"
    conversation_flow: List[Dict[str, Any]]
    success_criteria: List[str]
    validation_functions: List[callable]
    expected_tools: List[str]
    max_execution_time: float = 60.0

    def get_profile(self) -> Dict[str, Any]:
        """Get the test profile for this scenario"""
        return get_profile_by_type(self.profile_type)
    
    def get_prompt(self) -> Dict[str, Any]:
        """Get the essay prompt for this scenario"""
        return get_prompt_by_id(self.prompt_id)

# Happy Path Test Scenarios (HP-001 to HP-005)
HAPPY_PATH_SCENARIOS = [
    TestScenario(
        id="HP-001",
        name="Complete Essay Workflow - STEM Achievement",
        description="Full brainstorm → outline → draft → revise → polish workflow with STEM achiever profile",
        profile_type="achiever_stem",
        prompt_id="stanford_learning",
        test_type="happy_path",
        conversation_flow=[
            {
                "user_input": "I want to brainstorm ideas for my Stanford essay about learning",
                "expected_tools": ["brainstorm"],
                "expected_patterns": ["Story Ideas Generated", "Which story"],
                "validation": "successful_brainstorm"
            },
            {
                "user_input": "I like the first story about robotics",
                "expected_tools": ["outline"],
                "expected_patterns": ["Essay Outline Created", "Ready to help you draft"],
                "validation": "successful_outline"
            },
            {
                "user_input": "Write the draft",
                "expected_tools": ["draft"],
                "expected_patterns": ["Essay Draft Completed", "words", "revise"],
                "validation": "successful_draft"
            },
            {
                "user_input": "Please revise to make it more compelling",
                "expected_tools": ["revise"],
                "expected_patterns": ["Essay Revised", "improved"],
                "validation": "successful_revise"
            },
            {
                "user_input": "Polish it for final submission",
                "expected_tools": ["polish"],
                "expected_patterns": ["Essay Polished", "ready for submission"],
                "validation": "successful_polish"
            }
        ],
        success_criteria=[
            "All 5 tools execute successfully",
            "Essay content displayed at each step",
            "Word count within target range",
            "Final essay contains learning themes"
        ],
        validation_functions=[
            lambda result: "final_draft" in result,
            lambda result: len(result.get("final_draft", "").split()) >= 200,
            lambda result: "learning" in result.get("final_draft", "").lower()
        ],
        expected_tools=["brainstorm", "outline", "draft", "revise", "polish"]
    ),

    TestScenario(
        id="HP-002",
        name="Single-Step Brainstorm Request",
        description="User requests only brainstorming with follow-up suggestions",
        profile_type="challenger_humanities",
        prompt_id="common_challenge",
        test_type="happy_path",
        conversation_flow=[
            {
                "user_input": "Help me brainstorm stories for my Common App challenge essay",
                "expected_tools": ["brainstorm"],
                "expected_patterns": ["Story Ideas Generated", "Which story interests you"],
                "validation": "successful_brainstorm"
            }
        ],
        success_criteria=[
            "Brainstorm tool executes successfully",
            "3-5 relevant stories generated",
            "Stories match challenge theme",
            "Next step suggestions provided"
        ],
        validation_functions=[
            lambda result: len(result.get("stories", [])) >= 3,
            lambda result: any("challenge" in story.get("themes", []) for story in result.get("stories", []))
        ],
        expected_tools=["brainstorm"]
    ),

    TestScenario(
        id="HP-003",
        name="Multi-College Essay Differentiation",
        description="Different essays for MIT vs Harvard show distinct approaches",
        profile_type="creative_passionate",
        prompt_id="mit_community",
        test_type="happy_path",
        conversation_flow=[
            {
                "user_input": "I want to write about my community art project for MIT",
                "expected_tools": ["brainstorm", "outline", "draft"],
                "expected_patterns": ["Essay Draft Completed"],
                "validation": "successful_draft"
            }
        ],
        success_criteria=[
            "Draft emphasizes technical/innovation aspects for MIT",
            "Community service theme prominent",
            "Word count matches MIT requirements (300 words)",
            "Essay shows problem-solving approach"
        ],
        validation_functions=[
            lambda result: len(result.get("draft", "").split()) <= 350,
            lambda result: "community" in result.get("draft", "").lower()
        ],
        expected_tools=["brainstorm", "outline", "draft"]
    ),

    TestScenario(
        id="HP-004",
        name="Identity Essay with Vulnerability",
        description="Identity-focused essay with authentic personal story",
        profile_type="identity_explorer",
        prompt_id="harvard_identity",
        test_type="happy_path",
        conversation_flow=[
            {
                "user_input": "I want to write about my mental health advocacy for Harvard's diversity prompt",
                "expected_tools": ["brainstorm", "outline", "draft"],
                "expected_patterns": ["Essay Draft Completed"],
                "validation": "successful_draft"
            }
        ],
        success_criteria=[
            "Essay shows personal growth and vulnerability",
            "Identity themes clearly present",
            "Authentic voice throughout",
            "Harvard word limit respected (650 words)"
        ],
        validation_functions=[
            lambda result: 600 <= len(result.get("draft", "").split()) <= 700,
            lambda result: any(word in result.get("draft", "").lower() for word in ["identity", "authentic", "diversity"])
        ],
        expected_tools=["brainstorm", "outline", "draft"]
    ),

    TestScenario(
        id="HP-005",
        name="Revision Cycle Improvement",
        description="Multiple revision cycles showing iterative improvement",
        profile_type="service_leader", 
        prompt_id="yale_passion",
        test_type="happy_path",
        conversation_flow=[
            {
                "user_input": "Write an essay about my homeless shelter work",
                "expected_tools": ["brainstorm", "outline", "draft"],
                "expected_patterns": ["Essay Draft Completed"],
                "validation": "successful_draft"
            },
            {
                "user_input": "Make it more personal and emotional",
                "expected_tools": ["revise"],
                "expected_patterns": ["Essay Revised"],
                "validation": "successful_revise"
            },
            {
                "user_input": "Revise again to emphasize the impact on my life",
                "expected_tools": ["revise"],
                "expected_patterns": ["Essay Revised"],
                "validation": "successful_revise"
            }
        ],
        success_criteria=[
            "Each revision improves the essay",
            "Personal voice strengthens with each iteration",
            "Version history maintained",
            "Final version shows clear improvement"
        ],
        validation_functions=[
            lambda result: "revised_draft" in result,
            lambda result: len(result.get("revised_draft", "")) > 100
        ],
        expected_tools=["brainstorm", "outline", "draft", "revise", "revise"]
    )
]

# Error Recovery Test Scenarios (ER-001 to ER-010)
ERROR_RECOVERY_SCENARIOS = [
    TestScenario(
        id="ER-001",
        name="Tool Timeout Recovery",
        description="Graceful handling of tool timeouts with retry options",
        profile_type="achiever_stem",
        prompt_id="stanford_learning",
        test_type="error_recovery",
        conversation_flow=[
            {
                "user_input": "Write my essay",
                "expected_tools": ["draft"],
                "simulation": "timeout_after_30s",
                "expected_patterns": ["timeout", "retry", "fallback"],
                "validation": "timeout_recovery"
            }
        ],
        success_criteria=[
            "Timeout detected and reported clearly",
            "Retry options offered to user",
            "Fallback response provided",
            "System remains responsive"
        ],
        validation_functions=[
            lambda result: "timeout" in str(result).lower() or "fallback" in str(result).lower()
        ],
        expected_tools=["draft"],
        max_execution_time=45.0
    ),

    TestScenario(
        id="ER-002",
        name="Invalid Parameters Recovery",
        description="Handling of invalid tool parameters with helpful suggestions",
        profile_type="challenger_humanities",
        prompt_id="common_challenge",
        test_type="error_recovery",
        conversation_flow=[
            {
                "user_input": "Write a 5000 word essay",
                "expected_tools": [],
                "expected_patterns": ["word limit", "suggestion", "valid range"],
                "validation": "parameter_error_recovery"
            }
        ],
        success_criteria=[
            "Invalid word count detected",
            "Clear error message provided",
            "Suggestions for valid parameters",
            "No system crash"
        ],
        validation_functions=[
            lambda result: "word" in str(result).lower() and "limit" in str(result).lower()
        ],
        expected_tools=[]
    ),

    TestScenario(
        id="ER-003",
        name="Corrupted Profile Recovery",
        description="Recovery from missing or corrupted user profile data",
        profile_type="corrupted_profile",
        prompt_id="stanford_learning", 
        test_type="error_recovery",
        conversation_flow=[
            {
                "user_input": "Help me write my essay",
                "expected_tools": [],
                "expected_patterns": ["profile", "information", "setup"],
                "validation": "profile_recovery"
            }
        ],
        success_criteria=[
            "Corrupted profile detected",
            "Profile reconstruction prompts",
            "System continues functioning",
            "User guided through setup"
        ],
        validation_functions=[
            lambda result: "profile" in str(result).lower() or "setup" in str(result).lower()
        ],
        expected_tools=[]
    )
]

# Edge Case Test Scenarios (EC-001 to EC-015)
EDGE_CASE_SCENARIOS = [
    TestScenario(
        id="EC-001",
        name="Empty User Input",
        description="Handling of empty or whitespace-only input",
        profile_type="achiever_stem",
        prompt_id="stanford_learning",
        test_type="edge_case", 
        conversation_flow=[
            {
                "user_input": "",
                "expected_tools": [],
                "expected_patterns": ["help", "what", "how can"],
                "validation": "empty_input_recovery"
            },
            {
                "user_input": "   ",
                "expected_tools": [],
                "expected_patterns": ["help", "what", "how can"],
                "validation": "empty_input_recovery"
            }
        ],
        success_criteria=[
            "Empty input handled gracefully",
            "Helpful prompts provided",
            "No system errors",
            "User guided to valid actions"
        ],
        validation_functions=[
            lambda result: len(str(result)) > 20,
            lambda result: "help" in str(result).lower() or "?" in str(result)
        ],
        expected_tools=[]
    ),

    TestScenario(
        id="EC-004", 
        name="Very Short Word Count",
        description="Essay generation with very short word limits",
        profile_type="creative_passionate",
        prompt_id="test_short",
        test_type="edge_case",
        conversation_flow=[
            {
                "user_input": "Write a 100-word essay about myself",
                "expected_tools": ["brainstorm", "outline", "draft"],
                "expected_patterns": ["Essay Draft Completed", "100", "concise"],
                "validation": "short_essay_success"
            }
        ],
        success_criteria=[
            "Essay respects 100-word limit",
            "Quality maintained despite brevity",
            "Appropriate structure for short format",
            "All essential elements present"
        ],
        validation_functions=[
            lambda result: 90 <= len(result.get("draft", "").split()) <= 110,
            lambda result: len(result.get("draft", "")) > 50
        ],
        expected_tools=["brainstorm", "outline", "draft"]
    ),

    TestScenario(
        id="EC-005",
        name="Very Long Word Count",
        description="Essay generation with very long word limits",
        profile_type="service_leader",
        prompt_id="test_long",
        test_type="edge_case",
        conversation_flow=[
            {
                "user_input": "Write a comprehensive 1000-word essay about my goals",
                "expected_tools": ["brainstorm", "outline", "draft"],
                "expected_patterns": ["Essay Draft Completed", "1000", "comprehensive"],
                "validation": "long_essay_success"
            }
        ],
        success_criteria=[
            "Essay approaches 1000-word target",
            "Comprehensive coverage of topics",
            "Maintains quality throughout",
            "Proper structure for long format"
        ],
        validation_functions=[
            lambda result: 900 <= len(result.get("draft", "").split()) <= 1100,
            lambda result: len(result.get("draft", "")) > 500
        ],
        expected_tools=["brainstorm", "outline", "draft"]
    )
]

# Comprehensive test scenario collections
CONVERSATION_SCENARIOS = {
    "happy_path": HAPPY_PATH_SCENARIOS,
    "error_recovery": ERROR_RECOVERY_SCENARIOS,
    "edge_cases": EDGE_CASE_SCENARIOS
}

# All scenarios for comprehensive testing
ALL_SCENARIOS = HAPPY_PATH_SCENARIOS + ERROR_RECOVERY_SCENARIOS + EDGE_CASE_SCENARIOS

def get_test_scenario(scenario_id: str) -> Optional[TestScenario]:
    """Get a specific test scenario by ID"""
    for scenario in ALL_SCENARIOS:
        if scenario.id == scenario_id:
            return scenario
    return None

def get_scenarios_by_type(scenario_type: str) -> List[TestScenario]:
    """Get all scenarios of a specific type"""
    return CONVERSATION_SCENARIOS.get(scenario_type, [])

def get_scenarios_by_profile(profile_type: str) -> List[TestScenario]:
    """Get all scenarios using a specific profile type"""
    return [s for s in ALL_SCENARIOS if s.profile_type == profile_type]

def get_scenarios_by_prompt(prompt_id: str) -> List[TestScenario]:
    """Get all scenarios using a specific prompt"""
    return [s for s in ALL_SCENARIOS if s.prompt_id == prompt_id]

# Test execution helpers
def validate_scenario_result(scenario: TestScenario, result: Dict[str, Any]) -> List[str]:
    """Validate a scenario result against its success criteria"""
    errors = []
    
    # Run scenario-specific validation functions
    for validator in scenario.validation_functions:
        try:
            if not validator(result):
                errors.append(f"Scenario validation failed for {scenario.id}")
        except Exception as e:
            errors.append(f"Scenario validation error: {str(e)}")
    
    return errors

def get_scenario_summary() -> Dict[str, int]:
    """Get a summary of available test scenarios"""
    return {
        "total_scenarios": len(ALL_SCENARIOS),
        "happy_path": len(HAPPY_PATH_SCENARIOS),
        "error_recovery": len(ERROR_RECOVERY_SCENARIOS),
        "edge_cases": len(EDGE_CASE_SCENARIOS),
        "profile_types": len(set(s.profile_type for s in ALL_SCENARIOS)),
        "prompt_types": len(set(s.prompt_id for s in ALL_SCENARIOS))
    } 