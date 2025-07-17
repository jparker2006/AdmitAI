# Critical Bug Fix Implementation Prompt

You are an expert Python developer tasked with fixing the **4 most critical bugs** in the essay_agent system based on evaluation evidence from 17 conversation JSON files.

## Context & Evidence
The evaluation analysis revealed identical response duplication across all conversations, with agents ignoring user input and selecting wrong tools. See `evals_v0_16_bugs.md` for complete evidence.

## Your Task: Fix These 4 Critical Bugs

### **BUG #1: Identical Response Duplication (HIGHEST PRIORITY)**
**Evidence:** All agent responses in every conversation file are identical word-for-word
- File: `conversation_CONV-001-*` through `conversation_CONV-011-*`
- Field: `agent_response` contains same 383-412 word template every turn
- Impact: Complete conversation failure

**Fix Requirements:**
1. Locate where agent responses are generated/cached
2. Ensure each response incorporates current user input
3. Implement response variation logic
4. Test: Agent gives different responses to different user inputs

### **BUG #2: User Input Completely Ignored**
**Evidence:** User provides specific details (names, experiences, schools) but agent response never references them
- Example: User says "I'm Sarah, applying to Stanford for CS" → Agent gives generic response
- Field: `user_input` vs `agent_response` show zero correlation
- Impact: Agent appears non-functional to users

**Fix Requirements:**
1. Ensure user input parsing extracts key details
2. Modify prompt/context injection to include user specifics
3. Validate agent responses reference user-provided information
4. Test: Agent mentions user's name, school, major when provided

### **BUG #3: Tool Selection Mismatch**
**Evidence:** `tools_used` field shows wrong tools for conversation phase
- Turn 1: Shows ["outline", "draft"] but should be ["profile_questions", "brainstorm"]
- Turn 3: Shows ["research"] in drafting phase where it's irrelevant
- Impact: Tools don't match user needs or conversation flow

**Fix Requirements:**
1. Review tool selection logic in conversation runner
2. Map conversation phases to appropriate tool sets
3. Ensure tool selection reflects actual user requests
4. Test: Tools match conversation phase and user intent

### **BUG #4: No Essay Content Generation**
**Evidence:** Despite "drafting" phases, no actual essay text is produced
- Field: `agent_response` contains only advice/guidance, never essay drafts
- Tools show "draft" usage but no essay content appears
- Impact: Core functionality (essay writing) is missing

**Fix Requirements:**
1. Verify essay generation tools actually produce content
2. Ensure generated essays appear in agent responses
3. Check if essay content is being filtered/lost somewhere
4. Test: Agent produces actual essay paragraphs when requested

## Implementation Strategy

### Phase 1: Investigation (15 minutes)
```bash
# Examine conversation flow
python -c "
import json
with open('conversation_CONV-001-new-user-stanford-identity_20250716_033327.json') as f:
    data = json.load(f)
    for turn in data['conversation_turns']:
        print(f\"Turn {turn['turn_number']}: Tools={turn.get('tools_used', [])}\")
        print(f\"Response length: {len(turn['agent_response'])} chars\")
        print('---')
"

# Find where responses are generated
grep -r "agent_response" essay_agent/
grep -r "identical" essay_agent/
```

### Phase 2: Root Cause Analysis (15 minutes)
1. **Find response generation code:**
   - Check `essay_agent/eval/conversation_runner.py`
   - Check `essay_agent/executor.py`
   - Check `essay_agent/cli.py`

2. **Identify caching/templating logic:**
   - Look for static response templates
   - Find where user input should be processed
   - Locate tool selection algorithm

### Phase 3: Implement Fixes (60 minutes)
For each bug:
1. Write fix with clear comments
2. Add logging for debugging
3. Preserve existing functionality
4. Follow existing code patterns

### Phase 4: Testing Protocol (30 minutes)
```bash
# Test single conversation
python -m essay_agent.eval.conversation_runner --scenario stanford_identity --debug

# Verify fixes
python -c "
import json
with open('conversation_CONV-001-new-user-stanford-identity_[NEW_TIMESTAMP].json') as f:
    data = json.load(f)
    responses = [turn['agent_response'] for turn in data['conversation_turns']]
    print(f'Unique responses: {len(set(responses))}/{len(responses)}')
    print(f'User input referenced: {\"user\" in responses[1].lower()}')
"

# Run mini eval suite
python -c "
from essay_agent.eval.conversation_runner import ConversationRunner
runner = ConversationRunner()
results = runner.run_scenario('stanford_identity', debug=True)
print('SUCCESS: Conversation completed with unique responses')
"
```

## Success Criteria
After fixes, these should all be TRUE:
- [ ] Agent responses are unique across conversation turns
- [ ] Agent mentions user-provided details (name, school, major)
- [ ] Tools selected match conversation phase appropriately  
- [ ] Agent generates actual essay content when in drafting phase
- [ ] No identical response duplication in new evaluation runs

## Files Most Likely Needing Changes
Based on codebase structure:
- `essay_agent/eval/conversation_runner.py` - Core conversation logic
- `essay_agent/executor.py` - Agent execution and tool selection
- `essay_agent/cli.py` - Main conversation handling
- `essay_agent/agent/core/action_executor.py` - Tool execution
- `essay_agent/prompts/` - Response generation templates

## Debugging Commands
```bash
# Check for template files
find essay_agent/ -name "*.py" -exec grep -l "template\|static" {} \;

# Find response generation
grep -r "agent_response" essay_agent/ | head -10

# Check tool selection
grep -r "tools_used" essay_agent/ | head -10

# Look for caching
grep -r "cache\|store\|save" essay_agent/ | grep -v __pycache__
```

## Deliverables
1. **Fixed code** with clear commit messages for each bug
2. **Test results** showing the 4 bugs are resolved
3. **New conversation JSON** demonstrating unique, contextual responses
4. **Brief summary** of root causes and fix approaches

Remember: Focus on **evidence-based fixes** only. Each change should directly address the specific field/behavior problems documented in the evaluation analysis. 