'use client';

import { useState, useRef, useCallback, useEffect } from 'react';
import { 
  X, 
  Pin, 
  MoreVertical, 
  ExternalLink, 
  Copy, 
  Circle,
  ChevronDown,
  ChevronLeft,
  ChevronRight
} from 'lucide-react';

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

interface RecentEssayTabsProps {
  tabs: TabData[];
  onTabSelect: (tabId: string) => void;
  onTabClose: (tabId: string) => void;
  onTabPin: (tabId: string) => void;
  onTabUnpin: (tabId: string) => void;
  onTabReorder: (fromIndex: number, toIndex: number) => void;
  onTabDuplicate: (tabId: string) => void;
  className?: string;
}

interface ContextMenuState {
  isOpen: boolean;
  position: { x: number; y: number };
  tabId: string | null;
}

interface DragState {
  isDragging: boolean;
  draggedTabId: string | null;
  draggedFromIndex: number | null;
  dragOverIndex: number | null;
}

const RecentEssayTabs: React.FC<RecentEssayTabsProps> = ({
  tabs,
  onTabSelect,
  onTabClose,
  onTabPin,
  onTabUnpin,
  onTabReorder,
  onTabDuplicate,
  className = ''
}) => {
  const [contextMenu, setContextMenu] = useState<ContextMenuState>({
    isOpen: false,
    position: { x: 0, y: 0 },
    tabId: null
  });
  const [dragState, setDragState] = useState<DragState>({
    isDragging: false,
    draggedTabId: null,
    draggedFromIndex: null,
    dragOverIndex: null
  });
  const [showOverflow, setShowOverflow] = useState(false);
  const [visibleTabs, setVisibleTabs] = useState<TabData[]>([]);
  const [overflowTabs, setOverflowTabs] = useState<TabData[]>([]);
  const [scrollPosition, setScrollPosition] = useState(0);

  const tabsContainerRef = useRef<HTMLDivElement>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null);

  // Calculate visible tabs based on container width
  const calculateVisibleTabs = useCallback(() => {
    if (!tabsContainerRef.current) return;

    const containerWidth = tabsContainerRef.current.offsetWidth;
    const moreButtonWidth = 80; // Approximate width of "More" button
    const availableWidth = containerWidth - moreButtonWidth;
    
    let accumulatedWidth = 0;
    let visibleCount = 0;
    
    // Estimate tab width (adjust based on actual measurements)
    const averageTabWidth = 200; // Approximate width per tab
    
    for (let i = 0; i < tabs.length; i++) {
      if (accumulatedWidth + averageTabWidth <= availableWidth) {
        accumulatedWidth += averageTabWidth;
        visibleCount++;
      } else {
        break;
      }
    }

    // Always show at least 1 tab and at most 5 tabs
    visibleCount = Math.min(Math.max(visibleCount, 1), 5);
    
    setVisibleTabs(tabs.slice(0, visibleCount));
    setOverflowTabs(tabs.slice(visibleCount));
  }, [tabs]);

  // Update visible tabs when tabs change or container resizes
  useEffect(() => {
    calculateVisibleTabs();
  }, [tabs, calculateVisibleTabs]);

  useEffect(() => {
    const handleResize = () => {
      calculateVisibleTabs();
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [calculateVisibleTabs]);

  // Handle tab selection
  const handleTabClick = useCallback((tabId: string) => {
    onTabSelect(tabId);
  }, [onTabSelect]);

  // Handle tab close
  const handleTabClose = useCallback((e: React.MouseEvent, tabId: string) => {
    e.stopPropagation();
    const tab = tabs.find(t => t.id === tabId);
    if (tab && !tab.isPinned) {
      onTabClose(tabId);
    }
  }, [tabs, onTabClose]);

  // Handle tab middle click (close)
  const handleTabMiddleClick = useCallback((e: React.MouseEvent, tabId: string) => {
    if (e.button === 1) { // Middle mouse button
      e.preventDefault();
      handleTabClose(e, tabId);
    }
  }, [handleTabClose]);

  // Handle context menu
  const handleContextMenu = useCallback((e: React.MouseEvent, tabId: string) => {
    e.preventDefault();
    e.stopPropagation();
    
    setContextMenu({
      isOpen: true,
      position: { x: e.clientX, y: e.clientY },
      tabId
    });
  }, []);

  // Close context menu
  const closeContextMenu = useCallback(() => {
    setContextMenu(prev => ({ ...prev, isOpen: false }));
  }, []);

  // Handle context menu actions
  const handleContextMenuAction = useCallback((action: string) => {
    if (!contextMenu.tabId) return;

    const tab = tabs.find(t => t.id === contextMenu.tabId);
    if (!tab) return;

    switch (action) {
      case 'pin':
        onTabPin(contextMenu.tabId);
        break;
      case 'unpin':
        onTabUnpin(contextMenu.tabId);
        break;
      case 'close':
        if (!tab.isPinned) {
          onTabClose(contextMenu.tabId);
        }
        break;
      case 'close-others':
        tabs.forEach(t => {
          if (t.id !== contextMenu.tabId && !t.isPinned) {
            onTabClose(t.id);
          }
        });
        break;
      case 'duplicate':
        onTabDuplicate(contextMenu.tabId);
        break;
      case 'open-new-window':
        // TODO: Implement new window functionality
        console.log('Open in new window:', contextMenu.tabId);
        break;
    }
    
    closeContextMenu();
  }, [contextMenu, tabs, onTabPin, onTabUnpin, onTabClose, onTabDuplicate, closeContextMenu]);

  // Drag and drop handlers
  const handleDragStart = useCallback((e: React.DragEvent, tabId: string, index: number) => {
    setDragState({
      isDragging: true,
      draggedTabId: tabId,
      draggedFromIndex: index,
      dragOverIndex: null
    });
    
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/plain', tabId);
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent, index: number) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    
    setDragState(prev => ({
      ...prev,
      dragOverIndex: index
    }));
  }, []);

  const handleDragLeave = useCallback(() => {
    setDragState(prev => ({
      ...prev,
      dragOverIndex: null
    }));
  }, []);

  const handleDrop = useCallback((e: React.DragEvent, index: number) => {
    e.preventDefault();
    
    if (dragState.draggedFromIndex !== null && dragState.draggedFromIndex !== index) {
      onTabReorder(dragState.draggedFromIndex, index);
    }
    
    setDragState({
      isDragging: false,
      draggedTabId: null,
      draggedFromIndex: null,
      dragOverIndex: null
    });
  }, [dragState, onTabReorder]);

  const handleDragEnd = useCallback(() => {
    setDragState({
      isDragging: false,
      draggedTabId: null,
      draggedFromIndex: null,
      dragOverIndex: null
    });
  }, []);

  // Scroll handlers
  const handleScrollLeft = useCallback(() => {
    if (scrollContainerRef.current) {
      scrollContainerRef.current.scrollBy({ left: -200, behavior: 'smooth' });
    }
  }, []);

  const handleScrollRight = useCallback(() => {
    if (scrollContainerRef.current) {
      scrollContainerRef.current.scrollBy({ left: 200, behavior: 'smooth' });
    }
  }, []);

  // Close context menu on outside click
  useEffect(() => {
    const handleClickOutside = () => {
      if (contextMenu.isOpen) {
        closeContextMenu();
      }
    };

    document.addEventListener('click', handleClickOutside);
    return () => document.removeEventListener('click', handleClickOutside);
  }, [contextMenu.isOpen, closeContextMenu]);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.metaKey || e.ctrlKey) {
        switch (e.key) {
          case 'w':
            e.preventDefault();
            const activeTab = tabs.find(t => t.isActive);
            if (activeTab && !activeTab.isPinned) {
              onTabClose(activeTab.id);
            }
            break;
          case 't':
            e.preventDefault();
            // TODO: Implement new tab functionality
            break;
          case '1':
          case '2':
          case '3':
          case '4':
          case '5':
            e.preventDefault();
            const tabIndex = parseInt(e.key) - 1;
            if (visibleTabs[tabIndex]) {
              onTabSelect(visibleTabs[tabIndex].id);
            }
            break;
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [tabs, visibleTabs, onTabClose, onTabSelect]);

  // Render individual tab
  const renderTab = useCallback((tab: TabData, index: number, isOverflow = false) => {
    const isBeingDragged = dragState.draggedTabId === tab.id;
    const isDraggedOver = dragState.dragOverIndex === index;
    
    return (
      <div
        key={tab.id}
        className={`
          relative flex items-center space-x-2 px-3 py-2 min-w-0 cursor-pointer transition-all duration-150
          ${tab.isActive 
            ? 'bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 border-b-2 border-blue-500' 
            : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600'
          }
          ${isBeingDragged ? 'opacity-50' : ''}
          ${isDraggedOver ? 'bg-blue-100 dark:bg-blue-900/20' : ''}
          ${isOverflow ? 'w-full justify-between' : ''}
        `}
        onClick={() => handleTabClick(tab.id)}
        onMouseDown={(e) => handleTabMiddleClick(e, tab.id)}
        onContextMenu={(e) => handleContextMenu(e, tab.id)}
        onDragStart={(e) => handleDragStart(e, tab.id, index)}
        onDragOver={(e) => handleDragOver(e, index)}
        onDragLeave={handleDragLeave}
        onDrop={(e) => handleDrop(e, index)}
        onDragEnd={handleDragEnd}
        draggable
        role="tab"
        aria-selected={tab.isActive}
        aria-label={`Essay tab: ${tab.title}`}
      >
        {/* Tab Content */}
        <div className="flex items-center space-x-2 min-w-0 flex-1">
          {/* Pinned indicator */}
          {tab.isPinned && (
            <Pin className="w-3 h-3 text-gray-400 flex-shrink-0" />
          )}
          
          {/* Unsaved changes indicator */}
          {tab.hasUnsavedChanges && (
            <Circle className="w-2 h-2 fill-orange-500 text-orange-500 flex-shrink-0" />
          )}
          
          {/* Tab title */}
          <span className="text-sm font-medium truncate">
            {tab.title}
          </span>
        </div>

        {/* Close button */}
        {(!tab.isPinned || tab.isActive) && (
          <button
            onClick={(e) => handleTabClose(e, tab.id)}
            className="flex items-center justify-center w-5 h-5 rounded hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors flex-shrink-0"
            aria-label="Close tab"
          >
            <X className="w-3 h-3" />
          </button>
        )}
      </div>
    );
  }, [
    dragState, 
    handleTabClick, 
    handleTabMiddleClick, 
    handleContextMenu, 
    handleDragStart, 
    handleDragOver, 
    handleDragLeave, 
    handleDrop, 
    handleDragEnd, 
    handleTabClose
  ]);

  if (tabs.length === 0) {
    return null;
  }

  return (
    <div className={`flex items-center bg-gray-50 dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700 ${className}`}>
      <div className="flex-1 flex items-center overflow-hidden" ref={tabsContainerRef}>
        {/* Scroll Left Button */}
        {scrollPosition > 0 && (
          <button
            onClick={handleScrollLeft}
            className="flex items-center justify-center w-8 h-8 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-l transition-colors"
            aria-label="Scroll tabs left"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
        )}

        {/* Tabs Container */}
        <div 
          ref={scrollContainerRef}
          className="flex-1 flex overflow-x-auto scrollbar-hide"
          style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}
        >
          <div className="flex">
            {visibleTabs.map((tab, index) => renderTab(tab, index))}
          </div>
        </div>

        {/* Scroll Right Button */}
        {overflowTabs.length > 0 && (
          <button
            onClick={handleScrollRight}
            className="flex items-center justify-center w-8 h-8 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-r transition-colors"
            aria-label="Scroll tabs right"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Overflow Menu */}
      {overflowTabs.length > 0 && (
        <div className="relative">
          <button
            onClick={() => setShowOverflow(!showOverflow)}
            className="flex items-center space-x-1 px-3 py-2 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
            aria-label="More tabs"
          >
            <span>More</span>
            <ChevronDown className="w-4 h-4" />
          </button>
          
          {showOverflow && (
            <div className="absolute right-0 top-full mt-1 w-64 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg py-2 z-50">
              <div className="max-h-64 overflow-y-auto">
                {overflowTabs.map((tab, index) => (
                  <div
                    key={tab.id}
                    className="px-3 py-2 hover:bg-gray-100 dark:hover:bg-gray-700 cursor-pointer"
                    onClick={() => {
                      handleTabClick(tab.id);
                      setShowOverflow(false);
                    }}
                  >
                    {renderTab(tab, visibleTabs.length + index, true)}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Context Menu */}
      {contextMenu.isOpen && contextMenu.tabId && (
        <div
          className="fixed z-50 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg py-2 min-w-[180px] animate-in fade-in duration-100"
          style={{
            left: Math.min(contextMenu.position.x, window.innerWidth - 200),
            top: Math.min(contextMenu.position.y, window.innerHeight - 250)
          }}
        >
          {(() => {
            const tab = tabs.find(t => t.id === contextMenu.tabId);
            if (!tab) return null;

            return (
              <>
                <button
                  onClick={() => handleContextMenuAction('open-new-window')}
                  className="w-full px-3 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center space-x-2"
                >
                  <ExternalLink className="w-4 h-4" />
                  <span>Open in New Window</span>
                </button>
                
                <button
                  onClick={() => handleContextMenuAction(tab.isPinned ? 'unpin' : 'pin')}
                  className="w-full px-3 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center space-x-2"
                >
                  <Pin className="w-4 h-4" />
                  <span>{tab.isPinned ? 'Unpin Tab' : 'Pin Tab'}</span>
                </button>
                
                <button
                  onClick={() => handleContextMenuAction('duplicate')}
                  className="w-full px-3 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center space-x-2"
                >
                  <Copy className="w-4 h-4" />
                  <span>Duplicate Essay</span>
                </button>
                
                <div className="border-t border-gray-200 dark:border-gray-700 my-1" />
                
                <button
                  onClick={() => handleContextMenuAction('close')}
                  className={`w-full px-3 py-2 text-left text-sm flex items-center space-x-2 ${
                    tab.isPinned 
                      ? 'text-gray-400 dark:text-gray-600 cursor-not-allowed' 
                      : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                  }`}
                  disabled={tab.isPinned}
                >
                  <X className="w-4 h-4" />
                  <span>Close Tab</span>
                </button>
                
                <button
                  onClick={() => handleContextMenuAction('close-others')}
                  className="w-full px-3 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center space-x-2"
                >
                  <X className="w-4 h-4" />
                  <span>Close Other Tabs</span>
                </button>
              </>
            );
          })()}
        </div>
      )}
    </div>
  );
};

export default RecentEssayTabs; 