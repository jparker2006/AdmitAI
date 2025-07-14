# 🏁 Essay Agent · Next-Phase 100× TODO List

**Mission**  Build the definitive “Cursor for College Essays” – a developer-friendly agent and toolkit that can brainstorm, draft, revise, and manage an entire portfolio of application essays with zero fine-tuning friction.

This file supersedes completed items in `todo.md` and focuses only on forward work.

---

## Phase 6.4b · CLI UX & Tool-Trace Enhancements  🖥️  (must finish **before** 6.5)

The current `essay-agent write` command runs the full workflow but hides which tools were invoked and with what arguments unless `--debug` is used.  Before we can build an evaluation harness we need a **developer-friendly CLI** that makes it obvious:

1. Which tool ran (brainstorm/outline/… or any micro-tool)
2. The arguments passed (trimmed for length)
3. Execution time per tool
4. Errors / retries explicitly printed

### Deliverables
| File | Change |
| --- | --- |
| `essay_agent/cli.py` | `--verbose` flag ⇒ stream per-tool logs while keeping JSON result intact.  Colourised for human mode (rich / colorama). |
|  | `--steps` flag ⇒ run a single step (e.g. only brainstorm) or resume from an intermediate phase. |
| `essay_agent/utils/logging.py` | helper `tool_trace()` for consistent formatted output. |
| `tests/unit/test_cli_verbose.py` | asserts that `--verbose` prints the expected tool banners. |

### Acceptance Criteria
* `essay-agent write -p "…" --verbose` prints banners like:
  ```
  ▶ brainstorm  …args
  ✔ brainstorm  0.42 s
  ▶ outline     …args
  …
  ```
* `essay-agent write --steps outline …` only executes planning→outline and exits.
* Human-mode coloured; `--json` remains clean JSON.

---

## Phase 6.5 · Evaluation Harness  ⚙️ (Highest Priority)
**Files**   `essay_agent/eval/`

| File | Purpose |
| --- | --- |
| `__init__.py` | Package exports & helpers |
| `sample_prompts.py` | 3-5 diverse prompts (challenge, identity, fun activity, etc.) |
| `metrics.py` | Word-count, JSON-schema, similarity & rubric scorers |
| `test_runs.py` | pytest entry – executes full workflow on each prompt |

**Deliverables**
1. Deterministic harness that runs each sample prompt through `EssayAgent.run()`.
2. Validates:
   • JSON shape of stories / outline / final draft  
   • Word count within ±5 % of target  
   • Draft addresses prompt keywords (simple BM25 check)  
   • No tool errors.
3. Produces `EvaluationReport` dataclass (pass/fail + metrics JSON).

**Acceptance Criteria**
`pytest essay_agent/eval/test_runs.py` exits 0 and prints summary table.

---

## Phase 7 · Critical Quality Fixes  🚨  (HIGHEST PRIORITY - Must Fix Before Production)

**Context**: First evaluation run revealed major content quality issues despite technical infrastructure working. The system produces functional essays but suffers from story selection bias, word count shortfall, and LLM prompt compliance problems.

**Root Problems**:
1. **Story Selection Bias**: System picks "robotics" for ALL prompt types (identity, passion, challenge)
2. **Word Count Adherence**: Consistently 10-35% under target (465/500, 526/800)
3. **LLM Prompt Following**: Despite stronger prompts, models ignore specific instructions

### 7.1 · College-Scoped Anti-Repetition & Story Diversification  🎯
**Files**: `essay_agent/tools/brainstorm.py`, `essay_agent/prompts/brainstorm.py`

| File | Change |
| --- | --- |
| `essay_agent/tools/brainstorm.py` | Add `college_id` parameter and `story_history_for_college()` method. Track stories per college, not globally. Allow reuse across colleges. |
| `essay_agent/prompts/brainstorm.py` | Update diversification prompt: "For {college_name}, avoid repeating stories from this application: {college_story_history}. You MAY reuse stories from other colleges if they fit well." |
| `essay_agent/memory/user_profile_schema.py` | Add `college_story_usage: Dict[str, List[str]]` to track which stories were used for which college applications. |

