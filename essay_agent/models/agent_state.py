#!/usr/bin/env python3
"""
Essay Agent State - Unified Context for All Tools
================================================

Single source of truth for an essay writing session that gets passed to all tools.
Contains everything: prompt, user context, documents, chat history, current state.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime
import json
import uuid


@dataclass
class EssayAgentState:
    """
    Unified state object that contains everything about an essay writing session.
    
    This gets passed to ALL tools instead of individual parameters.
    Tools can access whatever they need and update the state.
    """
    
    # ============= CORE ESSAY INFORMATION =============
    essay_prompt: str
    """The college essay prompt the user is working on"""
    
    college: str = ""
    """Target college (e.g., 'Stanford', 'Harvard')"""
    
    word_limit: int = 650
    """Target word count for the essay"""
    
    essay_type: str = "personal_statement"
    """Type of essay: 'personal_statement', 'supplemental', 'why_major', etc."""
    
    # ============= USER CONTEXT =============
    user_id: str = ""
    """Unique identifier for the user"""
    
    user_profile: Dict[str, Any] = field(default_factory=dict)
    """Complete user profile with background, interests, achievements, etc."""
    
    preferences: Dict[str, Any] = field(default_factory=dict)
    """User preferences for writing style, feedback level, etc."""
    
    # ============= ESSAY CONTENT & DOCUMENTS =============
    primary_text: str = ""
    """The main essay text the user is working on"""
    
    working_notes: str = ""
    """Scratch space for notes, ideas, fragments, outlines - anything"""
    
    content_library: Dict[str, Any] = field(default_factory=dict)
    """Flexible storage for any user-created content:
    - 'ideas': brainstormed concepts (if user wants)
    - 'outlines': structure experiments (if user wants)  
    - 'drafts': alternative versions (if user wants)
    - 'fragments': partial texts, quotes, research
    - 'feedback': notes and suggestions
    - anything else the user creates
    """
    
    # ============= DOCUMENT HISTORY =============
    versions: List[Dict[str, Any]] = field(default_factory=list)
    """History of changes with timestamps and descriptions"""
    
    activity_log: List[Dict[str, Any]] = field(default_factory=list)
    """What the user has done, without imposing workflow order"""
    
    feedback_history: List[Dict[str, Any]] = field(default_factory=list)
    """History of feedback and scores given to different versions"""
    
    # ============= CURRENT CONTEXT =============
    selected_text: str = ""
    """Currently selected/highlighted text in the editor"""
    
    cursor_position: int = 0
    """Current cursor position in the document"""
    
    last_user_input: str = ""
    """The user's most recent input/request"""
    
    current_focus: str = ""
    """What the user is currently working on: 'brainstorming', 'outlining', 'drafting', 'revising', 'polishing'"""
    
    # ============= CHAT & INTERACTION HISTORY =============
    chat_history: List[Dict[str, Any]] = field(default_factory=list)
    """Complete conversation history with the agent"""
    
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    """History of tool executions for this session"""
    
    suggestions: List[Dict[str, Any]] = field(default_factory=list)
    """Pending suggestions and next steps for the user"""
    
    # ============= SESSION METADATA =============
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    """Unique session identifier"""
    
    created_at: datetime = field(default_factory=datetime.now)
    """When this essay session was created"""
    
    updated_at: datetime = field(default_factory=datetime.now)
    """When this state was last modified"""
    
    # ============= HELPER METHODS =============
    
    def update_primary_text(self, new_text: str, change_description: str = "") -> None:
        """Update the main essay text and record the change in history"""
        if self.primary_text != new_text:
            # Save current version to history
            self.versions.append({
                "content": self.primary_text,
                "timestamp": datetime.now().isoformat(),
                "change_description": change_description,
                "word_count": len(self.primary_text.split()) if self.primary_text else 0
            })
            
            # Update primary text
            self.primary_text = new_text
            self.updated_at = datetime.now()
    
    def add_to_library(self, category: str, content: Any, description: str = "") -> None:
        """Add content to the flexible content library"""
        if category not in self.content_library:
            self.content_library[category] = []
        
        self.content_library[category].append({
            "content": content,
            "description": description,
            "timestamp": datetime.now().isoformat()
        })
        self.updated_at = datetime.now()
    
    def log_activity(self, action: str, details: Dict[str, Any] = None) -> None:
        """Record what the user did without imposing workflow order"""
        self.activity_log.append({
            "action": action,  # "brainstormed", "outlined", "drafted", "polished", "researched", etc.
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        })
        self.updated_at = datetime.now()
    
    def get_word_count(self) -> int:
        """Get current primary text word count"""
        return len(self.primary_text.split()) if self.primary_text else 0
    
    def has_content_type(self, content_type: str) -> bool:
        """Check if user has created content of a specific type"""
        return content_type in self.content_library and len(self.content_library[content_type]) > 0
    
    def has_text(self) -> bool:
        """Check if user has written any primary text"""
        return bool(self.primary_text.strip())
    
    def has_ideas(self) -> bool:
        """Check if user has brainstormed ideas"""
        return self.has_content_type("ideas")
    
    def has_outline(self) -> bool:
        """Check if user has created an outline"""
        return self.has_content_type("outlines")
    
    def has_draft(self) -> bool:
        """Check if user has a draft (either in primary_text or content_library)"""
        return self.has_text() or self.has_content_type("drafts")
    
    @property
    def brainstormed_ideas(self) -> List[Dict[str, Any]]:
        """Get brainstormed ideas (backward compatibility)"""
        if self.has_content_type("ideas"):
            return [item["content"] for item in self.content_library["ideas"]]
        return []
    
    def get_context_summary(self) -> Dict[str, Any]:
        """Get a summary of current context for tools"""
        return {
            "essay_prompt": self.essay_prompt,
            "college": self.college,
            "word_limit": self.word_limit,
            "current_word_count": self.get_word_count(),
            "has_text": self.has_text(),
            "content_types": list(self.content_library.keys()),
            "activities_done": [activity["action"] for activity in self.activity_log[-5:]],
            "selected_text": self.selected_text,
            "current_focus": self.current_focus,
            "last_user_input": self.last_user_input
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "essay_prompt": self.essay_prompt,
            "college": self.college,
            "word_limit": self.word_limit,
            "essay_type": self.essay_type,
            "user_id": self.user_id,
            "user_profile": self.user_profile,
            "preferences": self.preferences,
            "primary_text": self.primary_text,
            "working_notes": self.working_notes,
            "content_library": self.content_library,
            "activity_log": self.activity_log,
            "versions": self.versions,
            "feedback_history": self.feedback_history,
            "selected_text": self.selected_text,
            "cursor_position": self.cursor_position,
            "last_user_input": self.last_user_input,
            "current_focus": self.current_focus,
            "chat_history": self.chat_history,
            "tool_calls": self.tool_calls,
            "suggestions": self.suggestions,
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> EssayAgentState:
        """Create from dictionary"""
        # Handle datetime fields
        created_at = datetime.fromisoformat(data.get("created_at", datetime.now().isoformat()))
        updated_at = datetime.fromisoformat(data.get("updated_at", datetime.now().isoformat()))
        
        return cls(
            essay_prompt=data.get("essay_prompt", ""),
            college=data.get("college", ""),
            word_limit=data.get("word_limit", 650),
            essay_type=data.get("essay_type", "personal_statement"),
            user_id=data.get("user_id", ""),
            user_profile=data.get("user_profile", {}),
            preferences=data.get("preferences", {}),
            primary_text=data.get("primary_text", data.get("current_draft", "")),  # Backward compatibility
            working_notes=data.get("working_notes", ""),
            content_library=data.get("content_library", {}),
            activity_log=data.get("activity_log", []),
            versions=data.get("versions", []),
            feedback_history=data.get("feedback_history", []),
            selected_text=data.get("selected_text", ""),
            cursor_position=data.get("cursor_position", 0),
            last_user_input=data.get("last_user_input", ""),
            current_focus=data.get("current_focus", ""),
            chat_history=data.get("chat_history", []),
            tool_calls=data.get("tool_calls", []),
            suggestions=data.get("suggestions", []),
            session_id=data.get("session_id", str(uuid.uuid4())),
            created_at=created_at,
            updated_at=updated_at
        )
    
    def save_to_file(self, filepath: str) -> None:
        """Save state to JSON file"""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2, default=str)
    
    @classmethod
    def load_from_file(cls, filepath: str) -> EssayAgentState:
        """Load state from JSON file"""
        with open(filepath, 'r') as f:
            data = json.load(f)
        return cls.from_dict(data)

    def add_chat_message(self, role: str, content: str, tool_calls: List[str] = None) -> None:
        """Add a message to the chat history"""
        self.chat_history.append({
            "role": role,  # 'user' or 'assistant'
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "tool_calls": tool_calls or []
        })
        self.updated_at = datetime.now()
    
    def record_tool_call(self, tool_name: str, inputs: Dict[str, Any], outputs: Dict[str, Any]) -> None:
        """Record a tool execution"""
        self.tool_calls.append({
            "tool_name": tool_name,
            "inputs": inputs,
            "outputs": outputs,
            "timestamp": datetime.now().isoformat()
        })
        self.updated_at = datetime.now()
    
    def add_suggestion(self, title: str, description: str, action: str = "") -> None:
        """Add a suggestion for the user"""
        self.suggestions.append({
            "title": title,
            "description": description,
            "action": action,
            "timestamp": datetime.now().isoformat(),
            "completed": False
        })
        self.updated_at = datetime.now()
    
    def get_latest_feedback(self) -> Optional[Dict[str, Any]]:
        """Get the most recent feedback"""
        return self.feedback_history[-1] if self.feedback_history else None


def create_initial_state(
    essay_prompt: str,
    user_id: str,
    college: str = "",
    word_limit: int = 650,
    user_profile: Dict[str, Any] = None
) -> EssayAgentState:
    """Create a new essay session state"""
    return EssayAgentState(
        essay_prompt=essay_prompt,
        college=college,
        word_limit=word_limit,
        user_id=user_id,
        user_profile=user_profile or {},
        current_focus="brainstorming"
    ) 