"""
Essay Agent Models Package
=========================

Contains data models and state management for the essay writing agent.
"""

from .agent_state import EssayAgentState, create_initial_state

__all__ = ['EssayAgentState', 'create_initial_state'] 