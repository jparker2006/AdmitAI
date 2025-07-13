'use client';

import { useState } from 'react';
import { BookOpen, Lightbulb, AlertCircle, CheckCircle, ChevronDown, ChevronUp } from 'lucide-react';

export default function WritingTips() {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [activeCategory, setActiveCategory] = useState('structure');
  
  const tips = {
    structure: [
      {
        title: 'Start with a hook',
        description: 'Begin your essay with an engaging opening that captures attention.',
        example: 'Use a question, anecdote, or surprising fact.'
      },
      {
        title: 'Show, don\'t tell',
        description: 'Use specific examples and vivid details instead of generic statements.',
        example: 'Instead of "I am hardworking," describe a specific instance.'
      }
    ],
    style: [
      {
        title: 'Use active voice',
        description: 'Active voice makes your writing more direct and engaging.',
        example: 'Write "I led the team" instead of "The team was led by me".'
      },
      {
        title: 'Vary sentence length',
        description: 'Mix short and long sentences for better flow.',
        example: 'Short sentences create impact. Longer sentences provide detail and context.'
      }
    ],
    content: [
      {
        title: 'Be specific',
        description: 'Avoid vague statements. Use concrete details and examples.',
        example: 'Instead of "many people," write "over 200 volunteers".'
      },
      {
        title: 'Stay focused',
        description: 'Every paragraph should relate to your main theme.',
        example: 'Ask yourself: "Does this support my central message?"'
      }
    ]
  };

  const categories = [
    { id: 'structure', label: 'Structure', icon: BookOpen },
    { id: 'style', label: 'Style', icon: Lightbulb },
    { id: 'content', label: 'Content', icon: CheckCircle }
  ];

  return (
    <div className="space-y-4">
      {/* Category Tabs */}
      <div className="flex space-x-1 bg-gray-100 dark:bg-gray-700 rounded-lg p-1">
        {categories.map((category) => {
          const Icon = category.icon;
          return (
            <button
              key={category.id}
              onClick={() => setActiveCategory(category.id)}
              className={`flex items-center space-x-1 flex-1 px-2 py-1 text-xs rounded-md transition-colors ${
                activeCategory === category.id
                  ? 'bg-white dark:bg-gray-600 text-gray-900 dark:text-white shadow-sm'
                  : 'text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white'
              }`}
            >
              <Icon className="w-3 h-3" />
              <span>{category.label}</span>
            </button>
          );
        })}
      </div>

      {/* Tips Content */}
      <div className="space-y-3">
        {tips[activeCategory as keyof typeof tips].map((tip, index) => (
          <div key={index} className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
            <div className="flex items-start space-x-2">
              <Lightbulb className="w-4 h-4 text-blue-600 dark:text-blue-400 mt-0.5 flex-shrink-0" />
              <div className="flex-1">
                <h4 className="text-sm font-medium text-blue-900 dark:text-blue-100">
                  {tip.title}
                </h4>
                <p className="text-xs text-blue-800 dark:text-blue-200 mt-1">
                  {tip.description}
                </p>
                {tip.example && (
                  <div className="mt-2 p-2 bg-blue-100 dark:bg-blue-900/40 rounded text-xs text-blue-700 dark:text-blue-300">
                    <span className="font-medium">Example: </span>
                    {tip.example}
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Quick Links */}
      <div className="pt-2 border-t border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between text-xs">
          <button className="text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300">
            Common pitfalls →
          </button>
          <button className="text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300">
            Essay examples →
          </button>
        </div>
      </div>
    </div>
  );
} 