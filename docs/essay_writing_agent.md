# College Essay Writing Agent: Engineering Spec

## 🧠 System Overview

The College Essay Writing Agent is a standalone, agentic writing coach that guides students through the complete college admissions essay process. Built on a `planner → executor → tool` architecture with persistent memory, the agent understands where students are in their writing journey and provides contextual, personalized guidance from initial brainstorming through final polish.

Unlike generic writing assistants, this agent is specifically trained on college admissions requirements, rubrics, and successful essay patterns. It maintains long-term memory of student values, stories, and writing voice across multiple essay drafts and prompts, ensuring consistency and preventing story reuse across applications.

### Major User-Facing Capabilities:
- **Prompt Understanding**: Classifies essay prompts by themes and suggests optimal response strategies
- **Brainstorming Story Ideas**: Surfaces relevant personal experiences from user memory and suggests new angles
- **Outline Creation**: Generates structured outlines with hooks, growth moments, and reflection
- **Draft Writing**: Converts outlines to full drafts while maintaining user's authentic voice
- **Draft Revision**: Iterative improvement for clarity, insight, tone, and structural flow
- **Rubric-Based Scoring**: Evaluates essays on admissions criteria (0-10 scale across multiple dimensions)
- **Final Polish**: Grammar, word count optimization, and stylistic refinement

---

## 🧬 Agent Architecture

The system operates as a stateful agent with a `planner → subtask → tool` execution loop. Each interaction begins with the planner assessing the current writing phase and user context from memory, then routing to appropriate tools via the controller.

### Core Components:

**`essay_planner.py`**: The decision-making orchestrator that:
- Analyzes user input to determine current phase (brainstorming, outlining, drafting, revision, polish)
- Consults memory for context (previous drafts, used stories, writing patterns)
- Generates execution plan with prioritized tool calls
- Handles multi-turn conversations and revision cycles

**`essay_controller.py`**: Input routing and tool execution manager:
- Validates tool inputs and manages error handling
- Orchestrates parallel tool execution where possible
- Maintains conversation state and tool output history
- Handles model inference calls and response formatting

**`memory/user_profile.json`**: Persistent storage for:
- User demographic and academic data
- Core values and defining life experiences
- Writing voice characteristics and stylistic preferences
- Complete essay history with versions, scores, and feedback
- Cross-prompt story usage tracking

**`tools/`**: Modular, single-purpose tools (see Toolkit section)

**`models/`**: Fine-tuned models for specialized tasks:
- Essay scoring and feedback generation
- Prompt classification and response suggestion
- Tone preservation and voice mimicry

### Session Flow:
Each user session can span multiple drafts and revisions. The agent maintains context across sessions, remembering:
- Which stories have been used for which prompts
- User's preferred writing tone and structural patterns
- Previous feedback and how it was incorporated
- Themes and values already covered in other essays

The planner ensures no repetition of stories across different prompts and maintains thematic diversity across a student's full application portfolio.

---

## 🛠 Toolkit

The agent employs a library of granular, composable tools. Each tool has a single responsibility and can be combined for complex workflows.

### 🧩 Prompt Tools

| Tool | Description |
|------|-------------|
| `classify_prompt(prompt)` | Tags prompt with themes (adversity, growth, identity, community, intellectual curiosity) |
| `suggest_response_types(prompt)` | Suggests story types that typically work well (personal challenge, leadership moment, intellectual discovery) |
| `detect_prompt_overlap(prompt, other_prompts)` | Warns if story is being reused across prompts and suggests alternatives |
| `extract_prompt_requirements(prompt)` | Identifies word limits, specific questions, and evaluation criteria |
| `suggest_prompt_strategy(prompt, user_profile)` | Recommends approach based on user's strengths and available stories |

### 💡 Brainstorming Tools

| Tool | Description |
|------|-------------|
| `get_possible_stories(user_profile, prompt)` | Suggests relevant personal stories based on user's experiences and values |
| `match_story_to_prompt(story, prompt)` | Validates fit between story and prompt requirements (0-10 compatibility score) |
| `get_unused_values(user_profile, essays)` | Detects which of user's core traits haven't been written about yet |
| `expand_story_details(story_seed)` | Asks follow-up questions to flesh out story details and emotional impact |
| `find_story_angles(story)` | Suggests different ways to frame the same experience |
| `validate_story_uniqueness(story, essay_database)` | Checks if story angle is too common/cliché |

### 🧱 Structure Tools

