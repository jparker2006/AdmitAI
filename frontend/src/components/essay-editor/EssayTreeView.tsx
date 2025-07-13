'use client';

import { useState, useRef, useCallback, useEffect } from 'react';
import { 
  ChevronRight, 
  ChevronDown, 
  University, 
  FileText, 
  Edit3, 
  Search,
  X,
  Plus,
  MoreHorizontal,
  Folder,
  FolderOpen,
  Circle,
  Pin,
  Trash2,
  Copy,
  Edit,
  Download
} from 'lucide-react';
import { 
  School, 
  EssayPrompt, 
  EssayDraft, 
  mockEssayData,
  getTotalEssayCount,
  getSchoolEssayCount,
  getPromptDraftCount
} from '../../lib/mock-essays';

interface TreeViewProps {
  onSelectDraft: (schoolId: string, promptId: string, draftId: string) => void;
  selectedDraftId?: string;
  className?: string;
}

interface ContextMenuState {
  isOpen: boolean;
  position: { x: number; y: number };
  type: 'school' | 'prompt' | 'draft' | null;
  targetId: string | null;
  data?: any;
}

interface TreeNode {
  id: string;
  type: 'school' | 'prompt' | 'draft';
  level: number;
  data: School | EssayPrompt | EssayDraft;
  isExpanded?: boolean;
  parentId?: string;
}

