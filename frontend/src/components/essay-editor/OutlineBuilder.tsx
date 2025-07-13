'use client';

import { useState } from 'react';
import { Plus, GripVertical, ChevronRight, ChevronDown, Edit, Trash2, Lock } from 'lucide-react';

export default function OutlineBuilder() {
  const [activeView, setActiveView] = useState<'outline' | 'brainstorm'>('outline');
  const [outlineItems, setOutlineItems] = useState([
    {
      id: '1',
      text: 'Introduction',
      level: 0,
      isExpanded: true,
      isLocked: false,
      children: [
        { id: '1-1', text: 'Hook', level: 1, isExpanded: true, isLocked: false }
      ]
    },
    {
      id: '2',
      text: 'Main Body',
      level: 0,
      isExpanded: true,
      isLocked: false,
      children: [
        { id: '2-1', text: 'First point', level: 1, isExpanded: true, isLocked: false },
        { id: '2-2', text: 'Second point', level: 1, isExpanded: true, isLocked: false }
      ]
    },
    {
      id: '3',
      text: 'Conclusion',
      level: 0,
      isExpanded: true,
      isLocked: false,
      children: []
    }
  ]);

  const renderOutlineItem = (item: any, level = 0) => (
    <div key={item.id} className="space-y-1">
      <div className="flex items-center group hover:bg-gray-50 dark:hover:bg-gray-700 rounded p-2">
        <div className="flex items-center space-x-2 flex-1">
          <GripVertical className="w-4 h-4 text-gray-400 cursor-grab" />
          {item.children && item.children.length > 0 ? (
            <button>
              {item.isExpanded ? (
                <ChevronDown className="w-4 h-4 text-gray-400" />
              ) : (
                <ChevronRight className="w-4 h-4 text-gray-400" />
              )}
            </button>
          ) : (
            <div className="w-4 h-4" />
          )}
          <span className="text-sm text-gray-900 dark:text-white flex-1">
            {item.text}
          </span>
        </div>
        <div className="flex items-center space-x-1 opacity-0 group-hover:opacity-100 transition-opacity">
          {item.isLocked && (
            <Lock className="w-3 h-3 text-yellow-500" />
          )}
          <button className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300">
            <Edit className="w-3 h-3" />
          </button>
          <button className="p-1 text-gray-400 hover:text-red-600 dark:hover:text-red-400">
            <Trash2 className="w-3 h-3" />
          </button>
        </div>
      </div>
      {item.isExpanded && item.children && (
        <div className="ml-6 space-y-1">
          {item.children.map((child: any) => renderOutlineItem(child, level + 1))}
        </div>
      )}
    </div>
  );

  return (
    <div className="space-y-4">
      {/* View Toggle */}
      <div className="flex items-center bg-gray-100 dark:bg-gray-700 rounded-lg p-1">
        <button
          onClick={() => setActiveView('outline')}
          className={`flex-1 px-3 py-1 text-sm rounded-md transition-colors ${
            activeView === 'outline'
              ? 'bg-white dark:bg-gray-600 text-gray-900 dark:text-white shadow-sm'
              : 'text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white'
          }`}
        >
          Outline
        </button>
        <button
          onClick={() => setActiveView('brainstorm')}
          className={`flex-1 px-3 py-1 text-sm rounded-md transition-colors ${
            activeView === 'brainstorm'
              ? 'bg-white dark:bg-gray-600 text-gray-900 dark:text-white shadow-sm'
              : 'text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white'
          }`}
        >
          Brainstorm
        </button>
      </div>

      {/* Outline Content */}
      {activeView === 'outline' && (
        <div className="space-y-2">
          {outlineItems.map((item) => renderOutlineItem(item))}
          
          <button className="flex items-center w-full p-2 text-sm text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 rounded-lg border-2 border-dashed border-gray-300 dark:border-gray-600">
            <Plus className="w-4 h-4 mr-2" />
            Add outline item
          </button>
        </div>
      )}

      {/* Brainstorm Content */}
      {activeView === 'brainstorm' && (
        <div className="space-y-4">
          <div className="p-4 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg">
            <p className="text-sm text-gray-500 dark:text-gray-400 text-center">
              Brainstorm mode - Coming soon
            </p>
          </div>
        </div>
      )}
    </div>
  );
} 