| Tool | Description |
|------|-------------|
| `generate_outline(prompt, story)` | Creates structured outline: hook → context → moment → growth → reflection |
| `suggest_alternative_structure(draft)` | Offers different organizational approaches (chronological, thematic, vignette-based) |
| `section_labeler(draft)` | Labels parts of draft (intro, hook, growth moment, conclusion) for analysis |
| `validate_structure_flow(outline)` | Checks logical progression and emotional arc |
| `suggest_transitions(outline)` | Recommends connecting phrases between outline sections |
| `optimize_structure_for_length(outline, word_limit)` | Adjusts outline proportions for word count constraints |

### ✍️ Drafting Tools

| Tool | Description |
|------|-------------|
| `expand_outline(outline)` | Converts outline bullets into full paragraph drafts |
| `rewrite_paragraph(paragraph, goal)` | Rewrites for specific improvements (tone, depth, clarity, emotion) |
| `shrink_paragraph(paragraph)` | Condenses while preserving core meaning and impact |
| `improve_opening_line(draft)` | Suggests more compelling first sentences with stronger hooks |
| `optimize_conclusion(draft)` | Strengthens ending for lasting impact and emotional resonance |
| `add_sensory_details(paragraph)` | Enhances descriptions with specific, concrete imagery |
| `strengthen_voice(paragraph, user_voice_profile)` | Adjusts tone to match user's authentic writing style |

### 🧪 Evaluation Tools

| Tool | Description |
|------|-------------|
| `score_essay(draft, prompt)` | Comprehensive rubric scoring: clarity, insight, structure, voice, prompt fit (0-10 each) |
| `highlight_weak_areas(draft)` | Flags specific sentences/paragraphs with low scoring traits |
| `summarize_reader_impression(draft)` | Simulates admissions officer's gut reaction and key takeaways |
| `detect_clichés(draft)` | Flags overused phrases, tropes, and generic language |
| `detect_redundancy(draft, other_drafts)` | Warns about overlapping stories or values used too often |
| `check_prompt_alignment(draft, prompt)` | Verifies essay directly addresses prompt requirements |
| `measure_emotional_impact(draft)` | Scores emotional resonance and memorability |

### 🧹 Polishing Tools

| Tool | Description |
|------|-------------|
| `polish_tone(draft, target_tone)` | Refines for specific tones: concise, poetic, confident, conversational |
| `remove_fluff(draft)` | Eliminates filler words, redundant phrases, and vague language |
| `fix_grammar_and_style(draft)` | Comprehensive grammar, spelling, and style corrections |
| `meet_word_count(draft, limit)` | Intelligently trims draft to fit word limits (650, 350, 250) |
| `enhance_word_choice(draft)` | Suggests stronger, more precise vocabulary |
| `check_readability(draft)` | Ensures appropriate reading level and sentence variety |
| `final_consistency_check(draft)` | Verifies tense, voice, and stylistic consistency throughout |

---

## 🧠 Memory Design

The user profile is stored as a structured JSON file containing all context needed for personalized essay guidance.

### Schema: `memory/user_profile.json`

```json
{
  "user_info": {
    "name": "string",
    "grade": "integer",
    "intended_major": "string",
    "college_list": ["string"],
    "platforms": ["Common App", "UC", "Coalition"],
    "application_deadlines": {"college_name": "date"}
  },
  "academic_profile": {
    "gpa": "float",
    "test_scores": {"SAT": "integer", "ACT": "integer"},
    "courses": ["string"],
    "activities": [
      {
        "name": "string",
        "role": "string",
        "duration": "string",
        "description": "string",
        "impact": "string"
      }
    ]
  },
  "core_values": [
    {
      "value": "string",
      "description": "string",
      "evidence": ["string"],
      "used_in_essays": ["prompt_id"]
    }
  ],
  "defining_moments": [
    {
      "title": "string",
      "description": "string",
      "emotional_impact": "string",
      "lessons_learned": "string",
      "used_in_essays": ["prompt_id"],
      "themes": ["string"]
    }
  ],
  "writing_voice": {
    "tone_preferences": ["conversational", "introspective", "direct"],
    "vocabulary_level": "string",
    "sentence_patterns": ["short", "varied", "complex"],
    "stylistic_traits": ["uses_humor", "detail_oriented", "philosophical"]
  },
  "essay_history": [
    {
      "prompt_id": "string",
      "prompt_text": "string",
      "platform": "string",
      "versions": [
        {
          "version": "integer",
          "timestamp": "datetime",
          "content": "string",
          "word_count": "integer",
          "scores": {
            "clarity": "float",
            "insight": "float",
            "structure": "float",
            "voice": "float",
            "prompt_fit": "float"
          },
          "feedback": ["string"],
          "used_stories": ["string"],
          "used_values": ["string"]
        }
      ],
      "final_version": "integer",
      "status": "draft|revision|complete"
    }
  ],
  "cliché_tracker": {
    "used_phrases": ["string"],
    "overused_themes": ["string"],
    "common_mistakes": ["string"]
  },
  "feedback_patterns": {
    "common_strengths": ["string"],
    "recurring_issues": ["string"],
    "improvement_areas": ["string"]
  }
}
```