const EssayTreeView: React.FC<TreeViewProps> = ({ 
  onSelectDraft, 
  selectedDraftId,
  className = ''
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [contextMenu, setContextMenu] = useState<ContextMenuState>({
    isOpen: false,
    position: { x: 0, y: 0 },
    type: null,
    targetId: null
  });
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(selectedDraftId || null);
  const [focusedNodeId, setFocusedNodeId] = useState<string | null>(null);
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set());

  const treeRef = useRef<HTMLDivElement>(null);
  const searchRef = useRef<HTMLInputElement>(null);

  // Initialize expanded nodes from mock data
  useEffect(() => {
    const initialExpanded = new Set<string>();
    mockEssayData.schools.forEach(school => {
      if (school.isExpanded) {
        initialExpanded.add(school.id);
      }
      school.prompts.forEach(prompt => {
        if (prompt.isExpanded) {
          initialExpanded.add(prompt.id);
        }
      });
    });
    setExpandedNodes(initialExpanded);
  }, []);

  // Filter data based on search query
  const filteredData = useCallback(() => {
    if (!searchQuery.trim()) {
      return mockEssayData.schools;
    }

    const query = searchQuery.toLowerCase();
    return mockEssayData.schools.filter(school => {
      const schoolMatches = school.name.toLowerCase().includes(query);
      const promptMatches = school.prompts.some(prompt => 
        prompt.title.toLowerCase().includes(query) ||
        prompt.drafts.some(draft => draft.name.toLowerCase().includes(query))
      );
      return schoolMatches || promptMatches;
    }).map(school => ({
      ...school,
      prompts: school.prompts.filter(prompt => {
        const promptMatches = prompt.title.toLowerCase().includes(query);
        const draftMatches = prompt.drafts.some(draft => 
          draft.name.toLowerCase().includes(query)
        );
        return promptMatches || draftMatches;
      })
    }));
  }, [searchQuery]);

  // Toggle node expansion
  const toggleNode = useCallback((nodeId: string) => {
    setExpandedNodes(prev => {
      const newSet = new Set(prev);
      if (newSet.has(nodeId)) {
        newSet.delete(nodeId);
      } else {
        newSet.add(nodeId);
      }
      return newSet;
    });
  }, []);

  // Handle node selection
  const handleNodeSelect = useCallback((nodeId: string, nodeType: 'school' | 'prompt' | 'draft', data: any) => {
    setSelectedNodeId(nodeId);
    setFocusedNodeId(nodeId);
    
    if (nodeType === 'draft') {
      // Find the school and prompt for this draft
      for (const school of mockEssayData.schools) {
        for (const prompt of school.prompts) {
          if (prompt.drafts.some(draft => draft.id === nodeId)) {
            onSelectDraft(school.id, prompt.id, nodeId);
            return;
          }
        }
      }
    } else if (nodeType === 'prompt' || nodeType === 'school') {
      // Toggle expansion for non-draft nodes
      toggleNode(nodeId);
    }
  }, [onSelectDraft, toggleNode]);

  // Handle context menu
  const handleContextMenu = useCallback((e: React.MouseEvent, nodeType: 'school' | 'prompt' | 'draft', nodeId: string, data: any) => {
    e.preventDefault();
    e.stopPropagation();
    
    setContextMenu({
      isOpen: true,
      position: { x: e.clientX, y: e.clientY },
      type: nodeType,
      targetId: nodeId,
      data
    });
  }, []);

  // Close context menu
  const closeContextMenu = useCallback(() => {
    setContextMenu(prev => ({ ...prev, isOpen: false }));
  }, []);

  // Handle context menu actions
  const handleContextMenuAction = useCallback((action: string) => {
    console.log(`Context menu action: ${action} for ${contextMenu.type} ${contextMenu.targetId}`);
    // TODO: Implement actual actions
    closeContextMenu();
  }, [contextMenu, closeContextMenu]);

  // Clear search
  const clearSearch = useCallback(() => {
    setSearchQuery('');
  }, []);

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!treeRef.current?.contains(document.activeElement)) return;

      switch (e.key) {
        case 'ArrowDown':
          e.preventDefault();
          // TODO: Implement down navigation
          break;
        case 'ArrowUp':
          e.preventDefault();
          // TODO: Implement up navigation
          break;
        case 'ArrowRight':
          e.preventDefault();
          if (focusedNodeId) {
            setExpandedNodes(prev => new Set([...prev, focusedNodeId]));
          }
          break;
        case 'ArrowLeft':
          e.preventDefault();
          if (focusedNodeId) {
            setExpandedNodes(prev => {
              const newSet = new Set(prev);
              newSet.delete(focusedNodeId);
              return newSet;
            });
          }
          break;
        case 'Enter':
          e.preventDefault();
          if (focusedNodeId) {
            // TODO: Open/select focused node
          }
          break;
        case 'Escape':
          closeContextMenu();
          break;
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [focusedNodeId, closeContextMenu]);

  // Close context menu on outside click
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (contextMenu.isOpen) {
        closeContextMenu();
      }
    };

    document.addEventListener('click', handleClickOutside);
    return () => document.removeEventListener('click', handleClickOutside);
  }, [contextMenu.isOpen, closeContextMenu]);

  // Render tree node
  const renderTreeNode = (
    node: School | EssayPrompt | EssayDraft, 
    type: 'school' | 'prompt' | 'draft', 
    level: number,
    parentId?: string
  ) => {
    const nodeId = node.id;
    const isExpanded = expandedNodes.has(nodeId);
    const isSelected = selectedNodeId === nodeId;
    const isFocused = focusedNodeId === nodeId;
    
    let icon;
    let label;
    let count = 0;
    let statusIndicator = null;

    switch (type) {
      case 'school':
        const school = node as School;
        icon = isExpanded ? <FolderOpen className="w-4 h-4" /> : <Folder className="w-4 h-4" />;
        label = school.name;
        count = getSchoolEssayCount(school.id);
        break;
      case 'prompt':
        const prompt = node as EssayPrompt;
        icon = <FileText className="w-4 h-4" />;
        label = prompt.title;
        count = getPromptDraftCount(prompt.id);
        break;
      case 'draft':
        const draft = node as EssayDraft;
        icon = <Edit3 className="w-4 h-4" />;
        label = draft.name;
        
        // Status indicator
        if (draft.status === 'current') {
          statusIndicator = <span className="text-xs text-blue-600 dark:text-blue-400">(Current)</span>;
        } else if (draft.status === 'unsaved') {
          statusIndicator = <Circle className="w-2 h-2 fill-orange-500 text-orange-500" />;
        } else {
          const timeDiff = Date.now() - draft.lastModified.getTime();
          const minutes = Math.floor(timeDiff / 60000);
          const timeText = minutes < 1 ? 'Just now' : minutes < 60 ? `${minutes}m ago` : 'Saved';
          statusIndicator = <span className="text-xs text-gray-500 dark:text-gray-400">({timeText})</span>;
        }
        break;
    }

    return (
      <div key={nodeId} className="select-none">
        <div
          className={`flex items-center space-x-2 px-2 py-1.5 rounded-md cursor-pointer transition-colors ${
            isSelected 
              ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-900 dark:text-blue-100' 
              : 'hover:bg-gray-100 dark:hover:bg-gray-700'
          } ${isFocused ? 'ring-2 ring-blue-500 ring-opacity-50' : ''}`}
          style={{ paddingLeft: `${level * 20 + 8}px` }}
          onClick={(e) => {
            e.stopPropagation();
            handleNodeSelect(nodeId, type, node);
          }}
          onContextMenu={(e) => handleContextMenu(e, type, nodeId, node)}
          tabIndex={0}
          role="treeitem"
          aria-expanded={type !== 'draft' ? isExpanded : undefined}
          aria-selected={isSelected}
          aria-level={level}
        >
          {/* Expand/Collapse Icon */}
          {type !== 'draft' && (
            <button
              className="flex items-center justify-center w-4 h-4 hover:bg-gray-200 dark:hover:bg-gray-600 rounded"
              onClick={(e) => {
                e.stopPropagation();
                toggleNode(nodeId);
              }}
              aria-label={isExpanded ? 'Collapse' : 'Expand'}
            >
              {isExpanded ? 
                <ChevronDown className="w-3 h-3" /> : 
                <ChevronRight className="w-3 h-3" />
              }
            </button>
          )}

          {/* Node Icon */}
          <div className="flex items-center justify-center w-4 h-4 text-gray-500 dark:text-gray-400">
            {icon}
          </div>

          {/* Node Label */}
          <span className="flex-1 text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
            {label}
          </span>

          {/* Count Badge */}
          {count > 0 && (
            <span className="px-2 py-0.5 text-xs bg-gray-200 dark:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-full">
              {count}
            </span>
          )}

          {/* Status Indicator */}
          {statusIndicator}
        </div>

        {/* Render children */}
        {isExpanded && type === 'school' && (
          <div>
            {(node as School).prompts.map(prompt => (
              <div key={prompt.id}>
                {renderTreeNode(prompt, 'prompt', level + 1, nodeId)}
                {expandedNodes.has(prompt.id) && prompt.drafts.map(draft => 
                  renderTreeNode(draft, 'draft', level + 2, prompt.id)
                )}
              </div>
            ))}
          </div>
        )}

        {isExpanded && type === 'prompt' && (
          <div>
            {(node as EssayPrompt).drafts.map(draft => 
              renderTreeNode(draft, 'draft', level + 1, nodeId)
            )}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className={`flex flex-col h-full ${className}`} ref={treeRef}>
      {/* Search Header */}
      <div className="p-3 border-b border-gray-200 dark:border-gray-700">
        <div className="relative mb-3">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            ref={searchRef}
            type="text"
            placeholder="Filter by school or prompt..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-8 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
          {searchQuery && (
            <button
              onClick={clearSearch}
              className="absolute right-2 top-1/2 transform -translate-y-1/2 p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
            >
              <X className="w-3 h-3 text-gray-400" />
            </button>
          )}
        </div>
        
        <button className="w-full flex items-center justify-center space-x-2 px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
          <Plus className="w-4 h-4" />
          <span className="text-sm font-medium">New Essay</span>
        </button>
      </div>

      {/* Tree Content */}
      <div className="flex-1 overflow-y-auto p-2" role="tree">
        <div className="space-y-1">
          {/* Root Node */}
          <div className="flex items-center space-x-2 px-2 py-1.5 text-sm font-semibold text-gray-900 dark:text-gray-100 border-b border-gray-200 dark:border-gray-700 mb-2">
            <Folder className="w-4 h-4" />
            <span>My Essays</span>
            <span className="px-2 py-0.5 text-xs bg-gray-200 dark:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-full">
              {getTotalEssayCount()}
            </span>
          </div>

          {/* School Nodes */}
          {filteredData().map(school => renderTreeNode(school, 'school', 1))}
        </div>
      </div>

      {/* Context Menu */}
      {contextMenu.isOpen && (
        <div
          className="fixed z-50 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg py-2 min-w-[160px] animate-in fade-in duration-100"
          style={{
            left: Math.min(contextMenu.position.x, window.innerWidth - 200),
            top: Math.min(contextMenu.position.y, window.innerHeight - 200)
          }}
        >
          {contextMenu.type === 'school' && (
            <>
              <button
                onClick={() => handleContextMenuAction('add-prompt')}
                className="w-full px-3 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center space-x-2"
              >
                <Plus className="w-4 h-4" />
                <span>Add New Prompt</span>
              </button>
              <button
                onClick={() => handleContextMenuAction('rename')}
                className="w-full px-3 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center space-x-2"
              >
                <Edit className="w-4 h-4" />
                <span>Rename School</span>
              </button>
              <div className="border-t border-gray-200 dark:border-gray-700 my-1" />
              <button
                onClick={() => handleContextMenuAction('delete')}
                className="w-full px-3 py-2 text-left text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 flex items-center space-x-2"
              >
                <Trash2 className="w-4 h-4" />
                <span>Delete School</span>
              </button>
            </>
          )}

          {contextMenu.type === 'prompt' && (
            <>
              <button
                onClick={() => handleContextMenuAction('new-version')}
                className="w-full px-3 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center space-x-2"
              >
                <Plus className="w-4 h-4" />
                <span>New Version</span>
              </button>
              <button
                onClick={() => handleContextMenuAction('duplicate')}
                className="w-full px-3 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center space-x-2"
              >
                <Copy className="w-4 h-4" />
                <span>Duplicate Prompt</span>
              </button>
              <button
                onClick={() => handleContextMenuAction('rename')}
                className="w-full px-3 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center space-x-2"
              >
                <Edit className="w-4 h-4" />
                <span>Rename Prompt</span>
              </button>
              <div className="border-t border-gray-200 dark:border-gray-700 my-1" />
              <button
                onClick={() => handleContextMenuAction('delete')}
                className="w-full px-3 py-2 text-left text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 flex items-center space-x-2"
              >
                <Trash2 className="w-4 h-4" />
                <span>Delete Prompt</span>
              </button>
            </>
          )}

          {contextMenu.type === 'draft' && (
            <>
              <button
                onClick={() => handleContextMenuAction('duplicate')}
                className="w-full px-3 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center space-x-2"
              >
                <Copy className="w-4 h-4" />
                <span>Duplicate Draft</span>
              </button>
              <button
                onClick={() => handleContextMenuAction('rename')}
                className="w-full px-3 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center space-x-2"
              >
                <Edit className="w-4 h-4" />
                <span>Rename Draft</span>
              </button>
              <button
                onClick={() => handleContextMenuAction('export')}
                className="w-full px-3 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center space-x-2"
              >
                <Download className="w-4 h-4" />
                <span>Export</span>
              </button>
              <div className="border-t border-gray-200 dark:border-gray-700 my-1" />
              <button
                onClick={() => handleContextMenuAction('delete')}
                className="w-full px-3 py-2 text-left text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 flex items-center space-x-2"
              >
                <Trash2 className="w-4 h-4" />
                <span>Delete Draft</span>
              </button>
            </>
          )}
        </div>
      )}
    </div>
  );
};

export default EssayTreeView; 