"""Test fixtures for essay agent testing

This package provides standardized test data for comprehensive system testing.
"""

from .profiles import *
from .prompts import *
from .responses import *
from .scenarios import *

__all__ = [
    # User profiles
    'TEST_PROFILES',
    'create_test_profile',
    'get_profile_by_type',
    
    # Essay prompts
    'ESSAY_PROMPTS',
    'get_prompt_by_type',
    'get_prompt_by_college',
    
    # Expected responses
    'EXPECTED_RESPONSES',
    'get_expected_response',
    
    # Test scenarios
    'CONVERSATION_SCENARIOS',
    'get_test_scenario',
] 