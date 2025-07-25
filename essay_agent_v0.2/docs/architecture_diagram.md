# 🏗️ Essay Agent v0.2: Complete Architecture Diagram

This diagram provides a comprehensive visual representation of the Essay Agent v0.2 architecture, showing all major components, data flows, and system interactions.

## 🎯 System Overview Architecture

```mermaid
graph TB
    %% Styling for black boxes with white text
    classDef default fill:#000000,stroke:#333333,stroke-width:2px,color:#ffffff
    classDef userBox fill:#1a1a1a,stroke:#666666,stroke-width:2px,color:#ffffff
    classDef agentBox fill:#2d2d2d,stroke:#888888,stroke-width:2px,color:#ffffff
    classDef memoryBox fill:#0f3460,stroke:#1e88e5,stroke-width:2px,color:#ffffff
    classDef toolBox fill:#1b5e20,stroke:#4caf50,stroke-width:2px,color:#ffffff
    classDef planningBox fill:#4a148c,stroke:#9c27b0,stroke-width:2px,color:#ffffff
    classDef sidebarBox fill:#d84315,stroke:#ff5722,stroke-width:2px,color:#ffffff
    classDef validationBox fill:#bf360c,stroke:#ff9800,stroke-width:2px,color:#ffffff
    
    %% User Layer
    U1[Student Writing<br/>Stanford Leadership Essay]:::userBox
    U2[Text Editor<br/>Real-time Editing]:::userBox
    U3[Cursor Sidebar<br/>AI Assistant Interface]:::userBox
    
    %% Agent Environment Framework
    AE[Essay Agent Environment<br/>Central Orchestration Hub]:::agentBox
    
    %% Specialized Agents
    PA[Planning Agent<br/>Intent Analysis & Goal Decomposition]:::agentBox
    TA[Tool Agent<br/>Tool Execution & Parameter Resolution]:::agentBox
    QA[Quality Agent<br/>Real-time Quality Monitoring]:::agentBox
    MA[Memory Agent<br/>Hyperpersonalized Memory Management]:::agentBox
    CA[Completion Agent<br/>Goal Achievement Detection]:::agentBox
    PER[Personalization Agent<br/>Adaptive Coaching & Voice Preservation]:::agentBox
    
    %% Hyperpersonalized Memory System (MIRIX + A-MEM + Cognitive Weave)
    HMS[Hyperpersonalized Memory System<br/>Six-Bank Architecture]:::memoryBox
    CM[Core Memory<br/>Student Identity & Background]:::memoryBox
    EM[Episodic Memory<br/>Interaction History & Sessions]:::memoryBox
    SM[Semantic Memory<br/>Writing Knowledge & Strategies]:::memoryBox
    PM[Procedural Memory<br/>Writing Processes & Workflows]:::memoryBox
    RM[Resource Memory<br/>Essays, Drafts & Feedback]:::memoryBox
    KV[Knowledge Vault<br/>Refined Insights & Discoveries]:::memoryBox
    
    %% Cognitive Weave Components
    RG[Resonance Graph<br/>Spatio-Temporal Connections]:::memoryBox
    IP[Insight Particles<br/>Rich Memory Units]:::memoryBox
    SO[Semantic Oracle<br/>Dynamic Memory Enrichment]:::memoryBox
    CR[Cognitive Refiner<br/>Insight Synthesis]:::memoryBox
    
    %% Hierarchical Planning System
    HPS[Hierarchical Planning System<br/>Strategic → Tactical → Operational]:::planningBox
    SP[Strategic Planner<br/>Goal Decomposition & Intent Analysis]:::planningBox
    TP[Tactical Planner<br/>Tool Sequencing & Dependencies]:::planningBox
    OP[Operational Planner<br/>Parameter Resolution & Context]:::planningBox
    
    %% Goal Completion & Agentic Loop
    GCE[Goal Completion Engine<br/>Multi-Dimensional Completion Criteria]:::planningBox
    AEL[Agentic Execution Loop<br/>SENSE → REASON → PLAN → ACT → CHECK]:::planningBox
    
    %% Core Tools with Pydantic Validation
    TR[Tool Registry<br/>Validated Tool Management]:::toolBox
    T1[Smart Brainstorm<br/>Personalized Story Generation]:::toolBox
    T2[Smart Outline<br/>Context-Aware Structure]:::toolBox
    T3[Smart Improve Paragraph<br/>Voice-Preserving Enhancement]:::toolBox
    T4[Smart Essay Chat<br/>Conversational Coaching]:::toolBox
    T5[Smart Classify Prompt<br/>Intelligent Prompt Analysis]:::toolBox
    T6[Smart Draft<br/>Section Generation]:::toolBox
    T7[Smart Evaluate<br/>Quality Assessment]:::toolBox
    T8[Smart Polish<br/>Final Enhancement]:::toolBox
    
    %% Cursor Sidebar Integration
    CSI[Cursor Sidebar Integration<br/>Real-time Editor Companion]:::sidebarBox
    TSA[Text Selection API<br/>Advanced Editor Integration]:::sidebarBox
    ECT[Essay Context Tracker<br/>Continuous State Awareness]:::sidebarBox
    SSM[Sidebar Session Manager<br/>Persistent Context Management]:::sidebarBox
    SUI[Sidebar UI Interface<br/>Natural Conversation & Progress]:::sidebarBox
    RTS[Real-Time Sync Engine<br/>Editor ↔ Sidebar Synchronization]:::sidebarBox
    
    %% JSON-First Architecture & Validation
    JFA[JSON-First Architecture<br/>Perfect Reliability System]:::validationBox
    SPE[Structured Prompt Engine<br/>Schema-Validated LLM Calls]:::validationBox
    SVP[Schema Validation Pipeline<br/>Comprehensive Data Integrity]:::validationBox
    SEH[Structured Error Handler<br/>Intelligent Retry & Recovery]:::validationBox
    
    %% External Systems
    LLM[OpenAI GPT-4<br/>Primary Intelligence Source]:::default
    VDB[Vector Database<br/>Memory Storage & Retrieval]:::default
    EDITOR[Student's Text Editor<br/>VS Code, Cursor, etc.]:::default
    
    %% Primary Data Flows
    U1 -.-> U2
    U2 <--> U3
    U3 <--> CSI
    CSI <--> AE
    
    AE --> PA
    AE --> TA
    AE --> QA
    AE --> MA
    AE --> CA
    AE --> PER
    
    %% Agent Coordination
    PA <--> TA
    PA <--> QA
    TA <--> QA
    MA <--> PA
    MA <--> TA
    CA <--> PA
    CA <--> QA
    PER <--> MA
    PER <--> TA
    
    %% Memory System Integration
    MA --> HMS
    HMS --> CM
    HMS --> EM
    HMS --> SM
    HMS --> PM
    HMS --> RM
    HMS --> KV
    
    %% Cognitive Weave Integration
    HMS --> RG
    HMS --> IP
    HMS --> SO
    HMS --> CR
    
    %% Planning System Integration
    PA --> HPS
    HPS --> SP
    HPS --> TP
    HPS --> OP
    
    %% Goal Completion Integration
    AE --> GCE
    AE --> AEL
    GCE <--> AEL
    
    %% Tool System Integration
    TA --> TR
    TR --> T1
    TR --> T2
    TR --> T3
    TR --> T4
    TR --> T5
    TR --> T6
    TR --> T7
    TR --> T8
    
    %% Sidebar Integration
    CSI --> TSA
    CSI --> ECT
    CSI --> SSM
    CSI --> SUI
    CSI --> RTS
    
    %% JSON Architecture Integration
    AE --> JFA
    JFA --> SPE
    JFA --> SVP
    JFA --> SEH
    
    %% External System Integration
    SPE <--> LLM
    HMS <--> VDB
    CSI <--> EDITOR
    
    %% Tool Validation Flow
    TR --> SVP
    T1 --> SVP
    T2 --> SVP
    T3 --> SVP
    T4 --> SVP
    T5 --> SVP
    T6 --> SVP
    T7 --> SVP
    T8 --> SVP
```

