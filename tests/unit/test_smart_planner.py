"""Tests for the smart planner implementation."""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock

from essay_agent.planner import EssayReActPlanner, Phase, EssayPlan
from essay_agent.memory.user_profile_schema import UserProfile, UserInfo, AcademicProfile
from langchain.llms.fake import FakeListLLM


class TestSmartPlanner:
    """Test suite for the enhanced smart planner."""

    def setup_method(self):
        """Set up test fixtures."""
        self.smart_response = {
            "tool": "brainstorm",
            "args": {"essay_prompt": "test prompt", "profile": "test profile"},
            "reasoning": {
                "context_analysis": "User requesting story ideas for college essay",
                "quality_assessment": "No previous outputs to evaluate",
                "decision_type": "CONTINUE - Starting new essay workflow",
                "tool_selection": "brainstorm tool selected for story generation",
                "expected_outcome": "Generate 3 unique story ideas",
                "success_criteria": "Stories match prompt and user profile"
            },
            "metadata": {
                "confidence": 0.9,
                "phase": "BRAINSTORMING",
                "quality_score": None,
                "revision_count": 0,
                "memory_flags": ["story_reuse_checked"]
            }
        }

    def test_context_analysis_with_memory(self):
        """Test context analysis with hierarchical memory."""
        # Create mock memory
        mock_memory = Mock()
        mock_profile = Mock()
        mock_profile.model_dump.return_value = {"name": "Test User", "grade": 12}
        mock_profile.essay_history = []
        mock_profile.core_values = []
        mock_profile.defining_moments = []
        mock_memory.profile = mock_profile
        mock_memory.get_recent_chat.return_value = ["Hello", "Hi there"]
        
        # Create planner
        planner = EssayReActPlanner(llm=Mock())
        
        # Mock hierarchical memory loading
        with patch('essay_agent.planner.HierarchicalMemory') as mock_hierarchical:
            mock_hierarchical.return_value = mock_memory
            
            context = {
                "user_id": "test_user",
                "tool_outputs": {"brainstorm": {"stories": ["Story 1", "Story 2"]}},
                "conversation_history": ["Previous message"]
            }
            
            analysis = planner._analyze_context(context)
            
            # Verify analysis contains expected data
            assert "user_profile" in analysis
            assert "essay_history" in analysis
            assert "conversation_context" in analysis
            assert "working_memory" in analysis
            assert "tool_outputs" in analysis
            
            # Verify memory was loaded
            mock_hierarchical.assert_called_once_with("test_user")
            mock_memory.get_recent_chat.assert_called_once_with(k=10)

    def test_context_analysis_fallback_to_simple_memory(self):
        """Test fallback to simple memory when hierarchical memory fails."""
        planner = EssayReActPlanner(llm=Mock())
        
        # Mock hierarchical memory to fail, simple memory to succeed
        with patch('essay_agent.planner.HierarchicalMemory') as mock_hierarchical:
            mock_hierarchical.side_effect = Exception("Memory loading failed")
            
            with patch('essay_agent.planner.SimpleMemory') as mock_simple:
                mock_profile = Mock()
                mock_profile.model_dump.return_value = {"name": "Test User"}
                mock_simple.load.return_value = mock_profile
                
                context = {"user_id": "test_user"}
                analysis = planner._analyze_context(context)
                
                # Verify simple memory was used as fallback
                mock_simple.load.assert_called_once_with("test_user")
                assert "user_profile" in analysis

    def test_json_extraction_from_response(self):
        """Test JSON extraction from various response formats."""
        planner = EssayReActPlanner(llm=Mock())
        
        # Test JSON with markdown markers
        response_with_markers = """
        Some reasoning text here.
        
        ```json
        {"tool": "brainstorm", "args": {}}
        ```
        """
        
        result = planner._extract_json_from_response(response_with_markers)
        assert result == '{"tool": "brainstorm", "args": {}}'
        
        # Test raw JSON
        response_raw = 'Thought: Analyzing context\n{"tool": "outline", "args": {"story": "test"}}'
        result = planner._extract_json_from_response(response_raw)
        assert result == '{"tool": "outline", "args": {"story": "test"}}'
        
        # Test complex nested JSON
        response_nested = '{"tool": "revise", "args": {"data": {"nested": "value"}}, "reasoning": {"type": "RETRY"}}'
        result = planner._extract_json_from_response(response_nested)
        expected = '{"tool": "revise", "args": {"data": {"nested": "value"}}, "reasoning": {"type": "RETRY"}}'
        assert result == expected

    def test_smart_planning_success(self):
        """Test successful smart planning execution."""
        # Create fake LLM with smart response
        smart_response_json = json.dumps(self.smart_response)
        fake_llm = FakeListLLM(responses=[smart_response_json])
        
        planner = EssayReActPlanner(llm=fake_llm)
        
        # Mock context analysis
        with patch.object(planner, '_analyze_context') as mock_analysis:
            mock_analysis.return_value = {
                "user_profile": "{}",
                "essay_history": "[]",
                "conversation_context": "[]",
                "working_memory": "[]",
                "tool_outputs": "{}"
            }
            
            # Mock tool registry
            with patch('essay_agent.planner.TOOL_REGISTRY', {"brainstorm": Mock()}):
                result = planner.decide_next_action("Generate story ideas", {"user_id": "test"})
                
                # Verify successful plan creation
                assert isinstance(result, EssayPlan)
                assert result.phase == Phase.BRAINSTORMING
                assert result.data["next_tool"] == "brainstorm"
                assert result.data["args"]["essay_prompt"] == "test prompt"
                assert "reasoning" in result.metadata
                assert result.metadata["confidence"] == 0.9
                assert not result.errors

    def test_smart_planning_with_quality_evaluation(self):
        """Test smart planning with quality metrics from tool outputs."""
        # Create response suggesting revision due to low quality
        revision_response = {
            "tool": "revise",
            "args": {"focus": "clarity", "target_score": 7.5},
            "reasoning": {
                "context_analysis": "User has draft with low quality score",
                "quality_assessment": "Essay scoring shows overall_score = 6.2, below threshold",
                "decision_type": "LOOP - Revision cycle needed for quality improvement",
                "tool_selection": "revise tool to address clarity issues",
                "expected_outcome": "Improve essay quality score to >= 7.0",
                "success_criteria": "Essay scoring shows improvement in clarity"
            },
            "metadata": {
                "confidence": 0.85,
                "phase": "REVISING",
                "quality_score": 6.2,
                "revision_count": 1,
                "memory_flags": ["quality_threshold_check"]
            }
        }
        
        fake_llm = FakeListLLM(responses=[json.dumps(revision_response)])
        planner = EssayReActPlanner(llm=fake_llm)
        
        # Mock context with quality metrics
        with patch.object(planner, '_analyze_context') as mock_analysis:
            mock_analysis.return_value = {
                "user_profile": "{}",
                "essay_history": "[]",
                "conversation_context": "[]",
                "working_memory": "[]",
                "tool_outputs": json.dumps({
                    "essay_scoring": {
                        "overall_score": 6.2,
                        "is_strong_essay": False,
                        "scores": {"clarity": 5, "insight": 7, "structure": 6}
                    }
                })
            }
            
            with patch('essay_agent.planner.TOOL_REGISTRY', {"revise": Mock()}):
                result = planner.decide_next_action("Improve my essay", {"user_id": "test"})
                
                # Verify revision decision
                assert result.phase == Phase.REVISING
                assert result.data["next_tool"] == "revise"
                assert result.metadata["quality_score"] == 6.2
                assert result.metadata["revision_count"] == 1
                assert "quality_threshold_check" in result.metadata["memory_flags"]

    def test_fallback_to_simple_planning(self):
        """Test fallback to simple planning when smart planning fails."""
        # Create LLM that returns invalid JSON for smart planning
        fake_llm = FakeListLLM(responses=[
            "Invalid JSON response",  # Smart planning fails
            '{"tool": "brainstorm", "args": {}}'  # Simple planning succeeds
        ])
        
        planner = EssayReActPlanner(llm=fake_llm)
        
        with patch.object(planner, '_analyze_context') as mock_analysis:
            mock_analysis.return_value = {"user_profile": "{}"}
            
            with patch('essay_agent.planner.TOOL_REGISTRY', {"brainstorm": Mock()}):
                result = planner.decide_next_action("Generate ideas", {"user_id": "test"})
                
                # Verify fallback worked
                assert result.phase == Phase.BRAINSTORMING
                assert result.data["next_tool"] == "brainstorm"
                assert "fallback_reason" in result.metadata
                assert "Smart planning failed" in result.metadata["fallback_reason"]

    def test_unknown_tool_handling(self):
        """Test handling of unknown tools in smart planning."""
        unknown_tool_response = {
            "tool": "unknown_tool",
            "args": {},
            "reasoning": {"decision_type": "CONTINUE"},
            "metadata": {"confidence": 0.8}
        }
        
        fake_llm = FakeListLLM(responses=[json.dumps(unknown_tool_response)])
        planner = EssayReActPlanner(llm=fake_llm)
        
        with patch.object(planner, '_analyze_context') as mock_analysis:
            mock_analysis.return_value = {"user_profile": "{}"}
            
            result = planner.decide_next_action("Test unknown tool", {"user_id": "test"})
            
            # Verify error handling
            assert result.errors == ["Unknown tool unknown_tool"]
            assert result.data["next_tool"] == "unknown_tool"
            assert "reasoning" in result.metadata

    def test_memory_integration_story_reuse_prevention(self):
        """Test that context analysis includes memory for story reuse prevention."""
        planner = EssayReActPlanner(llm=Mock())
        
        # Create mock memory with essay history
        mock_memory = Mock()
        mock_profile = Mock()
        mock_profile.model_dump.return_value = {"name": "Test User"}
        
        # Mock essay history with used stories
        mock_essay_record = Mock()
        mock_essay_record.model_dump.return_value = {
            "prompt_id": "test_prompt",
            "platform": "CommonApp",
            "status": "completed",
            "versions": [{"used_stories": ["My Leadership Story", "Overcoming Challenges"]}]
        }
        mock_profile.essay_history = [mock_essay_record]
        mock_profile.core_values = []
        mock_profile.defining_moments = []
        mock_memory.profile = mock_profile
        mock_memory.get_recent_chat.return_value = []
        
        with patch('essay_agent.planner.HierarchicalMemory') as mock_hierarchical:
            mock_hierarchical.return_value = mock_memory
            
            context = {"user_id": "test_user"}
            analysis = planner._analyze_context(context)
            
            # Verify essay history is included in analysis
            essay_history = json.loads(analysis["essay_history"])
            assert len(essay_history) == 1
            assert essay_history[0]["platform"] == "CommonApp"
            assert "My Leadership Story" in essay_history[0]["versions"][0]["used_stories"]

    def test_phase_mapping_for_evaluation_tools(self):
        """Test that evaluation tools map to appropriate phases."""
        from essay_agent.planner import _phase_from_tool
        
        # Test workflow tools
        assert _phase_from_tool("brainstorm") == Phase.BRAINSTORMING
        assert _phase_from_tool("outline") == Phase.OUTLINING
        assert _phase_from_tool("draft") == Phase.DRAFTING
        assert _phase_from_tool("revise") == Phase.REVISING
        assert _phase_from_tool("polish") == Phase.POLISHING
        
        # Test evaluation tools map to revising phase
        assert _phase_from_tool("essay_scoring") == Phase.REVISING
        assert _phase_from_tool("weakness_highlight") == Phase.REVISING
        assert _phase_from_tool("cliche_detection") == Phase.REVISING
        assert _phase_from_tool("alignment_check") == Phase.REVISING
        
        # Test unknown tool defaults to brainstorming
        assert _phase_from_tool("unknown_tool") == Phase.BRAINSTORMING

    def test_error_recovery_ultimate_fallback(self):
        """Test ultimate fallback when both smart and simple planning fail."""
        # Create LLM that returns invalid responses for both attempts
        fake_llm = FakeListLLM(responses=[
            "Invalid JSON for smart planning",
            "Invalid JSON for simple planning too"
        ])
        
        planner = EssayReActPlanner(llm=fake_llm)
        
        with patch.object(planner, '_analyze_context') as mock_analysis:
            mock_analysis.return_value = {"user_profile": "{}"}
            
            result = planner.decide_next_action("Test ultimate fallback", {"user_id": "test"})
            
            # Verify ultimate fallback
            assert len(result.errors) == 1
            assert "Both smart and simple planning failed" in result.errors[0]
            assert "llm_raw" in result.metadata

    def test_no_llm_fallback(self):
        """Test fallback when no LLM is available."""
        planner = EssayReActPlanner(llm=None)
        
        result = planner.decide_next_action("Test no LLM", {"user_id": "test"})
        
        # Verify graceful handling - uses FakeListLLM as fallback
        assert isinstance(result, EssayPlan)
        assert result.phase == Phase.BRAINSTORMING
        assert result.data["next_tool"] == "brainstorm"  # FakeListLLM provides mock response
        assert result.errors == []

    def test_context_analysis_with_missing_data(self):
        """Test context analysis handles missing data gracefully."""
        planner = EssayReActPlanner(llm=Mock())
        
        # Test with empty context
        analysis = planner._analyze_context({})
        
        # Verify default values
        assert analysis["user_profile"] == "{}"
        assert analysis["essay_history"] == "[]"
        assert analysis["conversation_context"] == "[]"
        assert analysis["working_memory"] == "[]"
        assert analysis["tool_outputs"] == "{}"

    def test_structured_reasoning_output(self):
        """Test that the planner returns structured reasoning in metadata."""
        fake_llm = FakeListLLM(responses=[json.dumps(self.smart_response)])
        planner = EssayReActPlanner(llm=fake_llm)
        
        with patch.object(planner, '_analyze_context') as mock_analysis:
            mock_analysis.return_value = {"user_profile": "{}"}
            
            with patch('essay_agent.planner.TOOL_REGISTRY', {"brainstorm": Mock()}):
                result = planner.decide_next_action("Generate ideas", {"user_id": "test"})
                
                # Verify structured reasoning
                reasoning = result.metadata["reasoning"]
                assert "context_analysis" in reasoning
                assert "quality_assessment" in reasoning
                assert "decision_type" in reasoning
                assert "tool_selection" in reasoning
                assert "expected_outcome" in reasoning
                assert "success_criteria" in reasoning
                
                # Verify reasoning content
                assert "Starting new essay workflow" in reasoning["decision_type"]
                assert "brainstorm tool selected" in reasoning["tool_selection"] 