**Deliverables**:
1. **College-Scoped Exclusion**: `BrainstormTool.exclude_used_stories(college_id)` filters stories only within same college application
2. **Cross-College Reuse**: Allow users to reuse their best stories for different colleges when appropriate
3. **Prompt-Story Mapping**: Logic that maps prompt types to appropriate story categories:
   - Identity → heritage/family stories
   - Passion → creative/academic interests  
   - Challenge → failure/growth moments
4. **College-Aware Tracking**: Persistent log of story→college→prompt mappings in user profile
5. **Smart Diversification**: Prevent repetition within college, encourage reuse across colleges

**Example Usage**:
```python
# Same college - avoid repetition
brainstorm_tool.run(prompt="identity", college_id="harvard")  # Uses "Heritage story"
brainstorm_tool.run(prompt="passion", college_id="harvard")   # Uses "Creative writing" (different story)

# Different college - can reuse best stories
brainstorm_tool.run(prompt="identity", college_id="stanford") # Can use "Heritage story" again if it fits
```

### 7.2 · External Word Count Tool + Enforcement  📏
**Files**: `essay_agent/tools/word_count.py`, `essay_agent/tools/draft.py`, `essay_agent/prompts/draft.py`

| File | Change |
| --- | --- |
| `essay_agent/tools/word_count.py` | **NEW FILE**: Create dedicated word count tool with `count_words()`, `validate_target()`, `expand_text()`, and `trim_text()` methods. |
| `essay_agent/tools/draft.py` | Integrate `WordCountTool` with retry loop. Check actual word count with Python, not LLM. Max 3 attempts with smart expansion/trimming. |
| `essay_agent/prompts/draft.py` | Remove LLM word counting instructions. Focus on content quality. Add expansion/trimming prompts for retry attempts. |

**Deliverables**:
1. **External Word Count Tool**: Python-based accurate word counting using `len(text.split())` 
2. **Automatic Retry Loop**: Draft tool checks word count and regenerates if <90% of target
3. **Smart Expansion**: LLM prompted to expand specific sections when draft is too short
4. **Precise Trimming**: LLM prompted to trim content when draft is too long
5. **Guaranteed Accuracy**: Can achieve ≥95% word count success rate vs unreliable LLM counting

**Implementation Pattern**:
```python
@register_tool("word_count")
class WordCountTool:
    def count_words(self, text: str) -> int:
        return len(text.split())
    
    def validate_target(self, text: str, target: int, tolerance: float = 0.1) -> bool:
        count = self.count_words(text)
        return target * (1 - tolerance) <= count <= target * (1 + tolerance)
```

### 7.3 · Profile Balancing & Enhancement  👤
**Files**: `essay_agent/memory/user_profile_schema.py`, `essay_agent/eval/sample_prompts.py`

| File | Change |
| --- | --- |
| `essay_agent/memory/user_profile_schema.py` | Rebalance profile to have 3 EQUAL-weight defining moments instead of 1 dominant robotics story. Add `story_weight` field. |
| `essay_agent/eval/sample_prompts.py` | Add 2 more diverse test profiles with different dominant activities (arts, community service, athletics). |

**Deliverables**:
1. **Balanced Test Profiles**: 3 profiles with different dominant themes
2. **Equal Story Weights**: No single story dominates the profile
3. **Story Categorization**: Clear labels for identity/passion/challenge story types

### 7.4 · Enhanced Prompt Engineering  🧠
**Files**: `essay_agent/prompts/brainstorm.py`, `essay_agent/prompts/outline.py`, `essay_agent/prompts/draft.py`

| File | Change |
| --- | --- |
| `essay_agent/prompts/brainstorm.py` | Add **chain-of-thought** story selection: "First, identify the prompt type. Then, list 3 suitable stories. Finally, select the BEST match, avoiding {excluded_stories}." |
| `essay_agent/prompts/outline.py` | Add **structural constraints**: "Your outline must support exactly {target_words} words. Plan {num_paragraphs} paragraphs of ~{words_per_paragraph} words each." |
| `essay_agent/prompts/draft.py` | Add **output validation**: "Before submitting, count your words. If under {target_words}, expand sections. If over, trim carefully." |

**Deliverables**:
1. **Chain-of-Thought Selection**: Step-by-step story selection reasoning
2. **Structural Planning**: Word count built into outline structure
3. **Self-Validation**: LLM self-checks before output
4. **Prompt-Type Awareness**: Explicit recognition of prompt categories