## 🔄 Agentic Execution Flow Diagram

```mermaid
flowchart TD
    %% Styling
    classDef default fill:#000000,stroke:#333333,stroke-width:2px,color:#ffffff
    classDef stepBox fill:#1a237e,stroke:#3f51b5,stroke-width:2px,color:#ffffff
    classDef decisionBox fill:#b71c1c,stroke:#f44336,stroke-width:2px,color:#ffffff
    classDef memoryBox fill:#0f3460,stroke:#1e88e5,stroke-width:2px,color:#ffffff
    classDef outputBox fill:#1b5e20,stroke:#4caf50,stroke-width:2px,color:#ffffff
    
    %% User Input
    START[Student Input:<br/>"Help me make this paragraph more compelling"]:::stepBox
    
    %% 1. SENSE Phase
    SENSE[SENSE:<br/>Gather Hyperpersonalized Context]:::stepBox
    SENSE1[Query Core Memory<br/>Student Background & Goals]:::memoryBox
    SENSE2[Query Episodic Memory<br/>Recent Interactions & Progress]:::memoryBox
    SENSE3[Query Knowledge Vault<br/>Personal Insights & Strengths]:::memoryBox
    SENSE4[Analyze Current Essay Context<br/>Position, Content, Requirements]:::stepBox
    
    %% 2. REASON Phase
    REASON[REASON:<br/>Understand Intent with Personalization]:::stepBox
    REASON1[Analyze Surface Intent<br/>Text improvement request]:::stepBox
    REASON2[Identify Deeper Goals<br/>College fit, authentic voice]:::stepBox
    REASON3[Assess Personalization Opportunities<br/>Background integration potential]:::stepBox
    
    %% 3. PLAN Phase
    PLAN[PLAN:<br/>Create Personalized Execution Plan]:::stepBox
    PLAN1[Strategic: Goal Decomposition<br/>Improve while preserving voice]:::stepBox
    PLAN2[Tactical: Tool Sequencing<br/>Select improvement approach]:::stepBox
    PLAN3[Operational: Parameter Resolution<br/>User profile → tool inputs]:::stepBox
    
    %% 4. COORDINATE Phase
    COORDINATE[COORDINATE:<br/>Multi-Agent Collaboration]:::stepBox
    COORD1[Quality Agent Pre-approval<br/>Validate improvement strategy]:::stepBox
    COORD2[Memory Agent Context Injection<br/>Provide personalization data]:::stepBox
    COORD3[Planning Agent Optimization<br/>Refine execution approach]:::stepBox
    
    %% 5. ACT Phase
    ACT[ACT:<br/>Execute with Quality Gates]:::stepBox
    ACT1[Tool Execution<br/>Smart Improve Paragraph]:::stepBox
    ACT2[Real-time Quality Monitoring<br/>Voice preservation check]:::stepBox
    ACT3[Validation Pipeline<br/>Schema & quality validation]:::stepBox
    
    %% 6. UPDATE Phase
    UPDATE[UPDATE:<br/>Evolve Memory Understanding]:::stepBox
    UPDATE1[Store Interaction Results<br/>Success patterns & preferences]:::memoryBox
    UPDATE2[Update User Profile<br/>Writing style refinements]:::memoryBox
    UPDATE3[Generate New Insights<br/>Personalization improvements]:::memoryBox
    
    %% 7. CHECK Phase
    CHECK[CHECK:<br/>Assess Completion]:::decisionBox
    CHECK1[Intent Satisfaction<br/>Did we address the request?]:::decisionBox
    CHECK2[Quality Threshold<br/>Meets student's standards?]:::decisionBox
    CHECK3[Voice Preservation<br/>Maintains authenticity?]:::decisionBox
    CHECK4[Personalization Score<br/>Reflects student's background?]:::decisionBox
    
    %% Decision Point
    COMPLETE{Goal Complete?}:::decisionBox
    
    %% 8. RESPOND Phase
    RESPOND[RESPOND:<br/>Generate Final Response]:::stepBox
    RESPOND1[Compile Improved Text<br/>With explanation of changes]:::outputBox
    RESPOND2[Provide Personalized Coaching<br/>Based on student's learning style]:::outputBox
    RESPOND3[Suggest Next Steps<br/>Context-aware recommendations]:::outputBox
    
    %% Iteration Loop
    ITERATE[Iterate:<br/>Refine Approach]:::stepBox
    
    %% Final Output
    OUTPUT[Deliver to Sidebar:<br/>Improved paragraph + coaching insights]:::outputBox
    
    %% Flow Connections
    START --> SENSE
    SENSE --> SENSE1
    SENSE --> SENSE2
    SENSE --> SENSE3
    SENSE --> SENSE4
    SENSE1 --> REASON
    SENSE2 --> REASON
    SENSE3 --> REASON
    SENSE4 --> REASON
    
    REASON --> REASON1
    REASON --> REASON2
    REASON --> REASON3
    REASON1 --> PLAN
    REASON2 --> PLAN
    REASON3 --> PLAN
    
    PLAN --> PLAN1
    PLAN --> PLAN2
    PLAN --> PLAN3
    PLAN1 --> COORDINATE
    PLAN2 --> COORDINATE
    PLAN3 --> COORDINATE
    
    COORDINATE --> COORD1
    COORDINATE --> COORD2
    COORDINATE --> COORD3
    COORD1 --> ACT
    COORD2 --> ACT
    COORD3 --> ACT
    
    ACT --> ACT1
    ACT --> ACT2
    ACT --> ACT3
    ACT1 --> UPDATE
    ACT2 --> UPDATE
    ACT3 --> UPDATE
    
    UPDATE --> UPDATE1
    UPDATE --> UPDATE2
    UPDATE --> UPDATE3
    UPDATE1 --> CHECK
    UPDATE2 --> CHECK
    UPDATE3 --> CHECK
    
    CHECK --> CHECK1
    CHECK --> CHECK2
    CHECK --> CHECK3
    CHECK --> CHECK4
    CHECK1 --> COMPLETE
    CHECK2 --> COMPLETE
    CHECK3 --> COMPLETE
    CHECK4 --> COMPLETE
    
    COMPLETE -->|Yes| RESPOND
    COMPLETE -->|No| ITERATE
    ITERATE --> PLAN
    
    RESPOND --> RESPOND1
    RESPOND --> RESPOND2
    RESPOND --> RESPOND3
    RESPOND1 --> OUTPUT
    RESPOND2 --> OUTPUT
    RESPOND3 --> OUTPUT
```

