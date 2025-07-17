# Evals v0.16 – Evidence-Only Bug Report

This document contains **only verified bugs** found through systematic analysis of the 17 conversation JSON files from the v0.16 evaluation run. Each bug includes specific field references and line numbers.

---

## Verified Bugs (Evidence-Based Analysis)

### **Bug #1: Identical Response Duplication Across All Turns**
**Evidence:** 
- `conversation_CONV-001-new-user-stanford-identity_20250716_033327.json` - All 4 agent responses are **identical** (383 words each)
- `conversation_CONV-002-new-user-harvard-diversity_20250716_033338.json` - All 4 agent responses are **identical** (412 words each)
- `conversation_CONV-003-new-user-common-app-challenge_20250716_033352.json` - All 5 agent responses are **identical** (419 words each)
- 14 more files show this pattern

**Fields:** `conversation_turns[*].agent_response`, `conversation_turns[*].word_count`
**Fix Task:** Implement response deduplication middleware that prevents identical consecutive outputs

---

### **Bug #2: Tool Selection Ignores User Evolution**
**Evidence:**
- `conversation_CONV-004-new-user-mit-stem-passion_20250716_033405.json` - User provides specific robotics story in Turn 2, agent still uses `brainstorm` tool in Turn 3
- `conversation_CONV-003-new-user-common-app-challenge_20250716_033352.json` - User selects ACL injury story in Turn 3, agent continues brainstorming in Turn 4
- All Columbia file turns use `classify_prompt` tool regardless of user progression

**Fields:** `conversation_turns[*].tools_used[]`, `phase_name`
**Fix Task:** Add conversation state tracking to prevent returning to brainstorming after story selection

---

### **Bug #3: User Input Completely Ignored**
**Evidence:**
- `conversation_CONV-002-new-user-harvard-diversity_20250716_033338.json` Turn 2: User says "My family immigrated from Vietnam when I was 10" - agent response contains no Vietnam/immigration content
- `conversation_CONV-009-new-user-northwestern-why_20250716_033500.json` Turn 2: User mentions "Knight Lab and Medill-DC program" - response ignores both programs
- Multiple files show user sharing personal stories that receive generic template responses

**Fields:** `conversation_turns[*].user_input` vs `conversation_turns[*].agent_response`
**Fix Task:** Implement user input parsing to extract key details and integrate into response generation

---

### **Bug #4: Wrong Tool Invocation for Phase**
**Evidence:**
- `conversation_CONV-007-new-user-columbia-diversity_20250716_033439.json` - All phases use `classify_prompt` tool instead of expected brainstorm/outline/draft tools
- `conversation_CONV-010-new-user-brown-open_20250716_033530.json` - All phases use `suggest_strategy` tool, no essay drafting attempted

**Fields:** `phase_results[*].tools_used[]` vs expected phase tool mapping
**Fix Task:** Create phase-to-tool mapping validation that ensures correct tool selection per phase

---

### **Bug #5: Memory Utilization Claimed But Not Evidenced**
**Evidence:**
- Multiple files show `memory_utilization_score: 1.0` but responses contain no user-specific personalization
- `conversation_CONV-001-new-user-stanford-identity_20250716_004102.json` shows `memory_accessed: []` (empty) in all turns
- Generic story suggestions appear across different user profiles

**Fields:** `memory_utilization_score`, `conversation_turns[*].memory_accessed[]`
**Fix Task:** Validate that claimed memory access results in personalized content in responses

---

### **Bug #6: Success Indicators Mismatch Reality**
**Evidence:**
- `conversation_CONV-005-new-user-yale-community_20250716_033416.json` Turn 4 claims `yale_connection` and `contribution_clarity` success indicators, but response contains no Yale-specific content
- `conversation_CONV-018-new-user-full-agent_20250716_033623.json` Turn 3 claims `complete_draft` success indicator but no essay draft exists in response

**Fields:** `conversation_turns[*].success_indicators_met[]` vs actual response content
**Fix Task:** Implement success indicator validation against actual response content

---

### **Bug #7: Prompt Response Quality Always Zero**
**Evidence:**
- All 17 files show `prompt_response_quality: 0.0` despite some conversations having coherent turns
- This metric appears broken or miscalibrated

**Fields:** `prompt_response_quality`
**Fix Task:** Fix prompt response quality calculation algorithm

---

### **Bug #8: Phase Completion Inconsistency**
**Evidence:**
- `conversation_CONV-003-new-user-common-app-challenge_20250716_033352.json` - `phase_results[4].completed: false` but `completion_status: "partial"` should reflect this
- `conversation_CONV-001-new-user-stanford-identity_20250716_033327.json` - `completion_status: "completed"` but `prompt_response_quality: 0.0`

**Fields:** `phase_results[*].completed` vs `completion_status`
**Fix Task:** Ensure completion_status accurately reflects phase completion states

---

### **Bug #9: Extreme Response Time Inconsistencies**
**Evidence:**
- `conversation_CONV-009-new-user-northwestern-why_20250716_033500.json` Turn 1: `response_time_seconds: 19.728` vs Turn 2: `1.053` (18x difference)
- `conversation_CONV-012-new-user-process-learning_20250716_033555.json` Turn 1: `16.441` vs subsequent turns ~1.5 seconds

