#!/usr/bin/env python3
"""
Natural Essay State - Simple, User-Centric Context
=================================================

Reflects what users actually have, not what workflow they should follow.
Perfect for cursor sidebar experience where users work however they want.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime
import json


@dataclass
class EssayAgentState:
    """
    Simple state that reflects what the user actually has:
    - Their conversation with the AI
    - The text they've written
    - Basic context (prompt, college, profile)
    - What they currently have selected
    
    No workflows, no buckets - just natural usage.
    """
    
    # ============= BASIC ESSAY CONTEXT =============
    essay_prompt: str
    """The college essay prompt/question"""
    
    college: str = ""
    """Target college (optional)"""
    
    word_limit: int = 650
    """Target word count"""
    
    # ============= USER CONTEXT =============
    user_id: str = ""
    """User identifier"""
    
    user_profile: Dict[str, Any] = field(default_factory=dict)
    """User's background, activities, experiences, etc."""
    
    # ============= WHAT THE USER HAS WRITTEN =============
    essay_text: str = ""
    """Their actual essay text - the main document"""
    
    notes: str = ""
    """Any notes, scratch work, fragments they want to keep"""
    
    # ============= CURRENT EDITOR STATE =============
    selected_text: str = ""
    """Currently highlighted/selected text in the editor"""
    
    cursor_position: int = 0
    """Current cursor position"""
    
    # ============= CONVERSATION HISTORY =============
    chat_history: List[Dict[str, Any]] = field(default_factory=list)
    """Complete conversation with the AI - this contains everything:
    - What they've brainstormed about
    - What feedback they've gotten
    - What they've been working on
    - All context from natural conversation
    """
    
    # ============= SESSION INFO =============
    user_id: str = ""
    session_id: str = field(default_factory=lambda: f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    # ============= SIMPLE HELPER METHODS =============
    
    def add_chat_message(self, role: str, content: str) -> None:
        """Add a message to conversation history"""
        self.chat_history.append({
            "role": role,  # 'user' or 'assistant'
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        self.updated_at = datetime.now()
    
    def update_essay_text(self, new_text: str) -> None:
        """Update the main essay text"""
        self.essay_text = new_text
        self.updated_at = datetime.now()
    
    def get_word_count(self) -> int:
        """Get current word count"""
        return len(self.essay_text.split()) if self.essay_text else 0
    
    def get_recent_conversation(self, num_messages: int = 10) -> List[Dict[str, Any]]:
        """Get recent conversation for context"""
        return self.chat_history[-num_messages:] if self.chat_history else []
    
    def extract_context_from_conversation(self) -> Dict[str, Any]:
        """
        Extract what the user has been working on from their conversation.
        
        This is much more natural than hardcoded buckets - the AI can understand:
        - What stories they've talked about
        - What feedback they've received
        - What they're currently focused on
        - What help they need
        
        All from natural conversation rather than imposed workflow.
        """
        recent_messages = self.get_recent_conversation(20)
        
        # Look for patterns in conversation
        context = {
            "has_discussed_ideas": any("brainstorm" in msg["content"].lower() or "story" in msg["content"].lower() 
                                     for msg in recent_messages),
            "has_received_feedback": any("score" in msg["content"].lower() or "improve" in msg["content"].lower() 
                                        for msg in recent_messages),
            "recent_focus": self._extract_focus_from_conversation(recent_messages),
            "mentioned_activities": self._extract_mentioned_activities(recent_messages),
            "current_challenges": self._extract_challenges(recent_messages)
        }
        
        return context
    
    def _extract_focus_from_conversation(self, messages: List[Dict[str, Any]]) -> str:
        """What has the user been focusing on recently?"""
        if not messages:
            return "getting_started"
        
        recent_content = " ".join([msg["content"].lower() for msg in messages[-5:]])
        
        if "grammar" in recent_content or "fix" in recent_content:
            return "polishing"
        elif "improve" in recent_content or "better" in recent_content:
            return "improving"
        elif "outline" in recent_content or "structure" in recent_content:
            return "structuring"
        elif "draft" in recent_content or "write" in recent_content:
            return "drafting"
        elif "idea" in recent_content or "story" in recent_content or "brainstorm" in recent_content:
            return "brainstorming"
        else:
            return "general_discussion"
    
    def _extract_mentioned_activities(self, messages: List[Dict[str, Any]]) -> List[str]:
        """What activities/experiences has the user mentioned?"""
        activities = []
        all_content = " ".join([msg["content"] for msg in messages])
        
        # Look for common activity patterns
        activity_keywords = [
            "investment club", "tutoring business", "model un", "debate team",
            "volunteer", "internship", "job", "leadership", "captain", "president",
            "founder", "started", "created", "organized", "led"
        ]
        
        for keyword in activity_keywords:
            if keyword in all_content.lower():
                activities.append(keyword)
        
        return list(set(activities))  # Remove duplicates
    
    def _extract_challenges(self, messages: List[Dict[str, Any]]) -> List[str]:
        """What challenges or help has the user mentioned?"""
        challenges = []
        user_messages = [msg["content"] for msg in messages if msg["role"] == "user"]
        
        for content in user_messages:
            content_lower = content.lower()
            if "stuck" in content_lower or "help" in content_lower:
                challenges.append("feeling_stuck")
            if "don't know" in content_lower or "not sure" in content_lower:
                challenges.append("needs_direction")
            if "cliche" in content_lower or "generic" in content_lower:
                challenges.append("worried_about_uniqueness")
        
        return list(set(challenges))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for saving"""
        return {
            "essay_prompt": self.essay_prompt,
            "college": self.college,
            "word_limit": self.word_limit,
            "user_id": self.user_id,
            "user_profile": self.user_profile,
            "essay_text": self.essay_text,
            "notes": self.notes,
            "selected_text": self.selected_text,
            "cursor_position": self.cursor_position,
            "chat_history": self.chat_history,
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> EssayAgentState:
        """Create from dictionary"""
        return cls(
            essay_prompt=data.get("essay_prompt", ""),
            college=data.get("college", ""),
            word_limit=data.get("word_limit", 650),
            user_id=data.get("user_id", ""),
            user_profile=data.get("user_profile", {}),
            essay_text=data.get("essay_text", ""),
            notes=data.get("notes", ""),
            selected_text=data.get("selected_text", ""),
            cursor_position=data.get("cursor_position", 0),
            chat_history=data.get("chat_history", []),
            session_id=data.get("session_id", ""),
            created_at=datetime.fromisoformat(data.get("created_at", datetime.now().isoformat())),
            updated_at=datetime.fromisoformat(data.get("updated_at", datetime.now().isoformat()))
        )


def create_new_essay_session(
    essay_prompt: str,
    user_id: str,
    user_profile: Dict[str, Any],
    college: str = "",
    word_limit: int = 650
) -> EssayAgentState:
    """Create a new essay writing session"""
    state = EssayAgentState(
        essay_prompt=essay_prompt,
        college=college,
        word_limit=word_limit,
        user_id=user_id,
        user_profile=user_profile
    )
    
    # Add welcome message
    state.add_chat_message(
        "assistant",
        f"Started new essay session for {college or 'college'}! I'm here to help with your essay: \"{essay_prompt[:100]}...\""
    )
    
    return state 