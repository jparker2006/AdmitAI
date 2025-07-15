# Essay Agent – Tool Catalog

_Generated: 2025-07-15T11:52:04 UTC_


| Tool | Description | Phase(s) | Required Args | Return |
| --- | --- | --- | --- | --- |
| alignment_check | Analyze how well an essay addresses the specific prompt requirements. Returns alignment score and identifies missing aspects. | - | essay_text, essay_prompt | dict(ok/error) |
| brainstorm | Suggest 3 unique personal story ideas for a college essay given the essay prompt and user profile. | - | essay_prompt, profile | dict(ok/error) |
| check_consistency | Check an essay for tense, voice, and stylistic consistency and provide detailed analysis and fixes. | - | essay_text | dict(ok/error) |
| classify_prompt | Classify an essay prompt by its dominant theme and provide confidence scoring. | - | essay_prompt | dict(ok/error) |
| cliche_detection | Detect cliches in essay. | - | - | dict(ok/error) |
| comprehensive_validation | Run comprehensive validation pipeline. | - | - | dict(ok/error) |
| detect_overlap | Detect thematic or anecdotal overlap between a candidate story and previous essays. | - | story, previous_essays | dict(ok/error) |
| draft | Expand an outline into a complete first-person draft while preserving the user's voice. | - | outline, voice_profile | dict(ok/error) |
| echo | Enhanced echo tool that returns messages with conversational context and progress tracking. Useful for testing conversational workflows. | - | - | dict(ok/error) |
| enhance_vocabulary | Enhance vocabulary precision and strength in an essay while maintaining the student's authentic voice. | - | essay_text | dict(ok/error) |
| essay_scoring | Score a complete essay on the 5-dimension admissions rubric: clarity, insight, structure, voice, and prompt fit. Returns detailed scores (0-10 each) with overall assessment and feedback. | - | essay_text, essay_prompt | dict(ok/error) |
| expand_outline_section | Expand a single outline section into a vivid paragraph while preserving voice. | - | outline_section, section_name, voice_profile | dict(ok/error) |
| expand_story | Generate strategic follow-up questions to expand and develop a story seed. | - | story_seed | dict(ok/error) |
| extract_requirements | Extract explicit constraints and requirements from an essay prompt. | - | essay_prompt | dict(ok/error) |
| final_polish | Final polish validation. | - | - | dict(ok/error) |
| fix_grammar | Fix grammar, spelling, and style errors in an essay while preserving the student's authentic voice and meaning. | - | essay_text | dict(ok/error) |
| improve_opening | Improve an opening sentence to create a compelling hook while matching voice. | - | opening_sentence, essay_context, voice_profile | dict(ok/error) |
| length_optimizer | Redistribute word counts across outline sections to hit target length while maintaining balance. | - | outline, target_word_count | dict(ok/error) |
| match_story | Rate how well a specific story matches an essay prompt with detailed analysis. | - | story, essay_prompt | dict(ok/error) |
| optimize_word_count | Intelligently optimize essay word count to meet target requirements while preserving meaning and impact. | - | essay_text, target_words | dict(ok/error) |
| outline | Generate a structured five-part outline (hook, context, conflict, growth, reflection) for a given story idea. Returns strict JSON. | - | story, prompt | dict(ok/error) |
| outline_alignment | Check essay alignment with outline. | - | - | dict(ok/error) |
| outline_generator | Create a structured outline with hook, context, growth moment, and reflection sections with appropriate word count allocation. | - | story, essay_prompt | dict(ok/error) |
| plagiarism_check | Check essay for potential plagiarism. | - | - | dict(ok/error) |
| polish | Perform final grammar/style polish on a draft while enforcing an exact word count. | - | draft | dict(ok/error) |
| revise | Revise essay draft according to a targeted focus and return both the revised draft and a concise list of changes. | - | draft, revision_focus | dict(ok/error) |
| rewrite_paragraph | Rewrite an existing paragraph to match a specific stylistic instruction while preserving voice. | - | paragraph, style_instruction, voice_profile | dict(ok/error) |
| strengthen_voice | Adjust a paragraph to better match the user's authentic voice profile. | - | paragraph, voice_profile, target_voice_traits | dict(ok/error) |
| structure_validator | Evaluate an outline's structure, flow, and quality with detailed feedback and scoring. | - | outline | dict(ok/error) |
| suggest_stories | Generate 5 relevant personal story suggestions from user profile for essay prompt. | - | essay_prompt, profile | dict(ok/error) |
| suggest_strategy | Suggest a strategic approach for responding to an essay prompt based on user profile. | - | essay_prompt, profile | dict(ok/error) |
| transition_suggestion | Generate seamless transition sentences between outline sections: hook, context, growth moment, and reflection. | - | outline | dict(ok/error) |
| validate_uniqueness | Check if a story angle is unique and help avoid overused college essay clichés. | - | story_angle | dict(ok/error) |
| weakness_highlight | Analyze an essay to identify 3-5 specific weaknesses that most need improvement. Returns weak sections with explanations and actionable improvement advice. | - | essay_text | dict(ok/error) |
| word_count | Accurate word counting and validation tool using Python-based counting. | - | text | dict(ok/error) |
