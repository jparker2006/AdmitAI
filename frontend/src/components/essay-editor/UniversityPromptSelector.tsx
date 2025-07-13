'use client';

import { useState } from 'react';
import { Search, Plus, Edit, Trash2 } from 'lucide-react';

export default function UniversityPromptSelector() {
  const [selectedUniversity, setSelectedUniversity] = useState('');
  const [prompts, setPrompts] = useState([
    {
      id: '1',
      text: 'Tell us about a personal quality, talent, accomplishment, contribution or experience that is important to you.',
      wordLimit: 650,
      type: 'personal_statement',
      isActive: true
    }
  ]);

  return (
    <div className="space-y-4">
      {/* University Selection */}
      <div className="space-y-2">
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
          University
        </label>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search universities..."
            className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            value={selectedUniversity}
            onChange={(e) => setSelectedUniversity(e.target.value)}
          />
        </div>
      </div>

      {/* Essay Prompts */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
            Essay Prompts
          </label>
          <button className="p-1 text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300">
            <Plus className="w-4 h-4" />
          </button>
        </div>
        
        <div className="space-y-2">
          {prompts.map((prompt) => (
            <div
              key={prompt.id}
              className={`p-3 border rounded-lg cursor-pointer transition-colors ${
                prompt.isActive
                  ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                  : 'border-gray-300 dark:border-gray-600 hover:border-gray-400 dark:hover:border-gray-500'
              }`}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <p className="text-sm text-gray-900 dark:text-white line-clamp-2">
                    {prompt.text}
                  </p>
                  <div className="flex items-center mt-2 text-xs text-gray-500 dark:text-gray-400">
                    <span className="px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded">
                      {prompt.wordLimit} words
                    </span>
                    <span className="ml-2 px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded">
                      {prompt.type.replace('_', ' ')}
                    </span>
                  </div>
                </div>
                <div className="flex items-center space-x-1 ml-2">
                  <button className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300">
                    <Edit className="w-3 h-3" />
                  </button>
                  <button className="p-1 text-gray-400 hover:text-red-600 dark:hover:text-red-400">
                    <Trash2 className="w-3 h-3" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
} 