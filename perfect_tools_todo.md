## Perfect Tools Prompt Audit TODO

> Goal: For every tool that relies on a dedicated Jinja/`make_prompt` template, trim token-bloat, document required args, and verify end-to-end execution from Planner → Orchestrator → Tool.  
> Mark each sub-task when complete. (~36 tools total)

| # | Tool | Prompt Constant / File | Tasks |
|---|------|------------------------|-------|
| 1 | brainstorm | `BRAINSTORM_PROMPT` – `prompts/brainstorm.py` | [x] Shrink prompt <400 tok  [x] List args (`essay_prompt`, `profile`)  [x] Live test |
| 2 | brainstorm_specific | reuses brainstorm helper | [x] Ensure helper prompt concise  [x] Args (`topic`, `user_input`)  [x] Test |
| 3 | suggest_stories | `STORY_SUGGESTION_PROMPT` – `prompts/brainstorming.py` | [x] Trim prompt  [x] Args (`essay_prompt`, `profile`)  [x] JSON-mode test |
| 4 | match_story | `STORY_MATCHING_PROMPT` | [x] Trim prompt  [x] Args (`story`, `essay_prompt`)  [x] JSON-mode test |
| 5 | expand_story | `STORY_EXPANSION_PROMPT` | [x] Trim prompt  [x] Args (`story_seed`)  [x] JSON-mode test |
| 6 | validate_uniqueness | `UNIQUENESS_VALIDATION_PROMPT` | [x] Trim prompt  [x] Args (`story_angle`, `previous_essays`)  [x] JSON-mode test |
| 7 | story_development | internal mini-prompt | [ x] Ensure concise  [x ] Args (`story`)  [ ] Test |
| 8 | story_themes | `STORY_THEMES_PROMPT` – `prompts/brainstorming.py` | [x] Trim prompt  [x] Args (`story`)  [x] JSON-mode test |
| 9 | outline | `OUTLINE_PROMPT` – `prompts/outline.py` | [x] Trim prompt  [x] Args (`story`,`prompt`,`word_count`)  [x] JSON-mode test |
|10 | outline_generator | `OUTLINE_GENERATOR_PROMPT` – `prompts/structure.py` | [x] Trim prompt  [x] Args (`story`,`essay_prompt`,`word_count`)  [x] JSON-mode test |
|11 | structure_validator | `STRUCTURE_VALIDATOR_PROMPT` – `prompts/structure.py` | [x] Trim prompt  [x] Args (`outline`)  [x] JSON-mode test |
|12 | transition_suggestion | `TRANSITION_SUGGESTION_PROMPT` – `prompts/structure.py` | [x] Trim prompt  [x] Args (`outline`)  [x] JSON-mode test |
|13 | length_optimizer | `LENGTH_OPTIMIZER_PROMPT` – `prompts/structure.py` | [x] Trim prompt  [x] Args (`outline`,`target_word_count`)  [x] JSON-mode test |
|14 | outline_alignment | `OUTLINE_ALIGNMENT_PROMPT` – `prompts/validation.py` | [x] Trim prompt  [x] Args (`essay_text`,`outline`,`context`)  [x] JSON-mode test |
|15 | alignment_check | `ALIGNMENT_CHECK_PROMPT` – `prompts/evaluation.py` | [x] Trim prompt  [x] Args (`essay_text`,`essay_prompt`)  [x] JSON-mode test |
|16 | draft | `DRAFT_PROMPT` – `prompts/draft.py` | [x] Trim prompt  [x] Args (`outline`,`voice_profile`,`extracted_keywords`,`word_count`)  [x] JSON-mode test |
|17 | revise | `REVISION_PROMPT` – `prompts/revision.py` | [x] Trim prompt  [x] Args (`draft`,`revision_focus`)  [x] JSON-mode test |
|18 | polish | `POLISH_PROMPT` – `prompts/polish.py` | [x] Trim prompt  [x] Args (`draft`,`word_count`)  [x] JSON-mode test |
|19 | final_polish | `FINAL_POLISH_PROMPT` – `prompts/validation.py` | [x] Trim prompt  [x] Args (`essay_text`,`context`)  [x] JSON-mode test |
|20 | fix_grammar | `GRAMMAR_FIX_PROMPT` – `prompts/polish.py` | [x] Trim prompt  [x] Args (`essay_text`)  [x] JSON-mode test |
|21 | enhance_vocabulary | `VOCABULARY_ENHANCEMENT_PROMPT` – `prompts/polish.py` | [x] Trim prompt  [x] Args (`essay_text`)  [x] JSON-mode test |
|22 | check_consistency | `CONSISTENCY_CHECK_PROMPT` – `prompts/polish.py` | [x] Trim prompt  [x] Args (`essay_text`)  [x] JSON-mode test |
|23 | cliche_detection | `CLICHE_DETECTION_PROMPT` – `prompts/evaluation.py` | [x] Trim prompt  [x] Args (`essay_text`)  [x] JSON-mode test |
|24 | plagiarism_check | `PLAGIARISM_DETECTION_PROMPT` – `prompts/validation.py` | [x] Trim prompt  [x] Args (`essay_text`)  [x] JSON-mode test |
|25 | essay_scoring | `ESSAY_SCORING_PROMPT` – `prompts/evaluation.py` | [x] Trim prompt  [x] Args (`essay_text`,`essay_prompt`)  [x] JSON-mode test |
|26 | weakness_highlight | `WEAKNESS_HIGHLIGHT_PROMPT` – `prompts/evaluation.py` | [x] Trim prompt  [x] Args (`essay_text`)  [x] JSON-mode test |
|27 | classify_prompt | `CLASSIFY_PROMPT_PROMPT` – `prompts/evaluation.py` | [x] Trim prompt  [x] Args (`essay_prompt`)  [x] JSON-mode test |
|28 | extract_requirements | `EXTRACT_REQUIREMENTS_PROMPT` | [x] Trim prompt [x] List args (`essay_prompt`) [x] JSON-mode test |
|29 | suggest_strategy | `SUGGEST_STRATEGY_PROMPT` | [x] Trim prompt [x] List args (`essay_prompt`, `profile`) [x] JSON-mode test |
|30 | detect_overlap | `DETECT_OVERLAP_PROMPT` | [x] Trim prompt [x] List args (`story`, `previous_essays`) [x] JSON-mode test |
|31 | expand_outline_section | `OUTLINE_EXPANSION_PROMPT` – `prompts/writing.py` | [x] Trim prompt [x] List args (`outline_section`, `section_name`, `voice_profile`, `target_words`) [x] JSON-mode test |
|32 | rewrite_paragraph | `PARAGRAPH_REWRITE_PROMPT` | [x] Trim prompt [x] List args (`paragraph`, `style_instruction`, `voice_profile`) [x] JSON-mode test |
|33 | improve_opening | `OPENING_IMPROVEMENT_PROMPT` | [x] Trim prompt [x] List args (`opening_sentence`, `essay_context`, `voice_profile`) [x] JSON-mode test |
|34 | strengthen_voice | `VOICE_STRENGTHENING_PROMPT` | [x] Trim prompt [x] List args (`paragraph`, `voice_profile`, `target_voice_traits`) [x] JSON-mode test |
|35 | clarify | `CLARIFY_PROMPT` – `prompts/query_rewrite.py` | [x] Trim prompt [x] List args (`user_input`, `context`) [x] JSON-mode test |
|36 | compress / condense_selection | `COMPRESS_PROMPT` | [ ] … |
|37|modify_selection|Cursor tool – prompt to create|[x] Jinja template [x] Args (`selection`,`instruction`, `surrounding_context`) [x] Test|
|38|explain_selection|Cursor tool – prompt to create|[x] Jinja template [x] Args (`selection`, `surrounding_context`) [x] Test|
|39|improve_selection|Cursor tool – prompt to create|[x] Jinja template [x] Args (`selection`, `surrounding_context`) [x] Test|
|40|rewrite_selection|Cursor tool – prompt to create|[x] Jinja template [x] Args (`selection`, `instruction`, `surrounding_context`) [x] Test|
|41|expand_selection|Cursor tool – prompt to create|[x] Jinja template [x] Args (`selection`, `surrounding_context`) [x] Test|
|42|condense_selection|Cursor tool – prompt to create|[x] Jinja template [x] Args (`selection`, `surrounding_context`) [x] Test|
|43|replace_selection|Cursor tool – prompt to create|[x] Jinja template [x] Args (`selection`, `surrounding_context`) [x] Test|
|44|smart_autocomplete|Real-time cursor tool|[x] Jinja template [x] Args (`text_before_cursor`, `surrounding_context`) [x] Test|