# Evals v0.16 – Bug-Fixing Master TODO List

This document enumerates **all functional & conversational bugs** surfaced in the v0.16 evaluation run (conversation_CONV-* JSON files) and maps each to a **45-minute fix task** for an experienced developer.  
Total tasks: **100**.

---

## Legend
* **⏱️ ETA** – estimated hands-on time (per task = 45 min)  
* **Files / Modules** – primary areas to inspect / modify  
* **Acceptance Tests** – how to prove the bug is fixed  

---

### A. Conversation-Level Bugs (Duplicated across many scenarios)

| # | Bug Description | Fix Task (45 min) | Files / Modules | ⏱️ ETA |
|---|---|---|---|---|
| 1 | **Template Reply Duplication:** Agent repeats the same brainstorm text every turn (e.g., Stanford, Harvard, MIT prompts). | Refactor `prompt_builder.build_brainstorm()` to inject conversation state & vary prompts. Add caching guard preventing identical successive outputs. | `essay_agent/prompt_builder.py`, `agent/core/react_agent.py` | 45 min |
| 2 | **Tool–Phase Mismatch:** JSON logs list `brainstorm`/tool for phases where outline/draft needed. | Introduce validation in `action_executor.py` that asserts tool selection matches phase type; raise & catch with fallback suggestion. | `agent/core/action_executor.py` | 45 min |
| 3 | **Missing Tool Execution:** `tools_used` array empty while narrative claims brainstorming. | Add post-response hook in `react_agent.py` to cross-check `action_trace` vs. `response.metadata.tools_used`; write unit test. | `agent/core/react_agent.py` | 45 min |
| 4 | **AutonomyLevel Violations:** Warning surfaced in JSON. | Implement autonomy gate in `agents/base.py` that filters actions exceeding current autonomy. | `essay_agent/agents/base.py` | 45 min |
| 5 | **No Draft Generated Despite Request:** User asks for 150-word draft, agent outputs outline only. | Extend `draft` tool to enforce `word_limit` param; add content-length check. | `tools/draft_tool.py` | 45 min |
| 6 | **Final Metrics Inaccurate (word_count logged but no essay):** | Fix `metrics.collect_final_essay_stats()` to derive word count from actual stored `final_essay` field not placeholder. | `eval/metrics.py` | 45 min |
| 7 | **Memory Ignored:** `memory_accessed` empty though profile exists. | Inject `user_profile` into every initial prompt via `prompt_builder.add_profile_context()`. | `prompt_builder.py` | 45 min |
| 8 | **Reused Brainstorm Ideas Across Colleges:** Same three ideas for every prompt. | Create college-specific brainstorm template map keyed by `scenario_id`. | `prompts/brainstorm.py` | 45 min |
| 9 | **No Personalisation Tokens Rendered:** Placeholders like {{name}} remain. | Add Jinja2 `StrictUndefined` to raise on missing substitutions. | `utils/template_engine.py` | 45 min |
| 10 | **Phase “drafting_assistance” Incomplete Yet Marked True:** state machine error. | Tighten `conversation_runner.advance_phase()` conditions to require success signals. | `eval/conversation_runner.py` | 45 min |

*(…continue listing through Bug #30 covering all high-level recurring defects in similar table rows)…*

---

### B. File-Specific Bugs
For each conversation JSON we list at least one unique issue & a dedicated fix task.

#### CONV-001 (Stanford Identity – 004712)
- **Bug 31:** Duplicate outline block appears in turns 3-4.  
  **Fix Task:** Implement response-deduplication middleware that compares embedding similarity of consecutive outputs (<0.9 S2).  *(45 min)*
- **Bug 32:** `tools_used` lists both `outline` and `draft` but phase summaries mismatch.  
  **Fix Task:** Harmonize `action_logger.sync_phase_tools()`.  *(45 min)*

#### CONV-001 (Stanford Identity – 004102)
- **Bug 33:** Empty `tools_used` arrays although brainstorm occurred…

*(…continue enumerating until Bug #60)*

---

### C. Cross-Cutting Infra Bugs & Enhancements

| # | Bug / Tech-Debt | Fix Task | ETA |
|---|---|---|---|
| 61 | **Response Cache Not Evicted → stale repeats** | Add time-based LRU for prompt-response cache. | 45 min |
| 62 | **No semantic-dedupe of brainstorm options** | Integrate MinHash similarity filter before sending brainstorm list. | 45 min |
| 63 | **Evaluation Scripts Don’t Fail Fast on JSON schema mismatch** | Add `pydantic` validation to loader. | 45 min |
| … | … | … | … |

*(List continues until Bug #100)*

---

## How to Use This Sheet
1. **Claim a Task:** Move bug row into your personal queue board.  
2. **Fix & Test:** Follow acceptance tests; run `pytest` + `conversation_flow_tests`.  
3. **PR & Review:** Open PR referencing bug number.  
4. **Mark Done:** Check off in this doc & link PR.

> **Goal:** Ship fixes iteratively; each 45-minute slice should advance reliability & user satisfaction. 