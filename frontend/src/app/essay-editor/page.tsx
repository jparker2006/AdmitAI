'use client';

import { useState, useRef, useCallback, useEffect } from 'react';
import { EssayEditorProvider } from '../../context/essay-editor-context';
import DashboardLayout from '../../components/DashboardLayout';
import ChatSidebar from '../../components/ChatSidebar';
import { 
  Edit3, 
  Save, 
  Settings, 
  Clock,
  MessageCircle,
  Bold,
  Italic,
  Sparkles,
  Target,
  Copy,
  Scissors,
  Clipboard,
  MousePointer2,
  X
} from 'lucide-react';

// Component imports
import WordCountTracker from '../../components/essay-editor/WordCountTracker';
import EssayTreeView from '../../components/essay-editor/EssayTreeView';
import RecentEssayTabs from '../../components/essay-editor/RecentEssayTabs';
import PanelResizer from '../../components/essay-editor/PanelResizer';

// Data imports
import { 
  mockEssayData, 
  findDraftById, 
  findPromptById,
  School,
  EssayPrompt,
  EssayDraft
} from '../../lib/mock-essays';

interface TabData {
  id: string;
  schoolId: string;
  promptId: string;
  draftId: string;
  title: string;
  isActive: boolean;
  isPinned: boolean;
  hasUnsavedChanges: boolean;
}

interface FloatingToolbarState {
  isVisible: boolean;
  position: { x: number; y: number };
  selectedText: string;
}

