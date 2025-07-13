'use client';

import { createContext, useContext, useReducer, useCallback, useEffect } from 'react';
import { 
  EssayEditorState, 
  EssayEditorActions, 
  EssayEditorContext as EssayEditorContextType,
  Essay,
  EssayVersion,
  OutlineItem,
  UserPreferences,
  ComparisonState,
  AIOperation,
  University,
  EssayPrompt,
  WordCountState,
  EssaySession
} from '../types/essay';

// Initial state
const initialState: EssayEditorState = {
  currentEssay: null,
  currentUniversity: null,
  currentPrompt: null,
  activeVersionId: null,
  versions: [],
  outline: [],
  isLoading: false,
  isSaving: false,
  lastSaved: null,
  aiOperations: [],
  userPreferences: {
    panelSizes: { left: 40, right: 60 },
    collapsedPanels: { left: false, right: false },
    activeView: 'outline',
    editorSettings: {
      fontSize: 16,
      lineHeight: 1.5,
      showLineNumbers: false,
      showParagraphNumbers: true,
      highlightCurrentParagraph: true,
    },
    aiSettings: {
      autoSuggestions: true,
      suggestionDelay: 1000,
      preferredTone: 'academic',
      improvementTypes: ['style', 'clarity', 'grammar'],
    },
    writingTips: {
      enabled: true,
      categories: ['structure', 'style', 'content'],
      showContextual: true,
    },
  },
  comparisonState: {
    isActive: false,
    leftVersionId: '',
    rightVersionId: '',
    showDiffOnly: false,
    diffType: 'words',
  },
  writingTips: [],
  session: null,
  errors: [],
};

// Action types
type EssayEditorAction = 
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_SAVING'; payload: boolean }
  | { type: 'SET_CURRENT_ESSAY'; payload: Essay | null }
  | { type: 'SET_CURRENT_UNIVERSITY'; payload: University | null }
  | { type: 'SET_CURRENT_PROMPT'; payload: EssayPrompt | null }
  | { type: 'SET_ACTIVE_VERSION'; payload: string | null }
  | { type: 'SET_VERSIONS'; payload: EssayVersion[] }
  | { type: 'ADD_VERSION'; payload: EssayVersion }
  | { type: 'UPDATE_OUTLINE'; payload: OutlineItem[] }
  | { type: 'UPDATE_CONTENT'; payload: string }
  | { type: 'UPDATE_TITLE'; payload: string }
  | { type: 'UPDATE_PREFERENCES'; payload: Partial<UserPreferences> }
  | { type: 'SET_COMPARISON_STATE'; payload: ComparisonState }
  | { type: 'ADD_AI_OPERATION'; payload: AIOperation }
  | { type: 'UPDATE_AI_OPERATION'; payload: { id: string; updates: Partial<AIOperation> } }
  | { type: 'SET_SESSION'; payload: EssaySession | null }
  | { type: 'ADD_ERROR'; payload: { type: 'save' | 'load' | 'ai' | 'validation'; message: string } }
  | { type: 'CLEAR_ERRORS' }
  | { type: 'SET_LAST_SAVED'; payload: Date | null };

// Reducer
function essayEditorReducer(state: EssayEditorState, action: EssayEditorAction): EssayEditorState {
  switch (action.type) {
    case 'SET_LOADING':
      return { ...state, isLoading: action.payload };
    
    case 'SET_SAVING':
      return { ...state, isSaving: action.payload };
    
    case 'SET_CURRENT_ESSAY':
      return { ...state, currentEssay: action.payload };
    
    case 'SET_CURRENT_UNIVERSITY':
      return { ...state, currentUniversity: action.payload };
    
    case 'SET_CURRENT_PROMPT':
      return { ...state, currentPrompt: action.payload };
    
    case 'SET_ACTIVE_VERSION':
      return { ...state, activeVersionId: action.payload };
    
    case 'SET_VERSIONS':
      return { ...state, versions: action.payload };
    
    case 'ADD_VERSION':
      return { ...state, versions: [...state.versions, action.payload] };
    
    case 'UPDATE_OUTLINE':
      return { 
        ...state, 
        outline: action.payload,
        currentEssay: state.currentEssay ? {
          ...state.currentEssay,
          outline: action.payload,
          updatedAt: new Date()
        } : null
      };
    
    case 'UPDATE_CONTENT':
      return {
        ...state,
        currentEssay: state.currentEssay ? {
          ...state.currentEssay,
          currentContent: action.payload,
          currentWordCount: action.payload.split(/\s+/).filter(word => word.length > 0).length,
          updatedAt: new Date()
        } : null
      };
    
    case 'UPDATE_TITLE':
      return {
        ...state,
        currentEssay: state.currentEssay ? {
          ...state.currentEssay,
          title: action.payload,
          updatedAt: new Date()
        } : null
      };
    
    case 'UPDATE_PREFERENCES':
      return {
        ...state,
        userPreferences: {
          ...state.userPreferences,
          ...action.payload
        }
      };
    
    case 'SET_COMPARISON_STATE':
      return { ...state, comparisonState: action.payload };
    
    case 'ADD_AI_OPERATION':
      return { ...state, aiOperations: [...state.aiOperations, action.payload] };
    
    case 'UPDATE_AI_OPERATION':
      return {
        ...state,
        aiOperations: state.aiOperations.map(op => 
          op.id === action.payload.id ? { ...op, ...action.payload.updates } : op
        )
      };
    
    case 'SET_SESSION':
      return { ...state, session: action.payload };
    
    case 'ADD_ERROR':
      return {
        ...state,
        errors: [...state.errors, {
          ...action.payload,
          timestamp: new Date()
        }]
      };
    
    case 'CLEAR_ERRORS':
      return { ...state, errors: [] };
    
    case 'SET_LAST_SAVED':
      return { ...state, lastSaved: action.payload };
    
    default:
      return state;
  }
}

