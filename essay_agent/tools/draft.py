"""essay_agent.tools.draft

LangChain-compatible DraftTool: expands a structured outline into a complete
first-person draft while preserving the user's voice profile.

Enhanced with external word count validation and intelligent retry logic.
"""

from __future__ import annotations

import json
from typing import Any, Dict, Union

from langchain.llms.fake import FakeListLLM

from essay_agent.tools import register_tool
from essay_agent.tools.base import ValidatedTool
from essay_agent.tools.word_count import WordCountTool
from essay_agent.llm_client import get_chat_llm, truncate_context
from essay_agent.prompts.draft import DRAFT_PROMPT, EXPANSION_PROMPT, TRIMMING_PROMPT
from essay_agent.prompts.templates import render_template
from essay_agent.response_parser import safe_parse, schema_parser

# JSON schema used for validating the main LLM response -----------------------
_SCHEMA = {
    "type": "object",
    "properties": {
        "draft": {"type": "string"},
    },
    "required": ["draft"],
}

# JSON schema for expansion responses ------------------------------------------
_EXPANSION_SCHEMA = {
    "type": "object",
    "properties": {
        "expanded_draft": {"type": "string"},
    },
    "required": ["expanded_draft"],
}

# JSON schema for trimming responses -------------------------------------------
_TRIMMING_SCHEMA = {
    "type": "object",
    "properties": {
        "trimmed_draft": {"type": "string"},
    },
    "required": ["trimmed_draft"],
}