### 7.5 · Evaluation Improvements  📊
**Files**: `essay_agent/eval/metrics.py`, `essay_agent/eval/test_runs.py`

| File | Change |
| --- | --- |
| `essay_agent/eval/metrics.py` | Add `story_diversity_score()` that penalizes repeated stories. Add `prompt_alignment_score()` for story-prompt fit. |
| `essay_agent/eval/test_runs.py` | Add multi-prompt test that verifies different stories are used for different prompt types. |

**Deliverables**:
1. **Diversity Metrics**: Quantitative score for story variety
2. **Alignment Scoring**: How well story matches prompt type
3. **Cross-Prompt Testing**: Verify no story repetition across multiple prompts

### Acceptance Criteria ✅
1. **College-Scoped Story Diversity**: Within same college application, 3 different prompts produce 3 different stories (0% repetition per college)
2. **Cross-College Story Reuse**: Same story can be reused across different colleges when appropriate
3. **Word Count**: ≥95% of target word count achieved on all test prompts
4. **Prompt Alignment**: Identity prompts use identity stories, passion prompts use passion stories
5. **Evaluation Pass Rate**: ≥80% of test prompts pass all metrics
6. **Speed Maintenance**: Fixes don't slow down execution >20%

### Priority Order  🎯
1. **7.1 Anti-Repetition** (blocks everything else)
2. **7.2 Word Count Enforcement** (most visible user impact)
3. **7.4 Enhanced Prompts** (supports all other fixes)
4. **7.3 Profile Balancing** (foundation for diversity)
5. **7.5 Evaluation Improvements** (measurement)
6. **7.6 Critical Bug Fixes** (immediate fixes for evaluation failures)
7. **7.7 Reliability Improvements** (short-term stability fixes)

### 7.6 · Critical Bug Fixes  🚨  (IMMEDIATE - Evaluation Blockers)
**Files**: `essay_agent/memory/user_profile_schema.py`, `essay_agent/tools/brainstorm.py`, `essay_agent/tools/draft.py`, `essay_agent/prompts/brainstorm.py`

**Context**: First evaluation run revealed critical bugs causing complete tool failures and persistent robotics story bias despite Phase 7 fixes.

**Root Problems**:
1. **Schema Mismatch**: User profile uses `story_category: 'passion'` but brainstorm tool expects `['creative', 'academic', 'intellectual', 'hobby']`
2. **Identity Prompt Complete Failure**: Draft tool returns 0 words and "No successful draft generated"
3. **LLM Prompt Compliance**: Despite stronger prompts, LLM still defaults to robotics stories

| File | Change |
| --- | --- |
| `essay_agent/memory/user_profile_schema.py` | Fix schema mismatch: Change `story_category` values to match brainstorm tool expectations. Map `passion` → `creative`, `identity` → `heritage`, `challenge` → `obstacle`, `achievement` → `accomplishment`. |
| `essay_agent/tools/brainstorm.py` | Update `_get_recommended_story_categories()` to use consistent schema. Add debug logging for story selection process. |
| `essay_agent/tools/draft.py` | Add comprehensive error handling and logging for identity prompt failures. Add retry logic for empty draft responses. |
| `essay_agent/prompts/brainstorm.py` | Strengthen anti-robotics bias instructions: "CRITICAL: Avoid technology/robotics stories unless prompt explicitly asks for technical interests. For identity prompts, focus on heritage/family. For passion prompts, explore creative/artistic interests." |

**Deliverables**:
1. **Schema Alignment**: Consistent story categorization across all components
2. **Draft Tool Reliability**: Zero complete failures on any prompt type
3. **Story Selection Debugging**: Detailed logging to understand LLM choices
4. **Anti-Robotics Enforcement**: Explicit prompt instructions preventing robotics bias

### 7.7 · Reliability Improvements  🔧  (SHORT-TERM - Quality & Stability)
**Files**: `essay_agent/eval/metrics.py`, `essay_agent/prompts/draft.py`, `essay_agent/tools/brainstorm.py`, `essay_agent/tools/outline.py`

**Context**: Address remaining evaluation failures and improve overall system reliability.

