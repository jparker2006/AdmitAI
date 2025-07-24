#!/usr/bin/env python3
"""
Essay State Manager - Session Management for Cursor Sidebar
==========================================================

Manages essay writing sessions with unified state for natural conversation.
Handles loading, saving, and creating essay sessions.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from essay_agent.models.agent_state import EssayAgentState, create_initial_state
from essay_agent.memory.simple_memory import SimpleMemory
import uuid


class EssayStateManager:
    """
    Manages essay writing sessions with unified state.
    
    Perfect for cursor sidebar - loads user's essay context instantly.
    """
    
    def __init__(self, memory_store_path: str = "memory_store"):
        self.memory_store_path = Path(memory_store_path)
        self.memory_store_path.mkdir(exist_ok=True)
        self.memory = SimpleMemory()
    
    def create_new_essay(
        self, 
        user_id: str,
        essay_prompt: str,
        college: str = "",
        word_limit: int = 650
    ) -> EssayAgentState:
        """Create a new essay writing session"""
        
        # Load user profile from memory with better error handling
        user_profile = {}
        try:
            print(f"🔍 Loading profile for user: {user_id}")
            profile_obj = self.memory.load(user_id)
            print(f"📦 Profile object type: {type(profile_obj)}")
            
            if profile_obj:
                if hasattr(profile_obj, 'model_dump'):
                    user_profile = profile_obj.model_dump()
                    print(f"✅ Profile converted to dict: {user_profile.keys()}")
                elif isinstance(profile_obj, dict):
                    user_profile = profile_obj
                    print(f"✅ Profile already dict: {user_profile.keys()}")
                else:
                    print(f"⚠️ Unknown profile format: {type(profile_obj)}")
                    user_profile = {}
            else:
                print("⚠️ No profile object returned")
                
        except Exception as e:
            print(f"❌ Error loading profile: {e}")
            user_profile = {}
        
        # Create initial state
        state = create_initial_state(
            essay_prompt=essay_prompt,
            user_id=user_id,
            college=college,
            word_limit=word_limit,
            user_profile=user_profile
        )
        
        # Save initial state
        self.save_state(state)
        
        # Add welcome message
        state.add_chat_message(
            "assistant", 
            f"Started new essay session for {college or 'college'}! Let's brainstorm ideas for your prompt.",
            []
        )
        
        return state
    
    def load_state(self, user_id: str, essay_id: str = "current") -> Optional[EssayAgentState]:
        """Load an existing essay session"""
        
        state_file = self._get_state_file_path(user_id, essay_id)
        
        if not state_file.exists():
            return None
        
        try:
            state = EssayAgentState.load_from_file(str(state_file))
            
            # Refresh user profile from memory (in case it was updated)
            try:
                profile_obj = self.memory.load(user_id)
                if profile_obj and hasattr(profile_obj, 'model_dump'):
                    state.user_profile = profile_obj.model_dump()
            except:
                pass  # Continue if memory load fails
            
            return state
            
        except Exception as e:
            print(f"Error loading state: {e}")
            return None
    
    def save_state(self, state: EssayAgentState) -> None:
        """Save essay session state"""
        
        state_file = self._get_state_file_path(state.user_id, "current")
        
        try:
            # Update timestamp
            from datetime import datetime
            state.updated_at = datetime.now()
            
            # Save to file
            state.save_to_file(str(state_file))
            
            # Also save user profile to memory (in case it was updated)
            if state.user_profile:
                try:
                    # Use the SimpleMemory static methods
                    from essay_agent.memory.simple_memory import save_user_profile
                    save_user_profile(state.user_id, state.user_profile)
                except:
                    pass  # Continue if memory save fails
                
        except Exception as e:
            print(f"Error saving state: {e}")
    
    def list_user_essays(self, user_id: str) -> List[Dict[str, Any]]:
        """List all essays for a user"""
        
        user_dir = self.memory_store_path / f"{user_id}_essays"
        if not user_dir.exists():
            return []
        
        essays = []
        for state_file in user_dir.glob("*.json"):
            try:
                state = EssayAgentState.load_from_file(str(state_file))
                essays.append({
                    "essay_id": state_file.stem,
                    "session_id": state.session_id,
                    "essay_prompt": state.essay_prompt[:100] + "...",
                    "college": state.college,
                    "word_count": state.get_word_count(),
                    "created_at": state.created_at.isoformat(),
                    "updated_at": state.updated_at.isoformat(),
                    "has_draft": state.has_draft(),
                    "has_outline": state.has_outline()
                })
            except Exception:
                continue
        
        # Sort by most recent
        essays.sort(key=lambda x: x["updated_at"], reverse=True)
        return essays
    
    def archive_essay(self, user_id: str, essay_id: str = "current") -> bool:
        """Archive an essay (move to archived folder)"""
        
        current_file = self._get_state_file_path(user_id, essay_id)
        if not current_file.exists():
            return False
        
        # Create archived version with timestamp
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archived_file = self._get_state_file_path(user_id, f"archived_{timestamp}")
        
        try:
            current_file.rename(archived_file)
            return True
        except Exception:
            return False
    
    def get_context_for_cursor(self, user_id: str, selected_text: str = "", user_input: str = "") -> Dict[str, Any]:
        """
        Get complete context for cursor sidebar agent.
        
        This is the main entry point for cursor integration.
        """
        
        # Load current essay state
        state = self.load_state(user_id, "current")
        
        if not state:
            # No current essay - return minimal context
            user_profile = self.memory.load_user_profile(user_id) or {}
            return {
                "has_active_essay": False,
                "user_profile": user_profile,
                "suggested_action": "start_new_essay",
                "message": "No active essay found. Start a new essay to begin writing!"
            }
        
        # Update current context
        if selected_text:
            state.selected_text = selected_text
        if user_input:
            state.last_user_input = user_input
        
        # Save updated state
        self.save_state(state)
        
        return {
            "has_active_essay": True,
            "state": state,
            "context_summary": state.get_context_summary(),
            "recent_chat": state.chat_history[-5:] if state.chat_history else [],
            "suggestions": [s for s in state.suggestions if not s.get("completed", False)],
            "essay_status": self._get_essay_status(state)
        }
    
    def update_from_cursor(
        self, 
        user_id: str, 
        updates: Dict[str, Any]
    ) -> Optional[EssayAgentState]:
        """Update state from cursor sidebar (e.g., user edited the draft)"""
        
        state = self.load_state(user_id, "current")
        if not state:
            return None
        
        # Update draft if changed
        if "current_draft" in updates and updates["current_draft"] != state.current_draft:
            old_word_count = state.get_word_count()
            state.update_draft(updates["current_draft"], "Manual edit in cursor")
            new_word_count = state.get_word_count()
            
            # Add chat message about the change
            change_desc = f"Word count: {old_word_count} → {new_word_count}"
            state.add_chat_message("user", f"Edited draft in cursor. {change_desc}", [])
        
        # Update selected text
        if "selected_text" in updates:
            state.selected_text = updates["selected_text"]
        
        # Update focus
        if "current_focus" in updates:
            state.current_focus = updates["current_focus"]
        
        # Save updated state
        self.save_state(state)
        return state
    
    def _get_state_file_path(self, user_id: str, essay_id: str) -> Path:
        """Get the file path for a state file"""
        
        # Create user essay directory
        user_dir = self.memory_store_path / f"{user_id}_essays"
        user_dir.mkdir(exist_ok=True)
        
        return user_dir / f"{essay_id}.json"
    
    def _get_essay_status(self, state: EssayAgentState) -> Dict[str, Any]:
        """Get a summary of essay progress"""
        
        word_count = state.get_word_count()
        target_words = state.word_limit
        
        progress = {
            "stage": "planning",
            "completion": 0,
            "next_steps": [],
            "word_progress": f"{word_count}/{target_words}"
        }
        
        if state.has_ideas():
            progress["completion"] = max(progress["completion"], 20)
            progress["stage"] = "brainstormed"
        
        if state.has_outline():
            progress["completion"] = max(progress["completion"], 40)
            progress["stage"] = "outlined"
        
        if state.has_draft():
            progress["completion"] = max(progress["completion"], 60)
            progress["stage"] = "drafted"
            
            # Calculate completion based on word count
            word_completion = min(100, (word_count / target_words) * 100)
            progress["completion"] = max(progress["completion"], int(word_completion))
        
        # Add next steps
        if not state.has_ideas():
            progress["next_steps"].append("Brainstorm essay ideas")
        elif not state.has_outline():
            progress["next_steps"].append("Create essay outline")
        elif not state.has_draft():
            progress["next_steps"].append("Write first draft")
        elif word_count < target_words * 0.8:
            progress["next_steps"].append("Expand essay content")
        elif word_count > target_words * 1.1:
            progress["next_steps"].append("Trim essay length")
        else:
            progress["next_steps"].append("Polish and refine")
        
        return progress


# ============= CURSOR SIDEBAR INTEGRATION =============

def cursor_sidebar_agent(user_id: str, user_input: str, selected_text: str = "") -> Dict[str, Any]:
    """
    Main entry point for cursor sidebar agent.
    
    User types in cursor sidebar, this function:
    1. Loads their essay context
    2. Determines what they want to do
    3. Executes appropriate tools
    4. Returns natural response
    """
    
    manager = EssayStateManager()
    
    # Get full context
    context = manager.get_context_for_cursor(user_id, selected_text, user_input)
    
    if not context["has_active_essay"]:
        return {
            "response": "No active essay found. Start a new essay to begin writing!",
            "action": "start_new_essay",
            "context": context
        }
    
    state = context["state"]
    
    # Analyze user input and determine action
    user_input_lower = user_input.lower()
    
    if any(word in user_input_lower for word in ["new essay", "start essay", "begin"]):
        return _handle_new_essay_request(manager, user_input)
    elif any(word in user_input_lower for word in ["brainstorm", "ideas"]):
        return _handle_brainstorm_request(state, manager)
    elif any(word in user_input_lower for word in ["outline", "structure"]):
        return _handle_outline_request(state, manager)
    elif any(word in user_input_lower for word in ["polish", "improve", "fix"]):
        return _handle_polish_request(state, manager)
    elif any(word in user_input_lower for word in ["words", "count", "length"]):
        return _handle_word_count_request(state)
    elif any(word in user_input_lower for word in ["status", "progress", "how"]):
        return _handle_status_request(state, context)
    else:
        return _handle_general_request(state, user_input)


def _handle_brainstorm_request(state: EssayAgentState, manager: EssayStateManager) -> Dict[str, Any]:
    """Handle brainstorming requests"""
    
    # Actually call the smart_brainstorm tool
    try:
        from essay_agent.tools.independent_tools import SmartBrainstormTool
        
        tool = SmartBrainstormTool()
        result = tool._run(state)
        
        # Generate response based on the ideas
        ideas = result.get("ideas", [])
        if ideas:
            response = f"I've brainstormed {len(ideas)} personalized essay ideas for your {state.college} essay:\n\n"
            for i, idea in enumerate(ideas, 1):
                response += f"{i}. **{idea['title']}**: {idea['description']}\n\n"
            response += "Which idea resonates with you? I can help you develop it further!"
        else:
            response = f"Let me brainstorm ideas for your {state.college} essay based on your background!"
        
        # Update state (already done by the tool)
        manager.save_state(state)
        
        return {
            "response": response,
            "action": "brainstorm", 
            "ideas": ideas,
            "suggestions": ["Select an idea to develop", "Create an outline", "Explore a specific story"],
            "tools_used": ["smart_brainstorm"]
        }
        
    except Exception as e:
        # Fallback to simple response if tool fails
        response = f"Let me brainstorm ideas for your {state.college} essay!"
        
        if state.user_profile:
            profile_summary = _extract_key_profile_points(state.user_profile)
            response += f" I'll personalize ideas based on your background: {profile_summary}"
        
        # Update state
        state.add_chat_message("assistant", response, ["smart_brainstorm"])
        manager.save_state(state)
        
        return {
            "response": response,
            "action": "brainstorm",
            "suggestions": ["Review generated ideas", "Select favorite idea", "Develop chosen story"],
            "error": str(e)
        }


def _handle_word_count_request(state: EssayAgentState) -> Dict[str, Any]:
    """Handle word count requests"""
    
    current_count = state.get_word_count()
    target = state.word_limit
    
    if current_count == 0:
        response = f"Your essay is empty. Target: {target} words."
    elif current_count < target * 0.8:
        response = f"Current: {current_count}/{target} words. You need about {target - current_count} more words."
    elif current_count > target * 1.1:
        response = f"Current: {current_count}/{target} words. You're over by {current_count - target} words - consider trimming."
    else:
        response = f"Current: {current_count}/{target} words. Perfect length!"
    
    return {
        "response": response,
        "action": "word_count",
        "data": {"current": current_count, "target": target}
    }


def _extract_key_profile_points(profile: Dict[str, Any]) -> str:
    """Extract key points from user profile"""
    points = []
    if profile.get("extracurriculars"):
        points.append(f"activities in {', '.join(profile['extracurriculars'][:2])}")
    if profile.get("achievements"):
        points.append(f"achievements like {profile['achievements'][0]}")
    return "; ".join(points) if points else "your background"


# Example usage for cursor sidebar
if __name__ == "__main__":
    # Demo: User starts new essay
    manager = EssayStateManager()
    
    state = manager.create_new_essay(
        user_id="alex_kim",
        essay_prompt="Tell us about a time you were challenged by a perspective that differed from your own. How did you respond?",
        college="Stanford",
        word_limit=650
    )
    
    print("📝 New Essay Session Created!")
    print(f"Essay: {state.essay_prompt[:80]}...")
    print(f"College: {state.college}")
    print(f"User: {state.user_profile.get('name', 'Unknown')}")
    print()
    
    # Demo: Cursor sidebar interaction
    response = cursor_sidebar_agent("alex_kim", "help me brainstorm ideas")
    print("🤖 Agent Response:")
    print(response["response"]) 