### Memory Usage Patterns:

**During Brainstorming**: Agent surfaces unused stories and values, warns about theme repetition across essays
**During Drafting**: Maintains consistent voice characteristics, prevents reuse of specific anecdotes
**During Revision**: References previous feedback patterns and successful writing strategies
**Cross-Prompt Analysis**: Ensures diverse themes and values across full application portfolio

---

## 🧪 Fine-Tuned Models

Custom models trained on college admissions essay data for specialized tasks where general-purpose LLMs are insufficient.

### ✅ MVP Models

| Model | Task | Training Data | Notes |
|-------|------|---------------|-------|
| `EssayScorer-v1` | Rubric-based scoring | 5K essays with human/GPT scores | 0-10 scale for clarity, depth, structure, voice, prompt fit |
| `PromptClassifier-v1` | Prompt → theme mapping | 1K prompts with theme labels | Tags: adversity, growth, identity, community, intellectual, leadership |
| `EssayCommenter-v1` | Line-by-line feedback | 3K essay sentences with targeted comments | Instruction-tuned for specific, actionable feedback |
| `ToneMimic-v1` | Voice preservation | User's previous drafts + rewrite pairs | Learns individual writing style for consistent revisions |

### 🚀 Optional Models

| Model | Task | Training Data | Notes |
|-------|------|---------------|-------|
| `OutlineToDraft-v1` | Auto-draft generation | 2K outline → draft pairs | Trained on structured outline-to-paragraph expansion |
| `ReaderSimulator-v1` | Admissions officer reactions | Essays + simulated AO summaries | Trained on paired essays with reader impressions |
| `ClichéDetector-v1` | Overused phrase identification | Common essay database with cliché labels | Specialized for college essay context |

### Model Specifications:

**Base Architecture**: LLaMA-3 8B with LoRA fine-tuning for efficiency
**Alternative**: GPT-3.5-turbo fine-tuning for faster deployment
**Training Strategy**: Bootstrap initial labels using GPT-4, then human validation on critical samples
**Evaluation**: Hold-out test sets with human evaluation for scoring accuracy

### Training Data Generation:

Use GPT-4 to generate initial training labels:
- Essay scores across rubric dimensions
- Prompt classifications and theme tags
- Feedback comments for specific writing issues
- Outline-to-draft expansions

Human reviewers validate 20% of GPT-4 labels for quality control.

---

## 📊 Required Data Sources

### Essay Data

**Public Essay Collections**:
- UC PIQ essays from College Essay Guy blog, Reddit r/ApplyingToCollege
- Common Application essays from personal statement databases
- Coalition Application essays from admissions consulting sites
- Scholarship essay examples from foundation websites

**Scoring Data**:
- GPT-4 generated rubric scores for 5,000+ essays
- Human-validated scores for 1,000+ essays (subset for model training)
- Admissions officer feedback samples (anonymized)

**Prompt Data**:
- Complete Common Application prompt sets (2020-2024)
- UC Personal Insight Question prompts
- Coalition Application prompts
- Supplemental essay prompts from top 50 universities

### User Data (Personalized Writing)

**Profile Data**:
- Academic transcripts and test scores (user-provided)
- Extracurricular activities and leadership roles
- Personal background and demographic information
- Values assessment questionnaire responses

**Writing Samples**:
- Previous essay drafts and revisions
- School writing assignments (with permission)
- Personal journals or blog posts (optional)
- Communication style from intake conversations

### Training Data Pipeline:

1. **Data Collection**: Scrape public sources, partner with counselors
2. **Data Cleaning**: Remove personally identifiable information
3. **Label Generation**: Use GPT-4 for initial scoring and classification
4. **Human Validation**: Expert review of 20% of labeled data
5. **Quality Control**: Inter-rater reliability checks for consistency

---

## 📅 Build Timeline & TODO List

### **Phase 1: MVP Drafting Loop (Weeks 1-4)**
- [ ] **Week 1: Core Architecture**
  - [ ] Set up project structure with `essay_planner.py` and `essay_controller.py`
  - [ ] Design memory schema and implement JSON storage
  - [ ] Create basic tool interface with error handling
  - [ ] Build prompt classification tool using GPT-4 API