// Context
const EssayEditorContext = createContext<EssayEditorContextType | null>(null);

// Provider component
export function EssayEditorProvider({ children }: { children: React.ReactNode }) {
  const [state, dispatch] = useReducer(essayEditorReducer, initialState);

  // Utility functions
  const calculateWordCount = useCallback((content: string): number => {
    return content.split(/\s+/).filter(word => word.length > 0).length;
  }, []);

  const getProgressPercentage = useCallback((): number => {
    if (!state.currentEssay || !state.currentPrompt) return 0;
    const wordCount = state.currentEssay.currentWordCount;
    const targetCount = state.currentPrompt.wordLimit;
    return Math.min((wordCount / targetCount) * 100, 100);
  }, [state.currentEssay, state.currentPrompt]);

  const generateId = useCallback((): string => {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
  }, []);

  // Actions
  const actions: EssayEditorActions = {
    // Essay management
    loadEssay: useCallback(async (essayId: string) => {
      dispatch({ type: 'SET_LOADING', payload: true });
      try {
        // TODO: Implement API call to load essay
        // const essay = await api.getEssay(essayId);
        // dispatch({ type: 'SET_CURRENT_ESSAY', payload: essay });
        
        // Mock implementation
        setTimeout(() => {
          dispatch({ type: 'SET_LOADING', payload: false });
        }, 1000);
      } catch (error) {
        dispatch({ type: 'ADD_ERROR', payload: { type: 'load', message: 'Failed to load essay' } });
        dispatch({ type: 'SET_LOADING', payload: false });
      }
    }, []),

    saveEssay: useCallback(async (isAutoSave = false) => {
      if (!state.currentEssay) return;
      
      dispatch({ type: 'SET_SAVING', payload: true });
      try {
        // TODO: Implement API call to save essay
        // await api.saveEssay(state.currentEssay);
        
        // Mock implementation
        setTimeout(() => {
          dispatch({ type: 'SET_LAST_SAVED', payload: new Date() });
          dispatch({ type: 'SET_SAVING', payload: false });
        }, 500);
      } catch (error) {
        dispatch({ type: 'ADD_ERROR', payload: { type: 'save', message: 'Failed to save essay' } });
        dispatch({ type: 'SET_SAVING', payload: false });
      }
    }, [state.currentEssay]),

    createEssay: useCallback(async (universityId: string, promptId: string) => {
      dispatch({ type: 'SET_LOADING', payload: true });
      try {
        const newEssay: Essay = {
          id: generateId(),
          userId: 'current-user', // TODO: Get from auth context
          universityId,
          promptId,
          title: 'Untitled Essay',
          currentContent: '',
          currentWordCount: 0,
          currentVersionId: '',
          outline: [],
          status: 'draft',
          progressPercentage: 0,
          createdAt: new Date(),
          updatedAt: new Date(),
          lastAccessedAt: new Date(),
          settings: {
            autoSave: true,
            autoSaveInterval: 30,
            showWordCount: true,
            showProgressBar: true,
            aiAssistanceEnabled: true,
            writingTipsEnabled: true,
          },
        };
        
        dispatch({ type: 'SET_CURRENT_ESSAY', payload: newEssay });
        dispatch({ type: 'SET_LOADING', payload: false });
      } catch (error) {
        dispatch({ type: 'ADD_ERROR', payload: { type: 'save', message: 'Failed to create essay' } });
        dispatch({ type: 'SET_LOADING', payload: false });
      }
    }, [generateId]),

    deleteEssay: useCallback(async (essayId: string) => {
      try {
        // TODO: Implement API call to delete essay
        // await api.deleteEssay(essayId);
        
        if (state.currentEssay?.id === essayId) {
          dispatch({ type: 'SET_CURRENT_ESSAY', payload: null });
        }
      } catch (error) {
        dispatch({ type: 'ADD_ERROR', payload: { type: 'save', message: 'Failed to delete essay' } });
      }
    }, [state.currentEssay]),

    // Content editing
    updateContent: useCallback((content: string) => {
      dispatch({ type: 'UPDATE_CONTENT', payload: content });
    }, []),

    updateTitle: useCallback((title: string) => {
      dispatch({ type: 'UPDATE_TITLE', payload: title });
    }, []),

    // Version management
    createVersion: useCallback((changeType: EssayVersion['changeType'], changeSummary?: string) => {
      if (!state.currentEssay) return;
      
      const newVersion: EssayVersion = {
        id: generateId(),
        essayId: state.currentEssay.id,
        content: state.currentEssay.currentContent,
        wordCount: state.currentEssay.currentWordCount,
        isAutoSave: changeType === 'draft',
        versionNumber: state.versions.length + 1,
        changeType,
        changeSummary,
        createdAt: new Date(),
      };
      
      dispatch({ type: 'ADD_VERSION', payload: newVersion });
      dispatch({ type: 'SET_ACTIVE_VERSION', payload: newVersion.id });
    }, [state.currentEssay, state.versions.length, generateId]),

    loadVersion: useCallback((versionId: string) => {
      const version = state.versions.find(v => v.id === versionId);
      if (version && state.currentEssay) {
        dispatch({ type: 'UPDATE_CONTENT', payload: version.content });
        dispatch({ type: 'SET_ACTIVE_VERSION', payload: versionId });
      }
    }, [state.versions, state.currentEssay]),

    compareVersions: useCallback((leftVersionId: string, rightVersionId: string) => {
      dispatch({ 
        type: 'SET_COMPARISON_STATE', 
        payload: {
          isActive: true,
          leftVersionId,
          rightVersionId,
          showDiffOnly: false,
          diffType: 'words'
        }
      });
    }, []),

    restoreVersion: useCallback((versionId: string) => {
      const version = state.versions.find(v => v.id === versionId);
      if (version && state.currentEssay) {
        dispatch({ type: 'UPDATE_CONTENT', payload: version.content });
        actions.createVersion('manual_edit', `Restored from version ${version.versionNumber}`);
      }
    }, [state.versions, state.currentEssay]),

    // Outline management
    updateOutline: useCallback((outline: OutlineItem[]) => {
      dispatch({ type: 'UPDATE_OUTLINE', payload: outline });
    }, []),

    addOutlineItem: useCallback((text: string, parentId?: string) => {
      const newItem: OutlineItem = {
        id: generateId(),
        text,
        level: parentId ? 1 : 0,
        order: state.outline.length,
        parentId,
        isExpanded: true,
        isLocked: false,
        createdAt: new Date(),
        updatedAt: new Date(),
      };
      
      dispatch({ type: 'UPDATE_OUTLINE', payload: [...state.outline, newItem] });
    }, [state.outline, generateId]),

    updateOutlineItem: useCallback((id: string, updates: Partial<OutlineItem>) => {
      const updatedOutline = state.outline.map(item => 
        item.id === id ? { ...item, ...updates, updatedAt: new Date() } : item
      );
      dispatch({ type: 'UPDATE_OUTLINE', payload: updatedOutline });
    }, [state.outline]),

    deleteOutlineItem: useCallback((id: string) => {
      const updatedOutline = state.outline.filter(item => item.id !== id && item.parentId !== id);
      dispatch({ type: 'UPDATE_OUTLINE', payload: updatedOutline });
    }, [state.outline]),

    reorderOutlineItems: useCallback((items: OutlineItem[]) => {
      const reorderedItems = items.map((item, index) => ({ ...item, order: index }));
      dispatch({ type: 'UPDATE_OUTLINE', payload: reorderedItems });
    }, []),

    // AI operations
    generateOutline: useCallback(async (prompt: string) => {
      const operation: AIOperation = {
        id: generateId(),
        type: 'outline_generation',
        status: 'pending',
        input: { prompt },
        createdAt: new Date(),
      };
      
      dispatch({ type: 'ADD_AI_OPERATION', payload: operation });
      dispatch({ type: 'UPDATE_AI_OPERATION', payload: { id: operation.id, updates: { status: 'processing' } } });
      
      try {
        // TODO: Implement AI API call
        // const result = await ai.generateOutline(prompt);
        
        // Mock implementation
        setTimeout(() => {
          const mockOutline: OutlineItem[] = [
            {
              id: generateId(),
              text: 'Introduction',
              level: 0,
              order: 0,
              isExpanded: true,
              isLocked: false,
              createdAt: new Date(),
              updatedAt: new Date(),
            },
            {
              id: generateId(),
              text: 'Main Body',
              level: 0,
              order: 1,
              isExpanded: true,
              isLocked: false,
              createdAt: new Date(),
              updatedAt: new Date(),
            },
            {
              id: generateId(),
              text: 'Conclusion',
              level: 0,
              order: 2,
              isExpanded: true,
              isLocked: false,
              createdAt: new Date(),
              updatedAt: new Date(),
            },
          ];
          
          dispatch({ type: 'UPDATE_OUTLINE', payload: mockOutline });
          dispatch({ 
            type: 'UPDATE_AI_OPERATION', 
            payload: { 
              id: operation.id, 
              updates: { 
                status: 'completed', 
                output: { outline: mockOutline },
                completedAt: new Date()
              } 
            } 
          });
        }, 2000);
      } catch (error) {
        dispatch({ 
          type: 'UPDATE_AI_OPERATION', 
          payload: { 
            id: operation.id, 
            updates: { 
              status: 'failed', 
              error: 'Failed to generate outline' 
            } 
          } 
        });
      }
    }, [generateId]),

    draftContent: useCallback(async (sectionId?: string) => {
      const operation: AIOperation = {
        id: generateId(),
        type: 'content_drafting',
        status: 'pending',
        input: { context: sectionId },
        createdAt: new Date(),
      };
      
      dispatch({ type: 'ADD_AI_OPERATION', payload: operation });
      // TODO: Implement AI drafting logic
    }, [generateId]),

    improveText: useCallback(async (text: string, improvementType: string) => {
      const operation: AIOperation = {
        id: generateId(),
        type: 'improvement',
        status: 'pending',
        input: { 
          selectedText: text, 
          operation: improvementType as any 
        },
        createdAt: new Date(),
      };
      
      dispatch({ type: 'ADD_AI_OPERATION', payload: operation });
      // TODO: Implement AI improvement logic
    }, [generateId]),

    getFeedback: useCallback(async () => {
      if (!state.currentEssay) return;
      
      const operation: AIOperation = {
        id: generateId(),
        type: 'feedback',
        status: 'pending',
        input: { context: state.currentEssay.currentContent },
        createdAt: new Date(),
      };
      
      dispatch({ type: 'ADD_AI_OPERATION', payload: operation });
      // TODO: Implement AI feedback logic
    }, [state.currentEssay, generateId]),

    // UI state
    updatePreferences: useCallback((preferences: Partial<UserPreferences>) => {
      dispatch({ type: 'UPDATE_PREFERENCES', payload: preferences });
    }, []),

    togglePanel: useCallback((panel: 'left' | 'right') => {
      const isCollapsed = state.userPreferences.collapsedPanels[panel];
      dispatch({ 
        type: 'UPDATE_PREFERENCES', 
        payload: { 
          collapsedPanels: { 
            ...state.userPreferences.collapsedPanels, 
            [panel]: !isCollapsed 
          } 
        } 
      });
    }, [state.userPreferences.collapsedPanels]),

    resizePanel: useCallback((panel: 'left' | 'right', size: number) => {
      const otherSize = 100 - size;
      
      dispatch({ 
        type: 'UPDATE_PREFERENCES', 
        payload: { 
          panelSizes: panel === 'left' 
            ? { left: size, right: otherSize }
            : { left: otherSize, right: size }
        } 
      });
    }, []),

    // Utility
    calculateWordCount,
    getProgressPercentage,
    clearErrors: useCallback(() => {
      dispatch({ type: 'CLEAR_ERRORS' });
    }, []),
  };

  // Auto-save effect
  useEffect(() => {
    if (!state.currentEssay?.settings.autoSave) return;
    
    const interval = setInterval(() => {
      if (state.currentEssay && !state.isSaving) {
        actions.saveEssay(true);
      }
    }, (state.currentEssay?.settings.autoSaveInterval || 30) * 1000);
    
    return () => clearInterval(interval);
  }, [state.currentEssay, state.isSaving, actions]);

  const contextValue: EssayEditorContextType = {
    ...state,
    actions,
  };

  return (
    <EssayEditorContext.Provider value={contextValue}>
      {children}
    </EssayEditorContext.Provider>
  );
}

// Hook
export function useEssayEditor() {
  const context = useContext(EssayEditorContext);
  if (!context) {
    throw new Error('useEssayEditor must be used within an EssayEditorProvider');
  }
  return context;
} 