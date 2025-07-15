from __future__ import annotations

"""essay_agent.tools.outline

LangChain-compatible tool that generates a structured five-part outline for a
chosen personal story idea.  It uses GPT-4 via :pymod:`essay_agent.llm_client`
under the hood but falls back to a deterministic stub when the environment is
offline (``FakeListLLM``) or the response cannot be parsed as JSON.
"""

import json
from typing import Any, Dict, List

from essay_agent.llm_client import chat
from essay_agent.prompts.outline import OUTLINE_PROMPT
from essay_agent.prompts.templates import render_template
from essay_agent.tools.base import ValidatedTool
from essay_agent.tools import register_tool
from essay_agent.memory.simple_memory import ensure_essay_record, SimpleMemory
from essay_agent.memory.user_profile_schema import EssayVersion
from datetime import datetime


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _build_stub(story: str, prompt: str, word_count: int) -> Dict[str, Any]:  # noqa: D401
    """Return a deterministic outline used in CI/offline mode."""

    outline = {
        "hook": f"A moment that redefined my perspective on: {story[:30]}...",
        "context": "Provide background that anchors the reader and highlights the setting.",
        "conflict": "Describe the central tension or obstacle encountered.",
        "growth": "Explain the actions taken and lessons learned in overcoming the conflict.",
        "reflection": "Conclude with personal insights and how the experience shapes future goals.",
    }
    return {"outline": outline, "estimated_word_count": word_count}


# ---------------------------------------------------------------------------
# Tool implementation
# ---------------------------------------------------------------------------