- [ ] **Week 2: Brainstorming & Outline Tools**
  - [ ] Implement story suggestion and matching tools
  - [ ] Create outline generation with structured templates
  - [ ] Build story validation and uniqueness checking
  - [ ] Add user profile initialization and values assessment

- [ ] **Week 3: Draft Generation**
  - [ ] Create outline-to-draft expansion tool
  - [ ] Implement paragraph rewriting for clarity and tone
  - [ ] Build basic essay scoring using GPT-4 rubric
  - [ ] Add draft version tracking and comparison

- [ ] **Week 4: MVP UI & Integration**
  - [ ] Build web interface: prompt entry → outline → draft editor
  - [ ] Implement real-time scoring display
  - [ ] Add revision suggestions and feedback panel
  - [ ] Create user onboarding flow for profile setup

### **Phase 2: Feedback & Polish (Weeks 5-8)**
- [ ] **Week 5: Evaluation Tools**
  - [ ] Build comprehensive rubric scoring system
  - [ ] Implement cliché detection and redundancy checking
  - [ ] Create reader impression simulation
  - [ ] Add weak area highlighting with specific feedback

- [ ] **Week 6: Polishing Tools**
  - [ ] Develop grammar and style correction tools
  - [ ] Create word count optimization algorithms
  - [ ] Build tone refinement and voice consistency tools
  - [ ] Implement final consistency checking

- [ ] **Week 7: Memory & Cross-Essay Analysis**
  - [ ] Enhance memory system with usage tracking
  - [ ] Build cross-prompt story reuse detection
  - [ ] Implement theme diversity analysis
  - [ ] Create feedback pattern recognition

- [ ] **Week 8: Advanced Features**
  - [ ] Add multi-draft revision workflows
  - [ ] Implement collaborative editing features
  - [ ] Build export functionality for different platforms
  - [ ] Create progress tracking and deadline management

### **Phase 3: Fine-Tuning & Optimization (Weeks 9-12)**
- [ ] **Week 9: Data Collection & Preparation**
  - [ ] Collect and clean 5,000+ essay samples
  - [ ] Generate GPT-4 scoring labels for training data
  - [ ] Create prompt classification dataset
  - [ ] Build outline-to-draft training pairs

- [ ] **Week 10: Model Training**
  - [ ] Fine-tune EssayScorer-v1 on rubric scoring task
  - [ ] Train PromptClassifier-v1 for theme detection
  - [ ] Develop EssayCommenter-v1 for feedback generation
  - [ ] Create ToneMimic-v1 for voice preservation

- [ ] **Week 11: Model Integration & Testing**
  - [ ] Deploy fine-tuned models to production
  - [ ] A/B test against GPT-4 baseline performance
  - [ ] Optimize model serving and response times
  - [ ] Implement model fallback strategies

- [ ] **Week 12: Production Optimization**
  - [ ] Performance testing and optimization
  - [ ] User acceptance testing with beta students
  - [ ] Documentation and deployment guides
  - [ ] Monitoring and analytics implementation

### **Phase 4: Advanced Features (Weeks 13-16)**
- [ ] **Week 13: Advanced Models**
  - [ ] Train OutlineToDraft-v1 for automated drafting
  - [ ] Develop ReaderSimulator-v1 for admissions insights
  - [ ] Create ClichéDetector-v1 for context-aware detection
  - [ ] Implement ensemble scoring with multiple models

- [ ] **Week 14: Personalization**
  - [ ] Build adaptive learning from user feedback
  - [ ] Create personalized writing style recommendations
  - [ ] Implement intelligent prompt suggestions
  - [ ] Add competitive analysis features

- [ ] **Week 15: Collaboration & Sharing**
  - [ ] Build counselor dashboard for student oversight
  - [ ] Create peer review and feedback systems
  - [ ] Implement essay sharing and collaboration tools
  - [ ] Add plagiarism detection and originality scoring

- [ ] **Week 16: Launch Preparation**
  - [ ] Final user testing and bug fixes
  - [ ] Performance monitoring and scaling
  - [ ] Marketing material and demo preparation
  - [ ] Customer support documentation

### Success Metrics:
- **User Engagement**: 80% of users complete at least one full draft
- **Essay Quality**: 25% improvement in average rubric scores
- **Efficiency**: 50% reduction in time from outline to final draft
- **Uniqueness**: 95% of essays pass originality checks
- **User Satisfaction**: 4.5+ star average rating

Each task is scoped for 4-8 hours of focused development work, with clear deliverables and testing criteria.