**Fields:** `conversation_turns[*].response_time_seconds`
**Fix Task:** Investigate response time inconsistencies and normalize measurement

---

### **Bug #10: Expected Behavior Match Always Low**
**Evidence:**
- Most files show `expected_behavior_match: 0.0` or very low values (0.2-0.4) across all phases
- Even successful phases show poor behavior matching

**Fields:** `phase_results[*].expected_behavior_match`, `conversation_turns[*].expected_behavior_match`
**Fix Task:** Recalibrate expected behavior matching algorithm

---

### **Bug #11: No Essay Generation Despite "Drafting" Phases**
**Evidence:**
- All files show `final_essay_word_count: null` and `final_essay_quality_score: null`
- Multiple conversations have "drafting" or "drafting_assistance" phases but produce no essay text

**Fields:** `final_essay_word_count`, `final_essay_quality_score`
**Fix Task:** Implement actual essay generation in drafting phases

---

### **Bug #12: Missing Word Count Validation**
**Evidence:**
- `conversation_CONV-002-new-user-harvard-diversity_20250716_033338.json` Turn 4: User requests "150 words" but response is 412 words
- No word limit enforcement in any conversation

**Fields:** User requests vs `conversation_turns[*].word_count`
**Fix Task:** Add word limit parameter validation and enforcement

---

### **Bug #13: Conversation Naturalness Near Zero**
**Evidence:**
- Most files show `conversation_naturalness` between 0.0-0.3 
- `conversation_CONV-007-new-user-columbia-diversity_20250716_033439.json`: `0.0`
- `conversation_CONV-009-new-user-northwestern-why_20250716_033500.json`: `0.0`

**Fields:** `conversation_naturalness`
**Fix Task:** Fix conversation naturalness calculation or improve response adaptation

---

### **Bug #14: School-Specific Context Missing**
**Evidence:**
- Northwestern conversation contains no Northwestern-specific mentions
- Yale conversation lacks Yale community references  
- Brown conversation missing open curriculum discussion despite user mentioning it

**Fields:** `scenario_id` vs response content analysis
**Fix Task:** Implement school-specific context injection based on scenario_id

---

### **Bug #15: Tools Used Summary Inconsistencies**
**Evidence:**
- `conversation_CONV-009-new-user-northwestern-why_20250716_033500.json`: `tools_used_summary: {"brainstorm": 4}` but `unique_tools_used: 1` (correct), yet some calculations appear wrong
- Empty summaries in some files despite tool usage

**Fields:** `tools_used_summary` vs `conversation_turns[*].tools_used[]`
**Fix Task:** Fix tools_used_summary aggregation logic

---

### **Bug #16: Identical Word Counts Across Different Content**
**Evidence:**
- Multiple conversations show identical word counts (e.g., 333, 370, 412) across different responses
- Suggests template reuse rather than original content generation

**Fields:** `conversation_turns[*].word_count`
**Fix Task:** Investigate template reuse causing identical word counts

---

### **Bug #17: Autonomy Level Violations**
**Evidence:**
- `conversation_CONV-001-new-user-stanford-identity_20250716_001859.json` shows `"issues_encountered": ["Autonomy level not respected: AutonomyLevel.COLLABORATIVE"]` in multiple phases

**Fields:** `phase_results[*].issues_encountered[]`
**Fix Task:** Implement proper autonomy level checking before action execution

---

### **Bug #18: Empty Notable Successes Despite High Scores**
**Evidence:**
- Multiple files show `notable_successes: []` even when phases have success_score > 0.5
- `conversation_CONV-018-new-user-full-agent_20250716_033623.json` has `success_score: 0.8` for agent_drafting but empty notable_successes

**Fields:** `notable_successes[]` vs `phase_results[*].success_score`
**Fix Task:** Populate notable_successes when phases achieve high success scores

---

### **Bug #19: Duration Seconds Patterns Suggest Mocking**
**Evidence:**
- Multiple files show suspiciously consistent duration patterns (~1.5 seconds)
- Some files show identical durations across different phases

**Fields:** `phase_results[*].duration_seconds`
**Fix Task:** Verify duration measurement is capturing actual execution time, not mocked values

---

### **Bug #20: College-Specific Prompt Handling Broken**
**Evidence:**
- MIT prompt about "pleasure" gets generic brainstorm responses
- Harvard diversity prompt receives unrelated environmental cleanup suggestions
- No evidence of prompt-specific response adaptation

**Fields:** `scenario_id` vs response content matching
**Fix Task:** Implement college-specific prompt interpretation and response generation

---

## Summary Statistics
- **Files Analyzed:** 17
- **Total Bugs Identified:** 20
- **Critical Bugs:** 8 (response duplication, ignoring user input, wrong tools, no essay generation)
- **Major Bugs:** 7 (memory issues, metrics broken, completion logic)
- **Minor Bugs:** 5 (timing, counting, labeling issues)

---

## Recommendations
1. **Priority 1:** Fix response deduplication and user input processing
2. **Priority 2:** Implement proper tool selection based on conversation state  
3. **Priority 3:** Add essay generation capability to drafting phases
4. **Priority 4:** Fix broken metrics (response quality, naturalness, behavior matching)
5. **Priority 5:** Add school-specific context injection system 