@register_tool("outline")
class OutlineTool(ValidatedTool):
    """Generate a five-part outline for a personal story idea.

    Input
    -----
    story : str
        The chosen personal story seed selected during brainstorming.
    prompt : str
        The original essay prompt (so the outline stays on-topic).
    word_count : int, default=650
        Target final essay length – used to size each outline section.

    Output (dict)
    --------------
    {
        "outline": {
            "hook": str,
            "context": str,
            "conflict": str,
            "growth": str,
            "reflection": str
        },
        "estimated_word_count": int
    }
    """

    name: str = "outline"
    description: str = (
        "Generate a structured five-part outline (hook, context, conflict, "
        "growth, reflection) for a given story idea. Returns strict JSON."
    )

    # ------------------------------------------------------------------
    # Core sync execution (ValidatedTool requirement)
    # ------------------------------------------------------------------

    def _run(  # type: ignore[override]
        self, *, story: str, prompt: str, word_count: int = 650, user_id: str | None = None, **_: Any
    ) -> Dict[str, Any]:
        """
        Generate a five-part outline for a personal story.

        Args:
            story: The chosen personal story seed.
            prompt: The original essay prompt.
            word_count: Target final essay length.
            user_id: Optional user ID for memory storage.

        Returns:
            Dict containing the outline and metadata.
        """
        from essay_agent.utils.logging import debug_print, VERBOSE
        
        if VERBOSE:
            debug_print(VERBOSE, f"Starting outline generation for story: '{story[:50]}...'")
        
        # Extract keywords from prompt for planning
        keyword_data = self._extract_and_plan_keywords(prompt, word_count)
        
        # Calculate word distribution for structural planning
        word_distribution = self._calculate_word_distribution(word_count)
        
        try:
            # Render the outline prompt with keyword planning
            rendered_prompt = render_template(
                OUTLINE_PROMPT,
                essay_prompt=prompt,
                story=story,
                word_count=word_count,
                extracted_keywords=keyword_data.get("extracted_keywords", []),
                keyword_planning=keyword_data.get("keyword_planning", {}),
                **word_distribution
            )
            
            if VERBOSE:
                debug_print(VERBOSE, f"Calling LLM for outline generation...")
            
            # Get LLM response
            response = chat(rendered_prompt)
            
            if VERBOSE:
                debug_print(VERBOSE, f"LLM response received: {len(response)} characters")
            
            # Try to parse as JSON
            try:
                outline_data = json.loads(response)
                
                # Validate outline structure
                if not isinstance(outline_data, dict) or "outline" not in outline_data:
                    raise ValueError("Invalid outline format")
                
                # Add keyword planning metadata
                outline_data.update({
                    "keyword_data": keyword_data,
                    "word_distribution": word_distribution
                })
                
                if VERBOSE:
                    debug_print(VERBOSE, f"Outline generated successfully with {len(outline_data.get('outline', {}))} sections")
                
                # Store in memory if user_id provided
                if user_id:
                    self._store_outline_in_memory(user_id, outline_data, story, prompt)
                
                return outline_data
                
            except (json.JSONDecodeError, ValueError) as e:
                if VERBOSE:
                    debug_print(VERBOSE, f"JSON parsing failed: {e}, using fallback")
                
                # Fall back to stub outline with keyword planning
                stub_outline = _build_stub(story, prompt, word_count)
                stub_outline.update({
                    "keyword_data": keyword_data,
                    "word_distribution": word_distribution
                })
                return stub_outline
                
        except Exception as e:
            if VERBOSE:
                debug_print(VERBOSE, f"Error during outline generation: {e}")
            
            # Return fallback outline with keyword planning
            stub_outline = _build_stub(story, prompt, word_count)
            stub_outline.update({
                "keyword_data": keyword_data,
                "word_distribution": word_distribution,
                "error": str(e)
            })
            return stub_outline
    
    def _extract_and_plan_keywords(self, essay_prompt: str, word_count: int) -> Dict[str, Any]:
        """
        Extract key terms from essay prompt and plan how outline will address them.
        Uses the same curated keywords as the evaluation system for consistency.
        
        Args:
            essay_prompt: The essay prompt to analyze
            word_count: Target word count for planning
            
        Returns:
            Dictionary with keyword extraction and planning data
        """
        from essay_agent.utils.logging import debug_print, VERBOSE
        
        try:
            # Use curated keywords that match the evaluation system
            # First, categorize the prompt to get the right keyword set
            prompt_lower = essay_prompt.lower()
            
            # Get curated keywords based on prompt type
            if any(keyword in prompt_lower for keyword in [
                'problem you\'ve solved', 'problem you have solved', 'challenge you faced',
                'solve', 'solution', 'dilemma', 'overcome', 'difficulty'
            ]):
                # Challenge prompt keywords
                curated_keywords = ["problem", "solve", "challenge", "solution", "steps", "significance", "difficulty", "overcome"]
            elif any(keyword in prompt_lower for keyword in [
                'community', 'cultural background', 'family traditions', 'diversity', 'inclusion',
                'relates to your cultural', 'community or family'
            ]):
                # Community prompt keywords
                curated_keywords = ["community", "cultural", "family", "traditions", "proud", "background", "impact"]
            elif any(keyword in prompt_lower for keyword in [
                'identity', 'background', 'heritage', 'culture', 'meaningful they believe',
                'application would be incomplete'
            ]):
                # Identity prompt keywords  
                curated_keywords = ["background", "identity", "meaningful", "story", "shapes", "perspective", "who you are"]
            elif any(keyword in prompt_lower for keyword in [
                'engaging', 'captivate', 'lose track of time', 'learn more', 'intellectual curiosity',
                'find so engaging'
            ]):
                # Passion prompt keywords
                curated_keywords = ["engaging", "captivate", "lose track", "time", "learn", "curiosity", "interest"]
            elif any(keyword in prompt_lower for keyword in [
                'achievement', 'accomplishment', 'sparked a period', 'personal growth',
                'new understanding', 'proud', 'leadership'
            ]):
                # Achievement prompt keywords
                curated_keywords = ["accomplishment", "growth", "realization", "understanding", "transformation", "change"]
            else:
                # Fallback: extract meaningful words from prompt
                import re
                stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during', 'before', 'after', 'above', 'below', 'between', 'among', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them', 'my', 'your', 'his', 'her', 'its', 'our', 'their'}
                words = re.findall(r'\b\w+\b', essay_prompt.lower())
                keywords = [word for word in words if len(word) > 3 and word not in stop_words]
                # Remove duplicates while preserving order
                seen = set()
                curated_keywords = []
                for word in keywords:
                    if word not in seen:
                        seen.add(word)
                        curated_keywords.append(word)
                curated_keywords = curated_keywords[:8]  # Limit to top 8
            
            # Filter keywords that actually appear in the prompt or are conceptually relevant
            extracted_keywords = []
            for keyword in curated_keywords:
                if keyword in prompt_lower or any(part in prompt_lower for part in keyword.split()):
                    extracted_keywords.append(keyword)
            
            # Ensure we have some keywords
            if not extracted_keywords:
                extracted_keywords = curated_keywords[:3]  # Use first 3 as fallback
            
            if VERBOSE:
                debug_print(VERBOSE, f"Extracted curated keywords from prompt: {extracted_keywords}")
            
            # Plan how each outline section will address keywords
            keyword_planning = self._plan_keyword_integration(extracted_keywords, word_count)
            
            return {
                "extracted_keywords": extracted_keywords,
                "keyword_planning": keyword_planning,
                "prompt_analysis": {
                    "total_words": len(essay_prompt.split()),
                    "unique_keywords": len(set(curated_keywords)),
                    "selected_keywords": len(extracted_keywords)
                }
            }
            
        except Exception as e:
            if VERBOSE:
                debug_print(VERBOSE, f"Error extracting keywords: {e}")
            
            return {
                "extracted_keywords": [],
                "keyword_planning": {},
                "error": str(e)
            }
    
    def _plan_keyword_integration(self, keywords: List[str], word_count: int) -> Dict[str, Any]:
        """
        Plan how outline sections will integrate keywords.
        
        Args:
            keywords: List of extracted keywords
            word_count: Target word count
            
        Returns:
            Dictionary with keyword integration planning
        """
        if not keywords:
            return {}
        
        # Distribute keywords across outline sections
        sections = ["hook", "context", "conflict", "growth", "reflection"]
        keywords_per_section = max(1, len(keywords) // len(sections))
        
        section_keyword_plan = {}
        keyword_index = 0
        
        for section in sections:
            section_keywords = []
            for _ in range(keywords_per_section):
                if keyword_index < len(keywords):
                    section_keywords.append(keywords[keyword_index])
                    keyword_index += 1
            
            # Add any remaining keywords to reflection section
            if section == "reflection":
                while keyword_index < len(keywords):
                    section_keywords.append(keywords[keyword_index])
                    keyword_index += 1
            
            section_keyword_plan[section] = section_keywords
        
        return {
            "section_keywords": section_keyword_plan,
            "integration_strategy": "Keywords distributed across outline sections for natural integration",
            "total_keywords": len(keywords),
            "planning_notes": "Each section should weave in assigned keywords naturally through story details"
        }
    
    def _calculate_word_distribution(self, word_count: int) -> Dict[str, Any]:
        """
        Calculate word distribution across outline sections.
        
        Args:
            word_count: Target word count
            
        Returns:
            Dictionary with word distribution data
        """
        # Standard percentages for five-part structure
        percentages = {
            "hook": 15,
            "context": 20,
            "conflict": 25,
            "growth": 25,
            "reflection": 15
        }
        
        distribution = {}
        for section, percentage in percentages.items():
            words = int(word_count * percentage / 100)
            distribution[f"{section}_words"] = words
            distribution[f"{section}_percentage"] = percentage
        
        return distribution
    
    def _store_outline_in_memory(self, user_id: str, outline_data: Dict[str, Any], story: str, prompt: str) -> None:
        """
        Store outline in user memory for future reference.
        
        Args:
            user_id: User identifier
            outline_data: Generated outline data
            story: Story used for outline
            prompt: Essay prompt
        """
        from essay_agent.utils.logging import debug_print, VERBOSE
        
        try:
            # Store outline in essay memory
            essay_record = ensure_essay_record(user_id, "outline_generation")
            
            # Create essay version
            essay_version = EssayVersion(
                content=json.dumps(outline_data),
                timestamp=datetime.now(),
                version_type="outline",
                metadata={
                    "story": story,
                    "prompt": prompt,
                    "word_count": outline_data.get("estimated_word_count", 0),
                    "keyword_data": outline_data.get("keyword_data", {})
                }
            )
            
            essay_record.essay_versions.append(essay_version)
            SimpleMemory.save_essay(user_id, "outline_generation", essay_record)
            
            if VERBOSE:
                debug_print(VERBOSE, f"Outline stored in memory for user: {user_id}")
                
        except Exception as e:
            if VERBOSE:
                debug_print(VERBOSE, f"Error storing outline in memory: {e}")
            # Don't fail the tool if memory storage fails
            pass

    # ------------------------------------------------------------------
    # Convenience call wrapper (mirrors EchoTool pattern)
    # ------------------------------------------------------------------

    def __call__(self, *args: Any, **kwargs: Any):  # type: ignore[override]
        """Ergonomic call signatures for tests & executor.

        Examples
        --------
        tool(story="...", prompt="...", word_count=650)
        """
        # Allow pure-keyword usage (preferred) ---------------------------
        if args:
            raise ValueError("Provide inputs as keyword arguments only")
        return self._run(**kwargs) 