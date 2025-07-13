export interface University {
  id: string;
  name: string;
  shortName?: string;
  type: 'public' | 'private' | 'other';
  location: {
    city: string;
    state: string;
    country: string;
  };
  website?: string;
}

export interface EssayPrompt {
  id: string;
  universityId: string;
  text: string;
  wordLimit: number;
  minWordCount?: number;
  type: 'personal_statement' | 'supplemental' | 'scholarship' | 'other';
  title?: string;
  deadline?: Date;
  isActive: boolean;
  createdAt: Date;
  updatedAt: Date;
}

export interface OutlineItem {
  id: string;
  text: string;
  level: number; // 0 = main point, 1 = sub-point, etc.
  order: number;
  parentId?: string;
  isExpanded: boolean;
  isLocked: boolean;
  createdAt: Date;
  updatedAt: Date;
}

export interface EssayVersion {
  id: string;
  essayId: string;
  content: string;
  wordCount: number;
  title?: string;
  isAutoSave: boolean;
  versionNumber: number;
  changeType: 'draft' | 'ai_revision' | 'manual_edit' | 'ai_generation';
  changeSummary?: string;
  userNotes?: string;
  createdAt: Date;
  metadata?: {
    aiPrompt?: string;
    selectedText?: string;
    improvementType?: 'style' | 'clarity' | 'tone' | 'length' | 'grammar';
  };
}

export interface Essay {
  id: string;
  userId: string;
  universityId: string;
  promptId: string;
  title: string;
  currentContent: string;
  currentWordCount: number;
  currentVersionId: string;
  outline: OutlineItem[];
  status: 'draft' | 'in_progress' | 'completed' | 'submitted';
  progressPercentage: number;
  createdAt: Date;
  updatedAt: Date;
  lastAccessedAt: Date;
  settings: {
    autoSave: boolean;
    autoSaveInterval: number; // in seconds
    showWordCount: boolean;
    showProgressBar: boolean;
    aiAssistanceEnabled: boolean;
    writingTipsEnabled: boolean;
  };
}

export interface AIOperation {
  id: string;
  type: 'outline_generation' | 'content_drafting' | 'revision' | 'feedback' | 'improvement';
  status: 'pending' | 'processing' | 'completed' | 'failed';
  input: {
    prompt?: string;
    selectedText?: string;
    context?: string;
    operation?: 'improve_style' | 'shorten' | 'elaborate' | 'clarify' | 'fix_grammar';
  };
  output?: {
    content?: string;
    suggestions?: string[];
    feedback?: string;
    outline?: OutlineItem[];
  };
  createdAt: Date;
  completedAt?: Date;
  error?: string;
}

export interface WritingTip {
  id: string;
  category: 'structure' | 'style' | 'grammar' | 'content' | 'revision';
  title: string;
  description: string;
  example?: string;
  isContextual: boolean;
  triggerConditions?: {
    wordCount?: { min?: number; max?: number };
    essayType?: string[];
    writingStage?: 'outline' | 'draft' | 'revision';
  };
}

export interface EssaySession {
  id: string;
  essayId: string;
  startTime: Date;
  endTime?: Date;
  duration: number; // in seconds
  wordsWritten: number;
  revisionsCount: number;
  aiInteractions: number;
  activityLog: {
    timestamp: Date;
    action: string;
    details?: any;
  }[];
}

export interface UserPreferences {
  panelSizes: {
    left: number;
    right: number;
  };
  collapsedPanels: {
    left: boolean;
    right: boolean;
  };
  activeView: 'outline' | 'brainstorm';
  editorSettings: {
    fontSize: number;
    lineHeight: number;
    showLineNumbers: boolean;
    showParagraphNumbers: boolean;
    highlightCurrentParagraph: boolean;
  };
  aiSettings: {
    autoSuggestions: boolean;
    suggestionDelay: number;
    preferredTone: 'formal' | 'casual' | 'academic' | 'personal';
    improvementTypes: string[];
  };
  writingTips: {
    enabled: boolean;
    categories: string[];
    showContextual: boolean;
  };
}

export interface ComparisonState {
  isActive: boolean;
  leftVersionId: string;
  rightVersionId: string;
  showDiffOnly: boolean;
  diffType: 'words' | 'sentences' | 'paragraphs';
}

export interface EssayEditorState {
  currentEssay: Essay | null;
  currentUniversity: University | null;
  currentPrompt: EssayPrompt | null;
  activeVersionId: string | null;
  versions: EssayVersion[];
  outline: OutlineItem[];
  isLoading: boolean;
  isSaving: boolean;
  lastSaved: Date | null;
  aiOperations: AIOperation[];
  userPreferences: UserPreferences;
  comparisonState: ComparisonState;
  writingTips: WritingTip[];
  session: EssaySession | null;
  errors: {
    type: 'save' | 'load' | 'ai' | 'validation';
    message: string;
    timestamp: Date;
  }[];
}

export interface EssayEditorActions {
  // Essay management
  loadEssay: (essayId: string) => Promise<void>;
  saveEssay: (isAutoSave?: boolean) => Promise<void>;
  createEssay: (universityId: string, promptId: string) => Promise<void>;
  deleteEssay: (essayId: string) => Promise<void>;
  
  // Content editing
  updateContent: (content: string) => void;
  updateTitle: (title: string) => void;
  
  // Version management
  createVersion: (changeType: EssayVersion['changeType'], changeSummary?: string) => void;
  loadVersion: (versionId: string) => void;
  compareVersions: (leftVersionId: string, rightVersionId: string) => void;
  restoreVersion: (versionId: string) => void;
  
  // Outline management
  updateOutline: (outline: OutlineItem[]) => void;
  addOutlineItem: (text: string, parentId?: string) => void;
  updateOutlineItem: (id: string, updates: Partial<OutlineItem>) => void;
  deleteOutlineItem: (id: string) => void;
  reorderOutlineItems: (items: OutlineItem[]) => void;
  
  // AI operations
  generateOutline: (prompt: string) => Promise<void>;
  draftContent: (sectionId?: string) => Promise<void>;
  improveText: (text: string, improvementType: string) => Promise<void>;
  getFeedback: () => Promise<void>;
  
  // UI state
  updatePreferences: (preferences: Partial<UserPreferences>) => void;
  togglePanel: (panel: 'left' | 'right') => void;
  resizePanel: (panel: 'left' | 'right', size: number) => void;
  
  // Utility
  calculateWordCount: (content: string) => number;
  getProgressPercentage: () => number;
  clearErrors: () => void;
}

export type EssayEditorContext = EssayEditorState & {
  actions: EssayEditorActions;
};

// Utility types
export type DraftingMode = 'paragraph' | 'section' | 'full' | 'revision';
export type AIOperationType = AIOperation['type'];
export type ImprovementType = 'style' | 'clarity' | 'tone' | 'length' | 'grammar';
export type WritingStage = 'setup' | 'outline' | 'draft' | 'revision' | 'complete';

export interface WordCountState {
  current: number;
  max: number;
  percentage: number;
  status: 'under' | 'approaching' | 'near' | 'over';
  trend: 'increasing' | 'decreasing' | 'stable';
}

export interface PanelState {
  width: number;
  isCollapsed: boolean;
  isResizing: boolean;
  minWidth: number;
  maxWidth: number;
}

export interface SelectionState {
  start: number;
  end: number;
  text: string;
  isActive: boolean;
} 