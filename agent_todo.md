# 🛠️ AdmitAI Unified Essay-Agent – Implementation Checklist

> Follow the tasks **in order**.  Each item unblocks the next.  Tick ☑️ when complete and run the referenced test.

---

## Phase 0 – Environment & Baseline
- [x] P0-01 Create/activate Python 3.11 virtualenv, `pip install -r requirements.txt`  
  • Test → `pytest -q` should collect tests (failures OK).
- [x] P0-02 Set `ESSAY_AGENT_OFFLINE_TEST=1` in your shell/profile for deterministic local testing.  
  • Test → `pytest -q tests/unit/test_tool_serialization.py::test_offline_stub`.

---

## Phase 1 – Tool Serialization & Reliability (blocks every higher phase)
1. [x] TP-63 Cursor-style tools (`modify_ / explain_ / improve_ / rewrite_ / expand_ / condense_ / replace_selection`) must return dict (`.model_dump()`).  
   • Test → `pytest -q tests/unit/test_selection_serialization.py`.
2. [x] TP-77 Real-time stub tools (`smart_autocomplete … strategy_advisor`) return dict.  
   • Test → same file above.
3. [x] TP-07 `essay_scoring` uses `.model_dump()`; verify field types.  
   • Test → `pytest -q tests/unit/test_tool_serialization.py::test_essay_scoring_serializable`.
4. [x] TP-55 `plagiarism_check` wrapper returns `result.model_dump()`.  
   • Test → `pytest -q tests/unit/test_tool_serialization.py::test_plagiarism_check_serializable`.
5. [x] TP-01 `expand_outline_section` serialization fix.  
6. [x] TP-03 `improve_opening` serialization fix.
7. [x] TP-05 `strengthen_voice` serialization fix.
8. [x] TP-09 `weakness_highlight` serialization fix.
9. [x] TP-11 `cliche_detection` serialization fix.
10. [x] TP-13 `alignment_check` serialization fix.
11. [x] TP-15 `draft` tool returns dict.  
12. [x] TP-17 `polish` tool returns dict.  
13. [x] TP-19 `word_count` returns dict & nested models dumped.  
14. [x] TP-21 `revise` returns dict with `changes` list.  
15. [x] TP-23 `outline_generator` serialization.  
16. [x] TP-25 `structure_validator` serialization.  
17. [x] TP-27 `transition_suggestion` serialization.  
18. [x] TP-29 `length_optimizer` serialization.  
19. [x] TP-31 `classify_prompt` serialization.  
20. [x] TP-33 `extract_requirements` serialization.  
21. [x] TP-35 `suggest_strategy` serialization.
22. [x] TP-37 `detect_overlap` serialization.
23. [x] TP-39 `suggest_stories` serialization.
24. [x] TP-41 `match_story` serialization.
25. [x] TP-43 `expand_story` serialization.
26. [x] TP-45 `validate_uniqueness` serialization.  
27. [x] TP-47 `fix_grammar` serialization.  
28. [x] TP-49 `enhance_vocabulary` serialization.  
29. [x] TP-51 `check_consistency` serialization.  
30. [x] TP-53 `optimize_word_count` serialization.  
31. [x] TP-57 `outline_alignment` serialization.  
32. [x] TP-59 `final_polish` serialization.  
33. [x] TP-61 `comprehensive_validation` serialization.  
   • Test after #33 → `ESSAY_AGENT_OFFLINE_TEST=1 python -m essay_agent.eval.comprehensive_test --category tools` should report **54 / 54** tools PASS.

---

## Phase 2 – Conversation Naturalness
34. [x] CN-81 Create `agents/response_enhancer.py` – ResponseEnhancer post-processor.  
35. [x] CN-82 Add empathetic prompt template in `prompts/response_enhancer.py`.  
36. [x] CN-83 Wire enhancer into `AutonomousEssayAgent.handle_message`.  
37. [ ] CN-84 Unit test positive-tone injection.  
38. [x] CN-85 Offline stub returns unchanged text.  
39. [ ] CN-86 Test stub path.  
40. [ ] CN-87 Add `politeness_level` setting.  
41. [ ] CN-88 Test levels 0-2 mapping.  
42. [ ] CN-89 Implement small-talk deflection.  
43. [ ] CN-90 Test deflection logic.

---

