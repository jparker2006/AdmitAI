#!/usr/bin/env python3
"""
Natural State Manager - Session Management for Cursor Sidebar
============================================================

Manages essay writing sessions with the new natural state approach.
Perfect for cursor sidebar - loads user's essay context instantly.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from essay_agent.models.natural_essay_state import EssayAgentState, create_new_essay_session
from essay_agent.memory.simple_memory import SimpleMemory


class NaturalStateManager:
    """
    Manages essay writing sessions with natural state approach.
    
    No workflow assumptions - just manages what users actually have:
    - Their essay text
    - Their conversation history  
    - Their profile
    - Current editor state
    """
    
    def __init__(self, memory_store_path: str = "memory_store"):
        self.memory_store_path = Path(memory_store_path)
        self.memory_store_path.mkdir(exist_ok=True)
        self.memory = SimpleMemory()
    
    def create_new_essay_session(
        self, 
        user_id: str,
        essay_prompt: str,
        college: str = "",
        word_limit: int = 650
    ) -> EssayAgentState:
        """Create a new essay writing session with natural state"""
        
        # Load user profile
        user_profile = self._load_user_profile(user_id)
        
        # Create new session using natural state
        state = create_new_essay_session(
            essay_prompt=essay_prompt,
            user_id=user_id,
            user_profile=user_profile,
            college=college,
            word_limit=word_limit
        )
        
        # Save initial session
        self.save_session(state)
        
        return state
    
    def load_session(self, user_id: str, session_id: str = None) -> Optional[EssayAgentState]:
        """Load an existing essay session"""
        
        try:
            if session_id:
                file_path = self.memory_store_path / f"{user_id}_{session_id}.session.json"
            else:
                # Load most recent session
                file_path = self._get_latest_session_file(user_id)
            
            if file_path and file_path.exists():
                with open(file_path, 'r') as f:
                    data = json.load(f)
                return EssayAgentState.from_dict(data)
            
            return None
            
        except Exception as e:
            print(f"❌ Error loading session: {e}")
            return None
    
    def save_session(self, state: EssayAgentState) -> bool:
        """Save essay session to disk"""
        
        try:
            file_path = self.memory_store_path / f"{state.user_id}_{state.session_id}.session.json"
            
            with open(file_path, 'w') as f:
                json.dump(state.to_dict(), f, indent=2, default=str)
            
            return True
            
        except Exception as e:
            print(f"❌ Error saving session: {e}")
            return False
    
    def update_essay_text(self, state: EssayAgentState, new_text: str) -> bool:
        """Update the essay text and save session"""
        state.update_essay_text(new_text)
        return self.save_session(state)
    
    def update_selected_text(self, state: EssayAgentState, selected_text: str, cursor_pos: int = 0) -> bool:
        """Update what user has selected/highlighted"""
        state.selected_text = selected_text
        state.cursor_position = cursor_pos
        return self.save_session(state)
    
    def add_conversation_message(self, state: EssayAgentState, role: str, content: str) -> bool:
        """Add message to conversation and save"""
        state.add_chat_message(role, content)
        return self.save_session(state)
    
    def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get list of all sessions for a user"""
        
        sessions = []
        pattern = f"{user_id}_*.session.json"
        
        for file_path in self.memory_store_path.glob(pattern):
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                
                sessions.append({
                    "session_id": data.get("session_id", ""),
                    "created_at": data.get("created_at", ""),
                    "essay_prompt": data.get("essay_prompt", "")[:100] + "...",
                    "college": data.get("college", ""),
                    "word_count": len(data.get("essay_text", "").split()) if data.get("essay_text") else 0
                })
                
            except Exception as e:
                print(f"⚠️ Error reading session file {file_path}: {e}")
                continue
        
        # Sort by creation date (newest first)
        sessions.sort(key=lambda x: x["created_at"], reverse=True)
        return sessions
    
    def _load_user_profile(self, user_id: str) -> Dict[str, Any]:
        """Load user profile from memory system"""
        
        try:
            profile_obj = self.memory.load(user_id)
            
            if profile_obj:
                if hasattr(profile_obj, 'model_dump'):
                    return profile_obj.model_dump()
                elif isinstance(profile_obj, dict):
                    return profile_obj
            
            print(f"⚠️ No profile found for user: {user_id}")
            return {}
            
        except Exception as e:
            print(f"❌ Error loading profile for {user_id}: {e}")
            return {}
    
    def _get_latest_session_file(self, user_id: str) -> Optional[Path]:
        """Get the most recently created session file for user"""
        
        pattern = f"{user_id}_*.session.json"
        session_files = list(self.memory_store_path.glob(pattern))
        
        if not session_files:
            return None
        
        # Sort by modification time (newest first)
        session_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        return session_files[0] 