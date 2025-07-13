'use client';

import { useState } from 'react';
import { ChevronDown, ChevronUp, Clock, GitBranch, Eye, RotateCcw } from 'lucide-react';

export default function VersionHistory() {
  const [isExpanded, setIsExpanded] = useState(false);
  const [versions] = useState([
    {
      id: '1',
      versionNumber: 3,
      changeType: 'ai_revision',
      changeSummary: 'AI improved style and clarity',
      createdAt: new Date('2024-01-15T10:30:00'),
      wordCount: 247,
      isAutoSave: false
    },
    {
      id: '2',
      versionNumber: 2,
      changeType: 'manual_edit',
      changeSummary: 'Manual edits to introduction',
      createdAt: new Date('2024-01-15T09:45:00'),
      wordCount: 234,
      isAutoSave: true
    },
    {
      id: '3',
      versionNumber: 1,
      changeType: 'draft',
      changeSummary: 'Initial draft',
      createdAt: new Date('2024-01-15T09:00:00'),
      wordCount: 198,
      isAutoSave: false
    }
  ]);

  const getChangeTypeIcon = (type: string) => {
    switch (type) {
      case 'ai_revision':
        return '🤖';
      case 'manual_edit':
        return '✏️';
      case 'draft':
        return '📝';
      default:
        return '📄';
    }
  };

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className="border-t border-gray-200 dark:border-gray-700">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full p-3 flex items-center justify-between text-left hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
      >
        <div className="flex items-center space-x-2">
          <GitBranch className="w-4 h-4 text-gray-500 dark:text-gray-400" />
          <span className="text-sm font-medium text-gray-900 dark:text-white">
            Version History
          </span>
          <span className="text-xs text-gray-500 dark:text-gray-400">
            ({versions.length} versions)
          </span>
        </div>
        {isExpanded ? (
          <ChevronUp className="w-4 h-4 text-gray-500 dark:text-gray-400" />
        ) : (
          <ChevronDown className="w-4 h-4 text-gray-500 dark:text-gray-400" />
        )}
      </button>

      {isExpanded && (
        <div className="border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800">
          <div className="max-h-60 overflow-y-auto">
            {versions.map((version) => (
              <div key={version.id} className="p-3 border-b border-gray-200 dark:border-gray-700 last:border-b-0">
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-3">
                    <div className="text-lg">
                      {getChangeTypeIcon(version.changeType)}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center space-x-2">
                        <span className="text-sm font-medium text-gray-900 dark:text-white">
                          Version {version.versionNumber}
                        </span>
                        {version.isAutoSave && (
                          <span className="text-xs px-2 py-1 bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 rounded">
                            Auto-save
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                        {version.changeSummary}
                      </p>
                      <div className="flex items-center space-x-4 mt-1 text-xs text-gray-500 dark:text-gray-400">
                        <div className="flex items-center space-x-1">
                          <Clock className="w-3 h-3" />
                          <span>{formatTime(version.createdAt)}</span>
                        </div>
                        <span>{version.wordCount} words</span>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-1">
                    <button className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300">
                      <Eye className="w-3 h-3" />
                    </button>
                    <button className="p-1 text-gray-400 hover:text-blue-600 dark:hover:text-blue-400">
                      <RotateCcw className="w-3 h-3" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
} 