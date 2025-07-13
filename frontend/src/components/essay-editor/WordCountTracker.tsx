'use client';

import { useState, useEffect } from 'react';
import { Target, AlertTriangle, CheckCircle, Clock } from 'lucide-react';

interface WordCountTrackerProps {
  content?: string;
  maxWords?: number;
  maxCharacters?: number;
  showCharacters?: boolean;
  showProgress?: boolean;
  universityName?: string;
}

export default function WordCountTracker({ 
  content = '', 
  maxWords = 650, 
  maxCharacters = 5000,
  showCharacters = true,
  showProgress = true,
  universityName = 'Stanford'
}: WordCountTrackerProps) {
  const [wordCount, setWordCount] = useState(0);
  const [charCount, setCharCount] = useState(0);
  const [sentences, setSentences] = useState(0);
  const [paragraphs, setParagraphs] = useState(0);
  const [readingTime, setReadingTime] = useState(0);

  // Calculate statistics
  useEffect(() => {
    if (!content) {
      setWordCount(0);
      setCharCount(0);
      setSentences(0);
      setParagraphs(0);
      setReadingTime(0);
      return;
    }

    // Word count
    const words = content.trim().split(/\s+/).filter(word => word.length > 0);
    setWordCount(words.length);

    // Character count (excluding spaces)
    const characters = content.replace(/\s/g, '').length;
    setCharCount(characters);

    // Sentence count
    const sentenceCount = content.split(/[.!?]+/).filter(s => s.trim().length > 0).length;
    setSentences(sentenceCount);

    // Paragraph count
    const paragraphCount = content.split(/\n\s*\n/).filter(p => p.trim().length > 0).length;
    setParagraphs(paragraphCount);

    // Reading time (average 200 words per minute)
    const readingTimeMinutes = Math.ceil(words.length / 200);
    setReadingTime(readingTimeMinutes);
  }, [content]);

  const wordPercentage = (wordCount / maxWords) * 100;
  const charPercentage = (charCount / maxCharacters) * 100;

  const getWordStatusColor = () => {
    if (wordPercentage >= 100) return 'text-red-600 dark:text-red-400';
    if (wordPercentage >= 95) return 'text-orange-600 dark:text-orange-400';
    if (wordPercentage >= 80) return 'text-yellow-600 dark:text-yellow-400';
    return 'text-green-600 dark:text-green-400';
  };

  const getWordProgressColor = () => {
    if (wordPercentage >= 100) return 'bg-red-600';
    if (wordPercentage >= 95) return 'bg-orange-600';
    if (wordPercentage >= 80) return 'bg-yellow-600';
    return 'bg-green-600';
  };

  const getStatusIcon = () => {
    if (wordPercentage >= 100) return <AlertTriangle className="w-4 h-4 text-red-600 dark:text-red-400" />;
    if (wordPercentage >= 95) return <AlertTriangle className="w-4 h-4 text-orange-600 dark:text-orange-400" />;
    if (wordPercentage >= 50) return <CheckCircle className="w-4 h-4 text-green-600 dark:text-green-400" />;
    return <Target className="w-4 h-4 text-gray-500 dark:text-gray-400" />;
  };

  const getRecommendation = () => {
    if (wordPercentage >= 100) return 'Over limit - consider trimming';
    if (wordPercentage >= 95) return 'Nearly at limit - be concise';
    if (wordPercentage >= 80) return 'Good length - keep refining';
    if (wordPercentage >= 50) return 'Solid progress - expand key points';
    if (wordPercentage >= 25) return 'Building foundation - keep writing';
    return 'Just getting started - develop your ideas';
  };

  return (
    <div className="flex items-center space-x-4">
      {/* Status Icon */}
      <div className="flex items-center space-x-2">
        {getStatusIcon()}
        <div className="text-sm">
          <span className={`font-medium ${getWordStatusColor()}`}>
            {wordCount}
          </span>
          <span className="text-gray-500 dark:text-gray-400">
            {' / '}{maxWords}
          </span>
        </div>
      </div>

      {/* Progress Bar */}
      {showProgress && (
        <div className="flex items-center space-x-2">
          <div className="w-24 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
            <div 
              className={`h-full transition-all duration-300 ${getWordProgressColor()}`}
              style={{ width: `${Math.min(wordPercentage, 100)}%` }}
            />
          </div>
          <div className="text-xs text-gray-500 dark:text-gray-400 min-w-[35px]">
            {Math.round(wordPercentage)}%
          </div>
        </div>
      )}

      {/* Character Count */}
      {showCharacters && (
        <div className="text-sm text-gray-500 dark:text-gray-400">
          <span className="font-medium">{charCount.toLocaleString()}</span>
          <span className="text-xs"> chars</span>
        </div>
      )}

      {/* Additional Statistics */}
      <div className="flex items-center space-x-3 text-xs text-gray-500 dark:text-gray-400">
        <div className="flex items-center space-x-1">
          <span>{sentences}</span>
          <span>sentences</span>
        </div>
        <div className="flex items-center space-x-1">
          <span>{paragraphs}</span>
          <span>paragraphs</span>
        </div>
        <div className="flex items-center space-x-1">
          <Clock className="w-3 h-3" />
          <span>{readingTime} min read</span>
        </div>
      </div>

      {/* Recommendation Tooltip */}
      <div className="relative group">
        <div className="text-xs text-gray-400 dark:text-gray-500 cursor-help">
          {universityName} Guidelines
        </div>
        <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 bg-gray-900 dark:bg-gray-100 text-white dark:text-gray-900 text-xs rounded-lg shadow-lg opacity-0 group-hover:opacity-100 transition-opacity duration-200 whitespace-nowrap z-50">
          {getRecommendation()}
          <div className="absolute top-full left-1/2 transform -translate-x-1/2 border-4 border-transparent border-t-gray-900 dark:border-t-gray-100"></div>
        </div>
      </div>
    </div>
  );
} 