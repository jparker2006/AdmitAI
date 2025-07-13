'use client';

import { Sparkles, Wand2, Scissors, Plus, MessageSquare, Lightbulb } from 'lucide-react';

export default function AIControls() {
  return (
    <div className="space-y-3">
      {/* Primary AI Actions */}
      <div className="flex items-center space-x-2">
        <button className="flex items-center space-x-2 px-3 py-1.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm">
          <Wand2 className="w-4 h-4" />
          <span>Draft Next Section</span>
        </button>
        <button className="flex items-center space-x-2 px-3 py-1.5 bg-green-600 text-white rounded-lg hover:bg-green-700 text-sm">
          <MessageSquare className="w-4 h-4" />
          <span>Get Feedback</span>
        </button>
        <button className="flex items-center space-x-2 px-3 py-1.5 bg-purple-600 text-white rounded-lg hover:bg-purple-700 text-sm">
          <Sparkles className="w-4 h-4" />
          <span>Save Version</span>
        </button>
      </div>

      {/* Secondary AI Actions */}
      <div className="flex items-center space-x-2">
        <button className="flex items-center space-x-2 px-2 py-1 border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-50 dark:hover:bg-gray-700 text-sm">
          <Wand2 className="w-3 h-3" />
          <span>Improve Style</span>
        </button>
        <button className="flex items-center space-x-2 px-2 py-1 border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-50 dark:hover:bg-gray-700 text-sm">
          <Scissors className="w-3 h-3" />
          <span>Shorten</span>
        </button>
        <button className="flex items-center space-x-2 px-2 py-1 border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-50 dark:hover:bg-gray-700 text-sm">
          <Plus className="w-3 h-3" />
          <span>Elaborate</span>
        </button>
        <button className="flex items-center space-x-2 px-2 py-1 border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-50 dark:hover:bg-gray-700 text-sm">
          <Lightbulb className="w-3 h-3" />
          <span>Clarify</span>
        </button>
      </div>

      {/* AI Status */}
      <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
        <div className="flex items-center space-x-2">
          <div className="w-2 h-2 bg-green-500 rounded-full"></div>
          <span>AI Ready</span>
        </div>
        <span>Select text to enable AI improvements</span>
      </div>
    </div>
  );
} 