## Phase 3 – Essay-Flow Enhancements
44. [x] EF-91 Refactor `cli.py` – prompt user for `college` & `essay_prompt` *before* chat loop.  
45. [x] EF-92 Add `prompt_validator` ensuring ≤650 words.  
46. [x] EF-93 Update `SmartOrchestrator` auto-starts brainstorm→outline.  
47. [x] EF-94 Integration test: offline full flow.  
48. [x] EF-95 Persist chosen college in `AgentMemory`.  
49. [x] EF-96 Unit test: college context injection.  
50. [ ] EF-97 Implement resume-workflow capability.  
51. [ ] EF-98 Test resume after memory save.  
52. [ ] EF-99 Update CLI `--help` text.  
53. [ ] EF-100 Test updated help.

### Cursor Tool Prompt Enhancements (Phase-3 add-on)
54. [ ] CP-101 Create Jinja prompt templates for each cursor-style tool (`modify_ / explain_ / improve_ / rewrite_ / expand_ / condense_ / replace_selection`).
55. [ ] CP-102 Refactor `essay_agent/tools/text_selection.py` to load and render these templates via `prompts/cursor/` directory.
56. [ ] CP-103 Unit tests: ensure each cursor tool renders prompt with required variables and still returns JSON-serialisable dict in offline mode.

### System Diagram (post-Phase-3)
57. [ ] DIAG-201 Generate a Mermaid diagram covering all prompts, tools, agents, workflows, and data stores.

---

## Phase 4 – Usability & Prompt-Transparency  🔥

101. [ ] U4-01 Unified LLM Planner Prompt  
    • Replace BulletproofReasoning with *PlannerPrompt*: one GPT-call that returns an ordered `plan` array (tool + args) based on full context.  
    • Prompt must include: essay_status, 3-turn working memory, profile extras, available tool list (names only).  

102. [ ] U4-02 Plan Executor & Arg-Autofill  
    • Extend SmartOrchestrator to accept the whole `plan` list.  
    • Create `utils/default_args.py::autofill_args(step, context, memory)` to fill any missing `story`, `prompt`, `outline`, `word_limit`, etc. *No hard-coded fallbacks beyond autofill*.  

103. [ ] U4-03 Conversation-as-Tool  
    • Register `chat_response` tool (wraps GPT answer).  
    • If planner returns an empty plan, Orchestrator calls `chat_response`. Thus every turn still passes through the registry without deterministic mapping.  

104. [ ] U4-04 Prompt Inspector  
    • Global CLI flag `--show-prompts` prints: 1) system+user planner prompt, 2) raw JSON plan.  
    • Redact any PII beyond memory fields. Add unit test.  

105. [ ] U4-05 Rich Formatter & Streaming  
    • brainstorm → numbered list, outline → nested bullets, validator results → ✅/⚠️ table, draft → full text.  
    • Stream each step’s formatted output as soon as the tool finishes. Unit tests for each formatter.  

106. [ ] U4-06 Memory Snapshot Injection  
    • Ensure planner prompt and `autofill_args` include recent chat + profile so tools reference prior dialogue (“As we discussed earlier…”).  

107. [ ] U4-07 Tool Help & Autocomplete  
    • Update `help` command to list all tools with examples; implement tab-completion for tool prefixes in CLI chat.  

108. [ ] U4-08 End-to-End Smoke Test  
    • Integration test: onboarding → user asks free-form; planner returns brainstorm → outline → draft plan; each step produces non-empty output; essay_status advances to `draft` in ≤3 turns.  

109. [ ] U4-09 Performance Guardrails  
    • Parallelise independent validator calls; cap latency per turn at 60 s (with retries).  
    • Log per-tool latency in SmartMemory.tool_stats.  

110. [ ] U4-10 Documentation & Demo Script  
    • Update README with architecture diagram + `demo_live.sh` that runs a live session with `--show-prompts`.

111. [ ] U4-11 Tool-Coverage Validator  
    • New test iterates over `TOOL_REGISTRY.keys()`; for each tool constructs a minimal user request (`"<tool_name>: test"`).  
    • Confirms PlannerPrompt JSON includes that tool and SmartOrchestrator executes it (offline stub acceptable).  
    • CI fails if any registered tool cannot be selected or executed.

### Success Metrics (Phase 4)
• 100 % of user turns execute at least one tool.  
• Draft produced in ≤3 turns with no manual arg hacks.  
• `--show-prompts` reveals clean JSON-only interchange.  
• Integration flow test passes offline and live.