## 🧠 Memory System Architecture Detail

```mermaid
graph TB
    %% Styling
    classDef default fill:#000000,stroke:#333333,stroke-width:2px,color:#ffffff
    classDef coreBox fill:#1a237e,stroke:#3f51b5,stroke-width:2px,color:#ffffff
    classDef episodicBox fill:#2e7d32,stroke:#4caf50,stroke-width:2px,color:#ffffff
    classDef semanticBox fill:#7b1fa2,stroke:#9c27b0,stroke-width:2px,color:#ffffff
    classDef proceduralBox fill:#d84315,stroke:#ff5722,stroke-width:2px,color:#ffffff
    classDef resourceBox fill:#f57f17,stroke:#ffeb3b,stroke-width:2px,color:#ffffff
    classDef knowledgeBox fill:#5d4037,stroke:#795548,stroke-width:2px,color:#ffffff
    classDef weaveBox fill:#37474f,stroke:#607d8b,stroke-width:2px,color:#ffffff
    
    %% Memory System Hub
    HMS[Hyperpersonalized Memory System<br/>MIRIX + A-MEM + Cognitive Weave]:::default
    
    %% Core Memory Bank
    CM[Core Memory Bank<br/>Student Identity Foundation]:::coreBox
    CM1[Basic Demographics<br/>Name, Grade, School Type, Location]:::coreBox
    CM2[Academic Profile<br/>GPA, Test Scores, Interests, Major]:::coreBox
    CM3[Extracurricular Profile<br/>Activities, Leadership, Work, Talents]:::coreBox
    CM4[Personal Characteristics<br/>Personality, Writing Style, Learning Preferences]:::coreBox
    CM5[College Application Goals<br/>Target Schools, Timeline, Essay Objectives]:::coreBox
    
    %% Episodic Memory Bank
    EM[Episodic Memory Bank<br/>Interaction History]:::episodicBox
    EM1[Writing Sessions<br/>Duration, Productivity, Breakthroughs]:::episodicBox
    EM2[Interaction Sequences<br/>Questions, Responses, Satisfaction]:::episodicBox
    EM3[Temporal Patterns<br/>Best times, mood cycles, progress rhythms]:::episodicBox
    EM4[Challenge History<br/>Difficulties faced, solutions found]:::episodicBox
    
    %% Semantic Memory Bank
    SM[Semantic Memory Bank<br/>Writing Knowledge]:::semanticBox
    SM1[Writing Concepts<br/>Student's understanding of essay principles]:::semanticBox
    SM2[Essay Strategies<br/>Effective approaches for this student]:::semanticBox
    SM3[Success Patterns<br/>What works well for this student]:::semanticBox
    SM4[Learning Insights<br/>How student best absorbs writing guidance]:::semanticBox
    
    %% Procedural Memory Bank
    PM[Procedural Memory Bank<br/>Writing Processes]:::proceduralBox
    PM1[Writing Workflows<br/>Preferred sequences and methods]:::proceduralBox
    PM2[Revision Patterns<br/>How student likes to edit and improve]:::proceduralBox
    PM3[Feedback Processing<br/>How student responds to different guidance]:::proceduralBox
    PM4[Tool Preferences<br/>Which assistance methods work best]:::proceduralBox
    
    %% Resource Memory Bank
    RM[Resource Memory Bank<br/>Essay Artifacts]:::resourceBox
    RM1[Essay Collection<br/>Drafts, versions, complete essays]:::resourceBox
    RM2[Feedback History<br/>Comments, suggestions, improvements made]:::resourceBox
    RM3[Quality Metrics<br/>Progress tracking, improvement trends]:::resourceBox
    RM4[Reference Materials<br/>Successful examples, inspiration sources]:::resourceBox
    
    %% Knowledge Vault
    KV[Knowledge Vault<br/>Refined Insights]:::knowledgeBox
    KV1[Student Strengths<br/>Validated talents and advantages]:::knowledgeBox
    KV2[Growth Areas<br/>Opportunities for development]:::knowledgeBox
    KV3[Personalization Strategy<br/>Optimal coaching approaches]:::knowledgeBox
    KV4[Success Predictors<br/>Patterns that lead to breakthroughs]:::knowledgeBox
    
    %% Cognitive Weave Components
    RG[Resonance Graph<br/>Spatio-Temporal Connections]:::weaveBox
    IP[Insight Particles<br/>Rich Memory Units with Resonance Keys]:::weaveBox
    SO[Semantic Oracle<br/>Dynamic Memory Enrichment]:::weaveBox
    CR[Cognitive Refiner<br/>Autonomous Insight Synthesis]:::weaveBox
    
    %% Memory Flow Architecture
    HMS --> CM
    HMS --> EM
    HMS --> SM
    HMS --> PM
    HMS --> RM
    HMS --> KV
    HMS --> RG
    HMS --> IP
    HMS --> SO
    HMS --> CR
    
    %% Core Memory Details
    CM --> CM1
    CM --> CM2
    CM --> CM3
    CM --> CM4
    CM --> CM5
    
    %% Episodic Memory Details
    EM --> EM1
    EM --> EM2
    EM --> EM3
    EM --> EM4
    
    %% Semantic Memory Details
    SM --> SM1
    SM --> SM2
    SM --> SM3
    SM --> SM4
    
    %% Procedural Memory Details
    PM --> PM1
    PM --> PM2
    PM --> PM3
    PM --> PM4
    
    %% Resource Memory Details
    RM --> RM1
    RM --> RM2
    RM --> RM3
    RM --> RM4
    
    %% Knowledge Vault Details
    KV --> KV1
    KV --> KV2
    KV --> KV3
    KV --> KV4
    
    %% Cross-Memory Connections (Cognitive Weave)
    CM1 -.-> RG
    EM2 -.-> RG
    SM3 -.-> RG
    KV1 -.-> IP
    CM3 -.-> IP
    RM2 -.-> SO
    PM1 -.-> CR
    SM2 -.-> CR
```