**Root Problems**:
1. **Low Keyword Similarity**: Essays don't address prompt keywords effectively (0.000-0.214 vs target ≥0.3)
2. **Incomplete College Scoping**: College-aware logic may not be working correctly  
3. **Insufficient Error Debugging**: Hard to diagnose why tools fail without better logging

| File | Change |
| --- | --- |
| `essay_agent/eval/metrics.py` | Add `keyword_similarity_debug()` that shows which keywords are missing. Add `prompt_alignment_detailed()` for granular prompt-story fit analysis. |
| `essay_agent/prompts/draft.py` | Add keyword integration requirements: "Your essay MUST explicitly address these key terms from the prompt: {extracted_keywords}. Weave them naturally into your narrative." |
| `essay_agent/tools/brainstorm.py` | Add college ID verification logging. Ensure `college_id` parameter is properly passed and used in all story selection logic. |
| `essay_agent/tools/outline.py` | Add keyword planning: Extract key terms from prompt and ensure outline structure supports addressing them. |

**Deliverables**:
1. **Keyword Compliance**: Essays systematically address prompt keywords (≥0.3 similarity score)
2. **College Scoping Verification**: Confirm college-aware story selection works correctly
3. **Enhanced Error Debugging**: Detailed logs for tool failures and story selection decisions
4. **Prompt-Story Alignment**: Better matching between prompt types and selected stories

**Acceptance Criteria** ✅
1. **Zero Complete Failures**: All tools return valid results for all prompt types
2. **Schema Consistency**: All components use aligned story categorization
3. **Keyword Coverage**: ≥0.3 similarity score for all prompts
4. **Story Selection Debugging**: Clear logs showing why each story was chosen
5. **Evaluation Pass Rate**: ≥70% after 7.6, ≥80% after 7.7

---

## Phase 8 · LangGraph Workflow & Multi-Essay Orchestration

### 8.1 EssayWorkflow Engine  🗺️
**Files**  `essay_agent/workflows/essay_workflow.py`

• Build StateGraph that mirrors Phase list but supports *branching* and *loops* (e.g., Revise→Polish→Evaluate→Revise).  
• Node types: `ToolCall`, `Evaluation`, `Decision`.

Tests: workflow progression, conditional edges, error retry.

### 8.2 Revision & Feedback Loops  🔄
• Auto-loop until rubric ≥ 8/10 or max 3 iterations.  
• Integrate `evaluation_tools.EssayScoringTool`.

### 8.3 Portfolio Manager  📚
• Track many prompts per user, enforce story reuse rules, deadline sorting.  
• API: `PortfolioManager.submit(prompt, profile)` → returns task-id.

### 8.4 QA Workflow  ✅
• Multi-stage validation: plagiarism check, cliche detector, outline-fit, final polish.

---

## Phase 5.2 – 5.4 · Advanced Memory & Retrieval  (parallel)
1. `memory/semantic_search.py` – FAISS/Chroma vector store.  
2. `memory/context_manager.py` – token-aware truncation & summarisation.  
3. `memory/rag.py` – Retrieval-Augmented Generation for personal memories.

---

## Phase 12 · Fine-Tuning & Cost Optimisation
1. Data capture pipeline → S3.  
2. Fine-tune OpenAI or local models per tool.  
3. A/B harness comparing prompt vs fine-tuned.

---

## Continuous Quality Gates
* > 90 % unit coverage (pytest-cov)
* `mypy --strict` clean
* Formatters & linters: `black`, `ruff`, `pylint`
* CI matrix: macOS, Linux, Python 3.10-3.12

### Quick Commands
```bash
pytest                # full test suite
pytest -m eval        # only evaluation harness
pytest essay_agent/eval/test_runs.py -v   # detailed eval run
mypy essay_agent/     # static types
black essay_agent/    # autoformat
essay-agent write -p "Prompt" --verbose   # human trace with tool tracing
essay-agent tool brainstorm --kwargs '{"essay_prompt": "…", "profile": "{}"}'
# Phase 7 testing commands:
essay-agent write -p "Identity prompt" --json | jq '.selected_story'  # check story selection
essay-agent write -p "Passion prompt" --json | jq '.final_draft | length'  # check word count
```

---

*Update this file at the end of every working session.*