---

## Phase 4 – Final Integration & QA
54. [ ] Run `pytest -q` (all suites) in **offline** then **online** mode.  
55. [ ] Run `essay-agent eval-suite --category new_user --count 5` (online).  
56. [ ] Ensure `comprehensive_test --run-all` passes ≥ 98 %.
57. [ ] Update documentation and bump version.

---

## Phase 5 – Planner Autonomy & Tool Diversity  🧠

112. [ ] P5-01 **Comprehensive Arg-Autofill**  
    • Extend `utils/default_args.py` so EVERY registered tool has a rule that fills the required args from context or memory.  
    • Test → new `tests/unit/test_autofill_completeness.py` iterates over `TOOL_REGISTRY` and asserts `autofill_args` returns all required kwargs.

113. [ ] P5-02 **Richer Few-Shot Library**  
    • Add at least 8 diverse examples to `prompts/planner/100x_planner_prompt.txt` covering grammar-fix, word-count optimisation, section rewrite, validator usage, etc.  
    • Unit test ensures template renders and contains all new examples.

114. [ ] P5-03 **Dynamic Temperature Control**  
    • Expose `PLANNER_TEMPERATURE` env-var; default 0.3, allow 0.0-1.0.  
    • Update `PlannerPrompt` wrapper to read it; add CLI `--creative` flag that sets 0.7.

115. [ ] P5-04 **Tool-Success Feedback Loop**  
    • SmartOrchestrator records success stats (already tracked) and injects a summary line into the planner prompt, e.g. `tool_stats: brainstorm(success=5/6), outline(3/3)…`.  
    • Planner examples updated to show how to use this signal.

116. [ ] P5-05 **Diversity Integration Tests**  
    • New test fires 10 varied user prompts and asserts >60 % of turns choose a tool OTHER than brainstorm/outline/draft.  
    • Fails CI if diversity threshold not met.

### Success Metrics (Phase 5)
• Planner selects ≥ 15 different tools across a 50-scenario eval-suite.  
• Arg-autofill returns 100 % required parameters (no runtime `TypeError`).  
• Average turn latency ≤ 60 s online.  
• Diversity integration test passes.

---

## Phase 6 – Intelligent Argument Resolution  🧩

Goal: Eliminate hard-coded parameter construction by introspecting each tool’s `_run` signature and/or Pydantic input model so the orchestrator can always supply the right kwargs.

### Core Idea
1. Build an `arg_spec` catalog for every registered tool at import time (required vs optional fields).  
2. Implement a generic `ArgResolver` that, for each required arg, searches planner-provided `tool_args`, context snapshot, user profile / memory, and user message (in that order).  
3. Plug the resolver into `SmartOrchestrator.execute_plan`, deprecating manual `build_params()` mappings except for legacy edge-cases.

### Tasks
117. [ ] P6-01 **Tool Introspection Utility**  
    • Create `essay_agent/tools/tool_introspection.py` that iterates over `TOOL_REGISTRY` and produces `TOOL_ARG_SPEC` dict via `inspect.signature` + Pydantic hints.  
    • Unit test verifies at least 95 % of tools expose ≥1 required/optional arg in the spec.

118. [ ] P6-02 **Generic ArgResolver**  
    • Add `utils/arg_resolver.py::ArgResolver.resolve(tool_name, context, planner_args, user_input)` implementing the search order + type coercion.  
    • Include detailed logging when `ESSAY_AGENT_SHOW_ARGS=1`.

119. [ ] P6-03 **Orchestrator Integration**  
    • Refactor `SmartOrchestrator.execute_plan` to use `ArgResolver` instead of `build_params()`.  
    • Maintain backwards compatibility for manual overrides via an optional `MANUAL_ARG_OVERRIDES` mapping.

120. [ ] P6-04 **Docstring Fallback Parser**  
    • When introspection yields zero required args, parse the tool docstring “Args:” section as a last resort.  
    • Extend unit test from P6-01 to cover a docstring-only tool.

121. [ ] P6-05 **Completeness & Regression Tests**  
    • New test `tests/unit/test_arg_resolver_completeness.py` iterates over all tools and asserts `ArgResolver.resolve()` returns all required kwargs when provided with a synthetic context containing canonical keys (essay_prompt, profile, outline, etc.).