## 🛠️ Tool System Architecture

```mermaid
graph TD
    %% Styling
    classDef default fill:#000000,stroke:#333333,stroke-width:2px,color:#ffffff
    classDef registryBox fill:#1a237e,stroke:#3f51b5,stroke-width:2px,color:#ffffff
    classDef toolBox fill:#2e7d32,stroke:#4caf50,stroke-width:2px,color:#ffffff
    classDef validationBox fill:#b71c1c,stroke:#f44336,stroke-width:2px,color:#ffffff
    classDef schemaBox fill:#e65100,stroke:#ff9800,stroke-width:2px,color:#ffffff
    
    %% Tool Registry
    TR[Tool Registry<br/>Central Tool Management]:::registryBox
    
    %% Core Tools
    T1[Smart Brainstorm<br/>Personalized Story Generation]:::toolBox
    T1I[Input: Essay prompt, target college, student background]:::schemaBox
    T1O[Output: 5 personalized story ideas with authenticity scores]:::schemaBox
    
    T2[Smart Outline<br/>Context-Aware Structure Generation]:::toolBox
    T2I[Input: Selected story, prompt, word limit, style preferences]:::schemaBox
    T2O[Output: Detailed outline with word allocation and tips]:::schemaBox
    
    T3[Smart Improve Paragraph<br/>Voice-Preserving Enhancement]:::toolBox
    T3I[Input: Original text, improvement focus, voice preservation flag]:::schemaBox
    T3O[Output: Improved text with change summary and voice score]:::schemaBox
    
    T4[Smart Essay Chat<br/>Conversational Coaching]:::toolBox
    T4I[Input: Student message, essay context, conversation history]:::schemaBox
    T4O[Output: Personalized response with insights and next steps]:::schemaBox
    
    T5[Smart Classify Prompt<br/>Intelligent Prompt Analysis]:::toolBox
    T5I[Input: Essay prompt, target college, application type]:::schemaBox
    T5O[Output: Prompt analysis with personalized strategies]:::schemaBox
    
    T6[Smart Draft<br/>Section Generation]:::toolBox
    T6I[Input: Outline section, story details, voice guidelines]:::schemaBox
    T6O[Output: Draft content maintaining student's authentic voice]:::schemaBox
    
    T7[Smart Evaluate<br/>Quality Assessment]:::toolBox
    T7I[Input: Essay text, prompt requirements, quality criteria]:::schemaBox
    T7O[Output: Quality scores with specific improvement suggestions]:::schemaBox
    
    T8[Smart Polish<br/>Final Enhancement]:::toolBox
    T8I[Input: Near-final essay, polish focus areas, word limits]:::schemaBox
    T8O[Output: Polished essay with refinement explanations]:::schemaBox
    
    %% Validation System
    PRE[Pre-execution Validation<br/>Dependency & Context Checks]:::validationBox
    POST[Post-execution Validation<br/>Quality & Schema Verification]:::validationBox
    RETRY[Retry Logic<br/>Intelligent Error Recovery]:::validationBox
    
    %% Base Tool Architecture
    BTA[Base Agentic Tool<br/>Pydantic Interface Contract]:::registryBox
    INPUT[Input Schema Validation<br/>Perfect Parameter Resolution]:::validationBox
    OUTPUT[Output Schema Validation<br/>Guaranteed Response Format]:::validationBox
    PERSON[Personalization Hooks<br/>Background, Style, Preferences]:::registryBox
    
    %% Flow Connections
    TR --> T1
    TR --> T2
    TR --> T3
    TR --> T4
    TR --> T5
    TR --> T6
    TR --> T7
    TR --> T8
    
    %% Tool Details
    T1 --> T1I
    T1 --> T1O
    T2 --> T2I
    T2 --> T2O
    T3 --> T3I
    T3 --> T3O
    T4 --> T4I
    T4 --> T4O
    T5 --> T5I
    T5 --> T5O
    T6 --> T6I
    T6 --> T6O
    T7 --> T7I
    T7 --> T7O
    T8 --> T8I
    T8 --> T8O
    
    %% Validation Flow
    TR --> PRE
    PRE --> POST
    POST --> RETRY
    
    %% Base Architecture
    BTA --> INPUT
    BTA --> OUTPUT
    BTA --> PERSON
    TR --> BTA
    
    %% Tool Inheritance
    T1 --> BTA
    T2 --> BTA
    T3 --> BTA
    T4 --> BTA
    T5 --> BTA
    T6 --> BTA
    T7 --> BTA
    T8 --> BTA
```