function EssayEditorPage() {
  // Panel state
  const [leftPanelWidth, setLeftPanelWidth] = useState(280);
  const [isLeftPanelCollapsed, setIsLeftPanelCollapsed] = useState(false);
  
  // Essay data state
  const [essayData, setEssayData] = useState(mockEssayData);
  const [currentDraft, setCurrentDraft] = useState<EssayDraft | null>(null);
  const [currentSchool, setCurrentSchool] = useState<School | null>(null);
  const [currentPrompt, setCurrentPrompt] = useState<EssayPrompt | null>(null);
  
  // Tabs state
  const [recentTabs, setRecentTabs] = useState<TabData[]>(
    essayData.recentTabs.map(tab => ({
      id: tab.id,
      schoolId: tab.schoolId,
      promptId: tab.promptId,
      draftId: tab.draftId,
      title: tab.title,
      isActive: tab.isActive,
      isPinned: tab.isPinned,
      hasUnsavedChanges: tab.hasUnsavedChanges
    }))
  );

  // AI Chat state
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [chatWidth] = useState(320);

  // Editor state
  const [content, setContent] = useState('');

  // Floating toolbar state
  const [floatingToolbar, setFloatingToolbar] = useState<FloatingToolbarState>({
    isVisible: false,
    position: { x: 0, y: 0 },
    selectedText: ''
  });

  // Context menu state
  const [contextMenu, setContextMenu] = useState<{
    isVisible: boolean;
    position: { x: number; y: number };
    hasSelection: boolean;
  }>({
    isVisible: false,
    position: { x: 0, y: 0 },
    hasSelection: false
  });

  // Focus mode state
  const [isFocusMode, setIsFocusMode] = useState(false);

  // Responsive state
  const [isMobile, setIsMobile] = useState(false);
  const [isTablet, setIsTablet] = useState(false);

  // Refs
  const editorRef = useRef<HTMLTextAreaElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const selectionTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Initialize with the first active tab
  useEffect(() => {
    const activeTab = recentTabs.find(tab => tab.isActive);
    if (activeTab) {
      const result = findDraftById(activeTab.draftId);
      if (result) {
        setCurrentDraft(result.draft);
        setCurrentSchool(result.school);
        setCurrentPrompt(result.prompt);
        setContent(result.draft.content);
      }
    }
  }, [recentTabs]);

  // Handle draft selection from tree
  const handleDraftSelection = useCallback((schoolId: string, promptId: string, draftId: string) => {
    const result = findDraftById(draftId);
    if (result) {
      setCurrentDraft(result.draft);
      setCurrentSchool(result.school);
      setCurrentPrompt(result.prompt);
      setContent(result.draft.content);
      
      // Update or add tab
      const existingTabIndex = recentTabs.findIndex(tab => tab.draftId === draftId);
      if (existingTabIndex >= 0) {
        // Tab exists, make it active
        setRecentTabs(tabs => tabs.map((tab, index) => ({
          ...tab,
          isActive: index === existingTabIndex
        })));
      } else {
        // Create new tab
        const newTab: TabData = {
          id: `tab-${draftId}`,
          schoolId,
          promptId,
          draftId,
          title: `${result.school.shortName} - ${result.prompt.title} - ${result.draft.version}`,
          isActive: true,
          isPinned: false,
          hasUnsavedChanges: false
        };
        
        setRecentTabs(tabs => [
          ...tabs.map(tab => ({ ...tab, isActive: false })),
          newTab
        ]);
      }
    }
  }, [recentTabs]);

  // Handle tab selection
  const handleTabSelect = useCallback((tabId: string) => {
    const tab = recentTabs.find(t => t.id === tabId);
    if (tab) {
      const result = findDraftById(tab.draftId);
      if (result) {
        setCurrentDraft(result.draft);
        setCurrentSchool(result.school);
        setCurrentPrompt(result.prompt);
        setContent(result.draft.content);
        
        setRecentTabs(tabs => tabs.map(t => ({
          ...t,
          isActive: t.id === tabId
        })));
      }
    }
  }, [recentTabs]);

  // Handle tab close
  const handleTabClose = useCallback((tabId: string) => {
    setRecentTabs(tabs => {
      const newTabs = tabs.filter(t => t.id !== tabId);
      
      // If we closed the active tab, make another tab active
      const closedTab = tabs.find(t => t.id === tabId);
      if (closedTab?.isActive && newTabs.length > 0) {
        newTabs[0].isActive = true;
        // Load the content for the new active tab
        const result = findDraftById(newTabs[0].draftId);
        if (result) {
          setCurrentDraft(result.draft);
          setCurrentSchool(result.school);
          setCurrentPrompt(result.prompt);
          setContent(result.draft.content);
        }
      }
      
      return newTabs;
    });
  }, []);

  // Handle tab pin/unpin
  const handleTabPin = useCallback((tabId: string) => {
    setRecentTabs(tabs => tabs.map(t => 
      t.id === tabId ? { ...t, isPinned: true } : t
    ));
  }, []);

  const handleTabUnpin = useCallback((tabId: string) => {
    setRecentTabs(tabs => tabs.map(t => 
      t.id === tabId ? { ...t, isPinned: false } : t
    ));
  }, []);

  // Handle tab reorder
  const handleTabReorder = useCallback((fromIndex: number, toIndex: number) => {
    setRecentTabs(tabs => {
      const newTabs = [...tabs];
      const [movedTab] = newTabs.splice(fromIndex, 1);
      newTabs.splice(toIndex, 0, movedTab);
      return newTabs;
    });
  }, []);

  // Handle tab duplicate
  const handleTabDuplicate = useCallback((tabId: string) => {
    const tab = recentTabs.find(t => t.id === tabId);
    if (tab) {
      const newTab: TabData = {
        ...tab,
        id: `tab-${tab.draftId}-copy-${Date.now()}`,
        title: `${tab.title} (Copy)`,
        isActive: false,
        isPinned: false,
        hasUnsavedChanges: false
      };
      
      setRecentTabs(tabs => [...tabs, newTab]);
    }
  }, [recentTabs]);

  // Handle panel collapse toggle
  const handlePanelCollapseToggle = useCallback(() => {
    setIsLeftPanelCollapsed(prev => !prev);
  }, []);

  // Handle panel width change
  const handlePanelWidthChange = useCallback((width: number) => {
    setLeftPanelWidth(width);
  }, []);

  const toggleChat = useCallback(() => {
    setIsChatOpen(prev => !prev);
  }, []);

  // Text selection handler for floating toolbar with debouncing
  const handleTextSelection = useCallback(() => {
    if (selectionTimeoutRef.current) {
      clearTimeout(selectionTimeoutRef.current);
    }

    selectionTimeoutRef.current = setTimeout(() => {
      const selection = window.getSelection();
      if (selection && selection.toString().length > 0) {
        const range = selection.getRangeAt(0);
        const rect = range.getBoundingClientRect();
        
        if (selection.toString().trim().length > 3) {
          setFloatingToolbar({
            isVisible: true,
            position: {
              x: Math.max(100, Math.min(rect.left + rect.width / 2, window.innerWidth - 100)),
              y: Math.max(60, rect.top - 10)
            },
            selectedText: selection.toString()
          });
        } else {
          setFloatingToolbar(prev => ({ ...prev, isVisible: false }));
        }
      } else {
        setFloatingToolbar(prev => ({ ...prev, isVisible: false }));
      }
    }, 150);
  }, []);

  // Handle mouse up to detect selection end
  const handleMouseUp = useCallback(() => {
    handleTextSelection();
  }, [handleTextSelection]);

  // Handle selection clearing
  const handleSelectionClear = useCallback(() => {
    setFloatingToolbar(prev => ({ ...prev, isVisible: false }));
  }, []);

  // Handle right-click context menu
  const handleContextMenu = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    const selection = window.getSelection();
    const hasSelection = selection && selection.toString().length > 0;
    
    setContextMenu({
      isVisible: true,
      position: {
        x: Math.min(e.clientX, window.innerWidth - 200),
        y: Math.min(e.clientY, window.innerHeight - 200)
      },
      hasSelection: !!hasSelection
    });
  }, []);

  // Handle context menu actions
  const handleContextMenuAction = useCallback((action: string) => {
    const selection = window.getSelection();
    
    switch (action) {
      case 'cut':
        if (selection && selection.toString().length > 0) {
          navigator.clipboard.writeText(selection.toString());
        }
        break;
      case 'copy':
        if (selection && selection.toString().length > 0) {
          navigator.clipboard.writeText(selection.toString());
        }
        break;
      case 'paste':
        navigator.clipboard.readText().then(text => {
          console.log('Pasting:', text);
        });
        break;
      case 'selectAll':
        editorRef.current?.select();
        break;
      case 'improve':
        console.log('Improving text:', selection?.toString());
        break;
      case 'expand':
        console.log('Expanding text:', selection?.toString());
        break;
    }
    
    setContextMenu(prev => ({ ...prev, isVisible: false }));
  }, []);

  // Close context menu on click outside
  const handleClickOutside = useCallback(() => {
    setContextMenu(prev => ({ ...prev, isVisible: false }));
  }, []);

  // Add global event listeners for text selection
  useEffect(() => {
    document.addEventListener('mouseup', handleMouseUp);
    document.addEventListener('selectionchange', handleSelectionClear);
    document.addEventListener('click', handleClickOutside);
    
    return () => {
      document.removeEventListener('mouseup', handleMouseUp);
      document.removeEventListener('selectionchange', handleSelectionClear);
      document.removeEventListener('click', handleClickOutside);
      if (selectionTimeoutRef.current) {
        clearTimeout(selectionTimeoutRef.current);
      }
    };
  }, [handleMouseUp, handleSelectionClear, handleClickOutside]);

  // Responsive detection
  useEffect(() => {
    const handleResize = () => {
      const width = window.innerWidth;
      setIsMobile(width < 768);
      setIsTablet(width >= 768 && width < 1024);
    };

    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Auto-save functionality
  const [lastSaved, setLastSaved] = useState<Date>(new Date());
  const [isAutoSaving, setIsAutoSaving] = useState(false);

  useEffect(() => {
    const autoSaveTimer = setTimeout(() => {
      setIsAutoSaving(true);
      setTimeout(() => {
        setLastSaved(new Date());
        setIsAutoSaving(false);
      }, 500);
    }, 2000);

    return () => clearTimeout(autoSaveTimer);
  }, [content]);

  const formatTimestamp = (date: Date) => {
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / 60000);
    
    if (minutes < 1) return 'Just now';
    if (minutes < 60) return `${minutes} min ago`;
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <EssayEditorProvider>
      <DashboardLayout>
        <div className="flex flex-col h-screen bg-gray-50 dark:bg-gray-900 overflow-hidden">
          {/* Top Toolbar */}
          <div className={`bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 py-4 flex items-center justify-between transition-opacity duration-300 ${isFocusMode ? 'opacity-20 hover:opacity-100' : ''}`}>
            {/* Left Section */}
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <Edit3 className="w-6 h-6 text-blue-600 dark:text-blue-400" />
                <h1 className="text-xl font-semibold text-gray-900 dark:text-white">
                  Essay Editor v3
                </h1>
              </div>
              {currentSchool && currentPrompt && (
                <div className="flex items-center space-x-2 bg-gray-50 dark:bg-gray-700 rounded-lg px-3 py-1">
                  <span className="text-sm text-gray-700 dark:text-gray-300">
                    {currentSchool.name} - {currentPrompt.title}
                  </span>
                </div>
              )}
            </div>

            {/* Center Section - Word Count */}
            <div className="flex items-center space-x-6">
              {currentPrompt && (
                <WordCountTracker 
                  content={content}
                  maxWords={currentPrompt.wordLimit}
                  universityName={currentSchool?.shortName || 'Unknown'}
                  showCharacters={!isMobile}
                  showProgress={!isMobile}
                />
              )}
              {!isMobile && (
                <div className="flex items-center space-x-2 text-sm text-gray-500 dark:text-gray-400">
                  <Clock className="w-4 h-4" />
                  <span>
                    {isAutoSaving ? 'Saving...' : `Saved ${formatTimestamp(lastSaved)}`}
                  </span>
                </div>
              )}
            </div>

            {/* Right Section */}
            <div className="flex items-center space-x-3">
              {!isMobile && (
                <button className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg">
                  <Settings className="w-5 h-5 text-gray-500 dark:text-gray-400" />
                </button>
              )}
              <button className="flex items-center space-x-2 px-3 py-1.5 bg-green-600 text-white rounded-lg hover:bg-green-700 text-sm">
                <Save className="w-4 h-4" />
                <span className={isMobile ? 'hidden' : ''}>Save</span>
              </button>
            </div>
          </div>

          {/* Recent Tabs Row */}
          <RecentEssayTabs
            tabs={recentTabs}
            onTabSelect={handleTabSelect}
            onTabClose={handleTabClose}
            onTabPin={handleTabPin}
            onTabUnpin={handleTabUnpin}
            onTabReorder={handleTabReorder}
            onTabDuplicate={handleTabDuplicate}
          />

          {/* Main Content Area */}
          <div className="flex-1 flex overflow-hidden relative">
            {/* Left Panel with Tree View */}
            {!isLeftPanelCollapsed && (
              <div 
                className="bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 flex-shrink-0 relative"
                style={{ width: leftPanelWidth }}
              >
                <EssayTreeView
                  onSelectDraft={handleDraftSelection}
                  selectedDraftId={currentDraft?.id}
                  className="h-full"
                />
                
                {/* Panel Resizer */}
                <div className="absolute right-0 top-0 bottom-0">
                  <PanelResizer
                    defaultWidth={280}
                    minWidth={200}
                    maxWidth={400}
                    isCollapsed={isLeftPanelCollapsed}
                    onWidthChange={handlePanelWidthChange}
                    onCollapseToggle={handlePanelCollapseToggle}
                  />
                </div>
              </div>
            )}

            {/* Collapsed Panel Button */}
            {isLeftPanelCollapsed && (
              <div className="w-12 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 flex-shrink-0 relative">
                <PanelResizer
                  defaultWidth={280}
                  minWidth={200}
                  maxWidth={400}
                  isCollapsed={isLeftPanelCollapsed}
                  onWidthChange={handlePanelWidthChange}
                  onCollapseToggle={handlePanelCollapseToggle}
                />
              </div>
            )}

            {/* Main Editor */}
            <div className="flex-1 flex flex-col overflow-hidden">
              <div className="flex-1 p-6 overflow-y-auto">
                <div className="max-w-none mx-auto">
                  <textarea
                    ref={editorRef}
                    value={content}
                    onChange={(e) => setContent(e.target.value)}
                    onContextMenu={handleContextMenu}
                    className="w-full h-full resize-none border-none outline-none bg-transparent text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 leading-relaxed text-lg"
                    placeholder={currentDraft ? "Continue writing your essay..." : "Select an essay from the left panel to start editing"}
                    style={{ minHeight: 'calc(100vh - 200px)' }}
                    aria-label="Essay content editor"
                    spellCheck="true"
                  />
                </div>
              </div>
            </div>

            {/* Right AI Chat Icon */}
            {!isMobile && (
              <div className={`bg-white dark:bg-gray-800 border-l border-gray-200 dark:border-gray-700 flex flex-col justify-center py-4 transition-opacity duration-300 ${isFocusMode ? 'opacity-20 hover:opacity-100' : ''}`}>
                <div className="px-2">
                  <button
                    onClick={toggleChat}
                    className={`p-3 rounded-lg transition-colors ${isChatOpen ? 'bg-blue-100 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400' : 'hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-500 dark:text-gray-400'}`}
                    title="AI Assistant"
                  >
                    <MessageCircle className="w-5 h-5" />
                  </button>
                </div>
              </div>
            )}

            {/* Floating Toolbar */}
            {floatingToolbar.isVisible && (
              <div
                className="absolute z-50 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg p-2 flex items-center space-x-1 animate-in fade-in duration-200"
                style={{
                  left: floatingToolbar.position.x - 100,
                  top: floatingToolbar.position.y - 40
                }}
              >
                <button className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded">
                  <Bold className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                </button>
                <button className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded">
                  <Italic className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                </button>
                <div className="w-px h-6 bg-gray-300 dark:bg-gray-600" />
                <button className="flex items-center space-x-1 px-2 py-1 bg-blue-600 text-white rounded text-sm hover:bg-blue-700">
                  <Sparkles className="w-3 h-3" />
                  <span>Improve</span>
                </button>
                <button className="flex items-center space-x-1 px-2 py-1 bg-green-600 text-white rounded text-sm hover:bg-green-700">
                  <Target className="w-3 h-3" />
                  <span>Expand</span>
                </button>
              </div>
            )}

            {/* Context Menu */}
            {contextMenu.isVisible && (
              <div
                className="absolute z-50 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg py-2 min-w-[180px] animate-in fade-in duration-150"
                style={{
                  left: contextMenu.position.x,
                  top: contextMenu.position.y
                }}
              >
                {contextMenu.hasSelection && (
                  <>
                    <button
                      onClick={() => handleContextMenuAction('cut')}
                      className="w-full px-4 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center space-x-3"
                    >
                      <Scissors className="w-4 h-4" />
                      <span>Cut</span>
                    </button>
                    <button
                      onClick={() => handleContextMenuAction('copy')}
                      className="w-full px-4 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center space-x-3"
                    >
                      <Copy className="w-4 h-4" />
                      <span>Copy</span>
                    </button>
                    <div className="border-t border-gray-200 dark:border-gray-700 my-1" />
                    <button
                      onClick={() => handleContextMenuAction('improve')}
                      className="w-full px-4 py-2 text-left text-sm text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 flex items-center space-x-3"
                    >
                      <Sparkles className="w-4 h-4" />
                      <span>Improve with AI</span>
                    </button>
                    <button
                      onClick={() => handleContextMenuAction('expand')}
                      className="w-full px-4 py-2 text-left text-sm text-green-600 dark:text-green-400 hover:bg-green-50 dark:hover:bg-green-900/20 flex items-center space-x-3"
                    >
                      <Target className="w-4 h-4" />
                      <span>Expand with AI</span>
                    </button>
                    <div className="border-t border-gray-200 dark:border-gray-700 my-1" />
                  </>
                )}
                <button
                  onClick={() => handleContextMenuAction('paste')}
                  className="w-full px-4 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center space-x-3"
                >
                  <Clipboard className="w-4 h-4" />
                  <span>Paste</span>
                </button>
                <button
                  onClick={() => handleContextMenuAction('selectAll')}
                  className="w-full px-4 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center space-x-3"
                >
                  <MousePointer2 className="w-4 h-4" />
                  <span>Select All</span>
                </button>
              </div>
            )}

            {/* AI Chat Overlay */}
            {isChatOpen && (
              <div className="absolute inset-0 z-40 flex">
                <div className="flex-1" onClick={toggleChat} />
                <div className="w-80 h-full animate-slide-in-right">
                  <ChatSidebar
                    isCollapsed={false}
                    onToggleCollapse={toggleChat}
                    width={chatWidth}
                  />
                </div>
              </div>
            )}
          </div>
        </div>
      </DashboardLayout>
    </EssayEditorProvider>
  );
}

export default EssayEditorPage; 