### Success Metrics (Phase 6)
• 100 % of tools execute without `TypeError` due to missing kwargs in full eval-suite.  
• Resolver fills ≥90 % of required args from context without manual overrides.  
• `ESSAY_AGENT_SHOW_ARGS=1` clearly logs the source of every filled arg.  
• Avg. turn latency increases ≤5 % vs Phase 5.

---

## Phase 7 – Output-Reliability Layer  📊

Goal: Ensure every tool returns strict, machine-readable JSON by combining example-driven prompts (high compliance) with a universal GPT repair pass (edge cases).

### Core Components
1. Example-First Prompts – inject a minimal, realistic JSON example into each tool’s prompt right after its `<output_schema>`.
2. Schema-Aware Self-Repair – generic helper that re-asks GPT-3.5 to fix malformed JSON using the tool’s schema.
3. Post-Repair Validation – re-run Pydantic parse; if still missing keys fall back to a tool-specific stub.
4. Telemetry – track how often repair and fallback are used; surface metrics at agent shutdown.

### Tasks
122. [ ] P7-01 **Prompt Example Injector**  
    • Add `prompts/templates.py::inject_example()` + `EXAMPLE_REGISTRY`.  
    • Populate realistic one-record example for all tools; unit test prompt contains example ≤600 tokens.

123. [ ] P7-02 **Schema-Aware Repair Helper**  
    • Create `utils/json_repair.py::fix(raw, schema)`; centralise repair logic; update `ValidatedTool` to call it.  
    • Remove duplicated repair code; add `SHOW_REPAIR_RAW` flag.

124. [ ] P7-03 **Complete Example Registry**  
    • Add a concise one-record JSON example for *every* tool in `EXAMPLE_REGISTRY`; use correct wrapper and keys per schema.  
    • Unit test verifies `EXAMPLE_REGISTRY` has an entry for every `TOOL_ARG_SPEC` key and each example is ≤250 chars.

125. [ ] P7-04.1 **Prompt Wiring – Phase 1**  
    • Ensure **every** tool prompt module wraps its raw template with `inject_example()` so the `<example_output>` block is always included.  
    • Create minimal prompt modules for tools that currently build prompts inline.  
    • Unit test scans all modules in `essay_agent/prompts/` and asserts the rendered prompt contains `<example_output>` and is ≤650 tokens.

126. [ ] P7-04.2 **Example Expansion – Phase 2**  
    • Replace generic stub strings in `EXAMPLE_REGISTRY` with realistic, schema-correct examples for all of the tools. We can do this in batches of 5-10
    • Keep each example ≤250 chars.  
    • Unit test fails if any registry value still matches the pattern `"stub for "`.

### Success Metrics (Phase 7)
• Valid structured output on first parse ≥90 %.  
• Repair routine fixes remaining ≤10 % with one extra LLM call.  
• Fallback invoked <1 % of executions in test suite.  
• Added latency per turn ≤10 %.

---

## 🔑 Quick-Start Guide
Make progress in **bite-sized, five-task chunks**:
1. Locate the next UNTICKED item(s) in the list below.
2. Copy the *Implementation Prompt* (template at bottom).
3. Replace the placeholders with the chosen 5 task IDs (e.g. TP-63, TP-77…).
4. Paste the prompt into Cursor / ChatGPT and follow the generated diff.
5. Run the referenced test(s); commit if green.

> ⚠️  Tip: Never mix tasks from different phases in one chunk—always finish open serialization fixes before moving to Conversation Naturalness.

---

### 🧑‍💻 Implementation Prompt Template
```
You are ChatGPT acting as a senior Python engineer on AdmitAI.
Complete the following task IDs in order: <TASK_ID_1>, <TASK_ID_2>, …

For EACH task:
• Show the file(s) to edit/create.
• Provide a concise code diff (no commentary between lines).
• Include unit-test changes if specified.

Constraints:
• Must pass `ESSAY_AGENT_OFFLINE_TEST=1 pytest -q`.
• Follow existing coding style & @register_tool patterns.
• Return only the code diff blocks.
```

### How to Use This File
1. Work strictly top-to-bottom; do not skip items (dependencies!).  
2. After each checkbox, commit with message `complete <ID> – <summary>`.  
3. Keep `ESSAY_AGENT_OFFLINE_TEST=1` for rapid local loops; switch off only for GPT-backed smoke tests at Phase 4. 