## 📱 Cursor Sidebar Integration Architecture

```mermaid
graph TB
    %% Styling
    classDef default fill:#000000,stroke:#333333,stroke-width:2px,color:#ffffff
    classDef editorBox fill:#2e7d32,stroke:#4caf50,stroke-width:2px,color:#ffffff
    classDef sidebarBox fill:#d84315,stroke:#ff5722,stroke-width:2px,color:#ffffff
    classDef apiBox fill:#7b1fa2,stroke:#9c27b0,stroke-width:2px,color:#ffffff
    classDef uiBox fill:#1a237e,stroke:#3f51b5,stroke-width:2px,color:#ffffff
    classDef syncBox fill:#f57f17,stroke:#ffeb3b,stroke-width:2px,color:#ffffff
    
    %% Editor Layer
    EDITOR[Student's Text Editor<br/>VS Code, Cursor, etc.]:::editorBox
    ESSAY[Essay Document<br/>Stanford Leadership Essay]:::editorBox
    SELECTION[Text Selection<br/>Highlighted paragraph for improvement]:::editorBox
    
    %% Sidebar Integration Hub
    CSI[Cursor Sidebar Integration<br/>Real-time Writing Companion]:::sidebarBox
    
    %% Text Selection API
    TSA[Text Selection API<br/>Advanced Editor Integration]:::apiBox
    TSA1[Capture Text Selection<br/>Range, context, position analysis]:::apiBox
    TSA2[Handle Improvement Requests<br/>Context-aware text enhancement]:::apiBox
    TSA3[Monitor Editor Events<br/>Selection, edit, cursor, save events]:::apiBox
    
    %% Essay Context Tracker
    ECT[Essay Context Tracker<br/>Continuous State Awareness]:::apiBox
    ECT1[Track Essay Evolution<br/>Content changes, progress metrics]:::apiBox
    ECT2[Analyze Structure<br/>Introduction, body, conclusion detection]:::apiBox
    ECT3[Provide Contextual Assistance<br/>Phase-appropriate suggestions]:::apiBox
    
    %% Session Manager
    SSM[Sidebar Session Manager<br/>Persistent Context Management]:::apiBox
    SSM1[Create/Restore Sessions<br/>Essay-specific memory restoration]:::apiBox
    SSM2[Handle Interruptions<br/>Editor close, system restart recovery]:::apiBox
    SSM3[Maintain Conversation History<br/>Cross-session continuity]:::apiBox
    
    %% UI Interface
    SUI[Sidebar UI Interface<br/>Natural Conversation & Progress]:::uiBox
    SUI1[Conversation Thread<br/>Student ↔ Agent dialogue]:::uiBox
    SUI2[Progress Indicators<br/>Essay completion, phase tracking]:::uiBox
    SUI3[Memory Insights Panel<br/>Personalization transparency]:::uiBox
    SUI4[Quick Actions<br/>Context-sensitive suggestions]:::uiBox
    
    %% Real-Time Sync
    RTS[Real-Time Sync Engine<br/>Editor ↔ Sidebar Synchronization]:::syncBox
    RTS1[WebSocket Connection<br/>Bidirectional real-time communication]:::syncBox
    RTS2[Essay Change Processing<br/>Live content synchronization]:::syncBox
    RTS3[Context Updates<br/>Sidebar awareness of essay state]:::syncBox
    
    %% Agent Integration
    AGENT[Essay Agent Environment<br/>Full AI System Integration]:::default
    
    %% Data Flows
    EDITOR --> ESSAY
    ESSAY --> SELECTION
    SELECTION --> CSI
    
    CSI --> TSA
    CSI --> ECT
    CSI --> SSM
    CSI --> SUI
    CSI --> RTS
    
    %% Text Selection API Details
    TSA --> TSA1
    TSA --> TSA2
    TSA --> TSA3
    
    %% Essay Context Tracker Details
    ECT --> ECT1
    ECT --> ECT2
    ECT --> ECT3
    
    %% Session Manager Details
    SSM --> SSM1
    SSM --> SSM2
    SSM --> SSM3
    
    %% UI Interface Details
    SUI --> SUI1
    SUI --> SUI2
    SUI --> SUI3
    SUI --> SUI4
    
    %% Real-Time Sync Details
    RTS --> RTS1
    RTS --> RTS2
    RTS --> RTS3
    
    %% Integration with Agent System
    CSI <--> AGENT
    TSA --> AGENT
    ECT --> AGENT
    SSM --> AGENT
    
    %% Bidirectional Communication
    EDITOR <--> RTS1
    SUI1 <--> TSA2
    ECT1 <--> RTS2
    SSM1 <--> RTS3
```

This comprehensive architecture diagram captures every major component of Essay Agent v0.2, from the user interface down to the memory storage layer. The black boxes with white text provide clear visual separation while maintaining readability. Each diagram focuses on a different aspect of the system:

1. **System Overview**: Shows the complete architecture with all major components
2. **Agentic Execution Flow**: Details the SENSE → REASON → PLAN → ACT → CHECK loop
3. **Memory System Detail**: Breaks down the six-bank MIRIX system with Cognitive Weave
4. **Tool System**: Shows all 8 core tools with their input/output schemas
5. **Sidebar Integration**: Details the cursor integration with real-time synchronization

You can edit any aspect of these diagrams before we begin implementation. The visual representation should help identify any architectural components that need adjustment or additional detail. 