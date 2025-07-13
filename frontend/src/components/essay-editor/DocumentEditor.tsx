'use client';

import { useState } from 'react';
import { Bold, Italic, Underline, AlignLeft, AlignCenter, AlignRight } from 'lucide-react';

export default function DocumentEditor() {
  const [content, setContent] = useState(`Write your essay here...

This is a rich text editor where you can draft your college essay. The AI will help you improve your writing as you go.

Start typing and let the AI assist you in crafting a compelling narrative that showcases your unique voice and experiences.`);

  return (
    <div className="h-full flex flex-col">
      {/* Editor Toolbar */}
      <div className="flex items-center space-x-2 p-2 border-b border-gray-200 dark:border-gray-700">
        <button className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded">
          <Bold className="w-4 h-4 text-gray-600 dark:text-gray-400" />
        </button>
        <button className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded">
          <Italic className="w-4 h-4 text-gray-600 dark:text-gray-400" />
        </button>
        <button className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded">
          <Underline className="w-4 h-4 text-gray-600 dark:text-gray-400" />
        </button>
        <div className="w-px h-6 bg-gray-300 dark:bg-gray-600" />
        <button className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded">
          <AlignLeft className="w-4 h-4 text-gray-600 dark:text-gray-400" />
        </button>
        <button className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded">
          <AlignCenter className="w-4 h-4 text-gray-600 dark:text-gray-400" />
        </button>
        <button className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded">
          <AlignRight className="w-4 h-4 text-gray-600 dark:text-gray-400" />
        </button>
      </div>

      {/* Editor Content */}
      <div className="flex-1 p-4 overflow-y-auto">
        <textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          className="w-full h-full resize-none border-none outline-none bg-transparent text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 leading-relaxed"
          placeholder="Start writing your essay..."
        />
      </div>

      {/* Editor Footer */}
      <div className="flex items-center justify-between p-2 border-t border-gray-200 dark:border-gray-700 text-sm text-gray-500 dark:text-gray-400">
        <div className="flex items-center space-x-4">
          <span>Paragraph 1</span>
          <span>Line 1</span>
        </div>
        <div className="flex items-center space-x-4">
          <span>{content.split(/\s+/).filter(word => word.length > 0).length} words</span>
        </div>
      </div>
    </div>
  );
} 