@register_tool("draft")
class DraftTool(ValidatedTool):
    """Generate a full essay draft from an outline with word count enforcement.

    The tool renders a high-stakes prompt, calls GPT-4 (or a fake LLM during
    offline/CI runs), parses the JSON output, and performs word count validation
    with intelligent retry logic for expansion/trimming.
    """

    name: str = "draft"
    description: str = (
        "Expand an outline into a complete first-person draft while preserving the user's voice."
    )

    # Drafting can take longer than quick tools
    timeout: float = 45.0  # drafting full essays requires substantial time

    def __init__(self):
        super().__init__()
        # Initialize word count tool as a private attribute
        object.__setattr__(self, '_word_count_tool', WordCountTool())
    
    @property
    def word_count_tool(self) -> WordCountTool:
        """Get the word count tool instance."""
        return getattr(self, '_word_count_tool', WordCountTool())

    def _handle_timeout_fallback(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """Provide fallback draft structure when drafting times out."""
        word_count = kwargs.get("word_count", 650)
        fallback_draft = f"""[DRAFT TIMEOUT FALLBACK - {word_count} words]

This essay draft could not be generated due to a timeout error. To resolve this issue:

1. Try reducing the complexity of your outline
2. Ensure your internet connection is stable  
3. Consider breaking the draft into smaller sections
4. Increase the timeout setting if timeouts persist

Your outline structure was preserved and can be used to manually craft your essay or retry with adjusted parameters.

Word count target: {word_count} words
Timeout occurred during: Essay drafting phase
Suggested next step: Retry with simplified outline or manual drafting

[Please retry the draft tool with adjusted parameters]"""
        
        return {
            "ok": {"draft": fallback_draft, "word_count": len(fallback_draft.split())},
            "error": f"Draft tool timed out after {self.timeout}s - using fallback structure"
        }

    # ------------------------------------------------------------------
    # LangChain sync execution
    # ------------------------------------------------------------------
    def _run(
        self,
        *,
        outline: Union[Dict[str, Any], str],
        voice_profile: str,
        word_count: int = 650,
        **_: Any,
    ) -> Dict[str, str]:  # type: ignore[override]
        """Generate a full essay draft from an outline with word count enforcement."""
        from essay_agent.tools.errors import ToolError
        import json
        
        # ----------------------- Input validation -----------------------
        # Check if outline is a failed tool result
        if isinstance(outline, dict) and "error" in outline and outline["error"] is not None:
            raise ValueError(f"Cannot process - upstream outline tool failed: {outline['error']}")
        
        # Extract actual outline from successful tool result
        if isinstance(outline, dict) and "ok" in outline:
            if outline["ok"] is None:
                raise ValueError("Outline tool returned no result")
            outline = outline["ok"]
        
        if not voice_profile or not voice_profile.strip():
            raise ValueError("voice_profile must not be empty.")

        if not (10 <= word_count <= 1000):
            raise ValueError("word_count must be between 10 and 1000.")

        if isinstance(outline, dict):
            outline_str = json.dumps(outline, ensure_ascii=False, indent=2, default=str)
            # BUGFIX BUG-003: Handle empty outline by generating basic structure
            if outline == {} or outline_str == "{}":
                outline_str = self._generate_basic_outline(voice_profile, word_count)
        else:
            outline_str = str(outline).strip()
            if not outline_str:
                # BUGFIX BUG-003: Generate basic outline instead of failing
                outline_str = self._generate_basic_outline(voice_profile, word_count)

        # ----------------------- Generate draft with retry logic --------
        try:
            final_draft = self._run_with_word_count_retry(
                outline_str, voice_profile, word_count
            )
            return {"draft": final_draft}
        except Exception as e:
            raise ValueError(f"Failed to generate draft meeting word count requirements: {str(e)}")

    def _run_with_word_count_retry(self, outline_str: str, voice_profile: str, word_count: int) -> str:
        """Execute draft generation with comprehensive error handling."""
        from essay_agent.utils.logging import debug_print, VERBOSE, tool_trace
        
        max_retries = 3
        current_draft = ""
        
        for attempt in range(max_retries):
            try:
                # Add debug logging
                debug_print(VERBOSE, f"Draft generation attempt {attempt + 1}/{max_retries}")
                debug_print(VERBOSE, f"Outline length: {len(outline_str)} chars")
                debug_print(VERBOSE, f"Voice profile length: {len(voice_profile)} chars")
                debug_print(VERBOSE, f"Target word count: {word_count}")
                
                # Truncate voice_profile to prevent token limit issues
                voice_profile_truncated = self._prepare_voice_profile(voice_profile)
                debug_print(VERBOSE, f"Truncated voice profile length: {len(voice_profile_truncated)} chars")
                
                # Generate initial draft
                current_draft = self._generate_initial_draft(outline_str, voice_profile_truncated, word_count)
                
                # Validate draft is not empty
                if not current_draft or not current_draft.strip():
                    error_msg = f"Generated draft is empty (attempt {attempt + 1})"
                    debug_print(VERBOSE, error_msg)
                    if attempt == max_retries - 1:
                        raise ValueError(error_msg)
                    continue
                
                debug_print(VERBOSE, f"Generated draft length: {len(current_draft)} chars")
                
                # Validate word count
                validation_result = self.word_count_tool.validate_target(current_draft, word_count, tolerance=0.05)
                debug_print(VERBOSE, f"Word count validation: {validation_result.passed} ({validation_result.word_count}/{word_count})")
                
                if validation_result.passed:
                    debug_print(VERBOSE, f"Draft generation succeeded on attempt {attempt + 1}")
                    return current_draft
                
                # Smart adjustment based on word count deviation
                adjustment = self.word_count_tool.calculate_adjustment(current_draft, word_count, tolerance=0.05)
                debug_print(VERBOSE, f"Word count adjustment needed: expansion={adjustment.needs_expansion}, trimming={adjustment.needs_trimming}")
                
                if adjustment.needs_expansion:
                    current_draft = self._expand_draft(
                        current_draft, voice_profile_truncated, word_count, adjustment
                    )
                elif adjustment.needs_trimming:
                    current_draft = self._trim_draft(
                        current_draft, voice_profile_truncated, word_count, adjustment
                    )
                
                # Validate adjusted draft
                validation_result = self.word_count_tool.validate_target(current_draft, word_count, tolerance=0.05)
                
                if validation_result.passed:
                    debug_print(VERBOSE, f"Draft adjustment succeeded on attempt {attempt + 1}")
                    return current_draft
                    
            except Exception as e:
                debug_print(VERBOSE, f"Draft generation failed (attempt {attempt + 1}): {str(e)}")
                if attempt == max_retries - 1:
                    tool_trace("error", "draft", error=str(e))
                    raise ValueError(f"Failed to generate draft after {max_retries} attempts: {str(e)}")
                continue
        
        # Final attempt with larger tolerance
        try:
            debug_print(VERBOSE, "Final attempt with larger tolerance")
            final_adjustment = self.word_count_tool.calculate_adjustment(current_draft, word_count, tolerance=0.10)
            
            if final_adjustment.needs_expansion:
                current_draft = self._expand_draft(
                    current_draft, voice_profile_truncated, word_count, final_adjustment
                )
            elif final_adjustment.needs_trimming:
                current_draft = self._trim_draft(
                    current_draft, voice_profile_truncated, word_count, final_adjustment
                )
            
            # Final validation with larger tolerance
            final_validation = self.word_count_tool.validate_target(current_draft, word_count, tolerance=0.10)
            
            if final_validation.passed:
                debug_print(VERBOSE, "Final attempt succeeded")
                return current_draft
                
        except Exception as e:
            debug_print(VERBOSE, f"Final attempt failed: {str(e)}")
        
        # If all attempts fail but we have a draft, return it
        if current_draft and current_draft.strip():
            debug_print(VERBOSE, "Returning best available draft despite word count issues")
            return current_draft
        
        # Complete failure
        raise ValueError("Failed to generate any valid draft after all attempts")

    def _prepare_voice_profile(self, voice_profile: str) -> str:
        """Prepare voice profile for LLM consumption."""
        voice_profile_truncated = truncate_context(voice_profile.strip(), max_tokens=10000)
        
        # For very large profiles, extract only essential information
        try:
            profile_data = json.loads(voice_profile_truncated)
            
            # If still too large, create a summary profile
            if len(voice_profile_truncated) > 20000:  # Very large profile
                essential_profile = {
                    "user_info": profile_data.get("user_info", {}),
                    "core_values": profile_data.get("core_values", []),
                    "writing_voice": profile_data.get("writing_voice"),
                    "recent_essays": profile_data.get("essay_history", [])[-2:] if profile_data.get("essay_history") else []
                }
                voice_profile_truncated = json.dumps(essential_profile, indent=2, default=str)
        except (json.JSONDecodeError, KeyError):
            # If not JSON, just truncate aggressively
            if len(voice_profile_truncated) > 20000:
                voice_profile_truncated = voice_profile_truncated[:20000] + "\n... [truncated for length]"
        
        return voice_profile_truncated

    def _generate_basic_outline(self, voice_profile: str, word_count: int) -> str:
        """Generate a basic outline structure when none is provided.
        
        BUGFIX BUG-003: This method allows draft tool to work without pre-existing outline
        by creating a simple 3-paragraph structure based on user profile.
        """
        import json
        
        # Create basic outline structure suitable for personal essays
        basic_outline = {
            "structure": {
                "introduction": {
                    "hook": "Opening moment or reflection",
                    "context": "Background and setting"
                },
                "body": {
                    "development": "Main story or experience",
                    "growth": "Lessons learned and personal growth",
                    "reflection": "Deeper insights and meaning"
                },
                "conclusion": {
                    "connection": "Link to future goals",
                    "impact": "How this shapes who you are"
                }
            },
            "word_distribution": {
                "introduction": f"{int(word_count * 0.2)} words",
                "body": f"{int(word_count * 0.6)} words", 
                "conclusion": f"{int(word_count * 0.2)} words"
            },
            "keyword_data": {
                "extracted_keywords": ["personal growth", "experience", "learning", "reflection"]
            }
        }
        
        return json.dumps(basic_outline, ensure_ascii=False, indent=2)

    def _extract_keywords_from_outline(self, outline_str: str) -> list:
        """Extract keywords from outline's keyword_data if present."""
        try:
            import json
            outline_data = json.loads(outline_str)
            if isinstance(outline_data, dict):
                keyword_data = outline_data.get("keyword_data", {})
                if isinstance(keyword_data, dict):
                    extracted_keywords = keyword_data.get("extracted_keywords", [])
                    if isinstance(extracted_keywords, list):
                        return extracted_keywords
        except (json.JSONDecodeError, KeyError, TypeError):
            pass
        
        # Fallback to empty list if no keywords found
        return []

    def _generate_initial_draft(self, outline_str: str, voice_profile: str, word_count: int) -> str:
        """Generate initial draft focused on content quality."""
        # Calculate word count range for self-validation (±10%)
        word_count_min = int(word_count * 0.9)
        word_count_max = int(word_count * 1.1)
        
        # Extract keywords from outline for prompt
        extracted_keywords = self._extract_keywords_from_outline(outline_str)
        
        prompt = render_template(
            DRAFT_PROMPT,
            outline=outline_str,
            voice_profile=voice_profile,
            word_count=word_count,  # Still pass for context, but not enforced
            word_count_min=word_count_min,
            word_count_max=word_count_max,
            extracted_keywords=extracted_keywords,
        )

        llm = get_chat_llm()
        from essay_agent.llm_client import call_llm
        response: str = call_llm(llm, prompt)

        # Allow FakeListLLM deterministic fallback
        if isinstance(llm, FakeListLLM):
            pass

        parsed = safe_parse(schema_parser(_SCHEMA), response)
        draft_text: str = str(parsed["draft"]).strip()

        if not draft_text:
            raise ValueError("Initial draft text is empty.")

        return draft_text

    def _expand_draft(self, current_draft: str, voice_profile: str, target_words: int, adjustment) -> str:
        """Expand draft using targeted expansion techniques."""
        current_words = self.word_count_tool.count_words(current_draft)
        expansion_needed = adjustment.words_needed
        
        expansion_prompt = render_template(
            EXPANSION_PROMPT,
            current_draft=current_draft,
            current_words=current_words,
            target_words=target_words,
            expansion_needed=expansion_needed,
        )

        llm = get_chat_llm()
        from essay_agent.llm_client import call_llm
        response: str = call_llm(llm, expansion_prompt)

        parsed = safe_parse(schema_parser(_EXPANSION_SCHEMA), response)
        expanded_draft: str = str(parsed["expanded_draft"]).strip()

        if not expanded_draft:
            raise ValueError("Expanded draft text is empty.")

        return expanded_draft

    def _trim_draft(self, current_draft: str, voice_profile: str, target_words: int, adjustment) -> str:
        """Trim draft using targeted trimming techniques."""
        current_words = self.word_count_tool.count_words(current_draft)
        trimming_needed = adjustment.words_excess
        
        trimming_prompt = render_template(
            TRIMMING_PROMPT,
            current_draft=current_draft,
            current_words=current_words,
            target_words=target_words,
            trimming_needed=trimming_needed,
        )

        llm = get_chat_llm()
        from essay_agent.llm_client import call_llm
        response: str = call_llm(llm, trimming_prompt)

        parsed = safe_parse(schema_parser(_TRIMMING_SCHEMA), response)
        trimmed_draft: str = str(parsed["trimmed_draft"]).strip()

        if not trimmed_draft:
            raise ValueError("Trimmed draft text is empty.")

        return trimmed_draft 