'use client';

import { useState, useRef, useEffect } from 'react';
import { X, MessageCircle, ArrowUp, ChevronLeft, ChevronRight, ImagePlus, Paperclip } from 'lucide-react';

// Chain of Thought animation styles
const cotAnimationStyles = `
  @keyframes slideIn {
    0% {
      transform: translateY(-5px);
      opacity: 0;
    }
    100% {
      transform: translateY(0);
      opacity: 1;
    }
  }
  
  @keyframes subtlePulse {
    0%, 100% { 
      opacity: 1;
    }
    50% { 
      opacity: 0.7;
    }
  }
  
  @keyframes dotBounce {
    0%, 80%, 100% { 
      transform: scale(1);
      opacity: 0.6;
    }
    40% { 
      transform: scale(1.1);
      opacity: 1;
    }
  }
  
  .cot-step-appear {
    animation: slideIn 0.3s ease-out forwards;
  }
  
  .cot-step-active {
    animation: subtlePulse 1.5s ease-in-out infinite;
  }
  
  .cot-dot-bounce {
    animation: dotBounce 0.6s ease-in-out infinite;
  }
`;

interface ChatSidebarProps {
  isCollapsed: boolean;
  onToggleCollapse: () => void;
  width: number;
}

export default function ChatSidebar({ isCollapsed, onToggleCollapse, width }: ChatSidebarProps) {
  const [message, setMessage] = useState('');
  const [messages, setMessages] = useState<Array<{ id: string; text: string; isUser: boolean; timestamp: Date; fromCOT?: boolean }>>([
    { id: '1', text: 'Hello! How can I help you today?', isUser: false, timestamp: new Date() }
  ]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  
  // Chain of Thought state
  const [isThinking, setIsThinking] = useState(false);
  const [thoughtStep, setThoughtStep] = useState(0);
  const [visibleSteps, setVisibleSteps] = useState(0);
  const [isTyping, setIsTyping] = useState(false);
  const [typedText, setTypedText] = useState('');
  const [cotCompleted, setCotCompleted] = useState(false);
  const [expandedCotMessages, setExpandedCotMessages] = useState<Set<number>>(new Set());
  const [allCompletedSteps, setAllCompletedSteps] = useState<Array<{text: string; detail: string; thinking: string}>>([]);
  const [currentThinkingText, setCurrentThinkingText] = useState('');
  const [thinkingStepIndex, setThinkingStepIndex] = useState(-1);
  
  // Chain of Thought steps with thinking
  const thoughtSteps = [
    { 
      text: "Analyzing academic profile\nProcessing GPA, SAT scores, and course load", 
      thinking: "3.8 GPA + 1450 SAT puts you in the competitive range for top universities. AP courses and leadership show strong academic rigor. This is a solid profile for selective institutions.",
      detail: "Processing GPA, test scores, and course rigor from your profile",
      duration: 1200 
    },
    { 
      text: "Accessing college databases\nQuerying admission statistics and enrollment data", 
      thinking: "UCSD: 32% acceptance, median SAT 1420. UW: 56% acceptance, stronger research output. Students with your profile historically perform well at research-focused schools.",
      detail: "Querying Common Data Set and IPEDS for admission statistics",
      duration: 1400 
    },
    { 
      text: "Cross-referencing program rankings\nAnalyzing Computer Science department quality", 
      thinking: "CS rankings: UCSD #6 (AI/ML research), UW #8 (tech industry connections), UT Austin #10 (startup ecosystem). All offer excellent undergraduate research opportunities.",
      detail: "Checking US News, Princeton Review, and Niche for program quality",
      duration: 1300 
    },
    { 
      text: "Calculating financial fit\nRunning net price calculators for $85k income", 
      thinking: "At $85k income: UCSD ~$35k/year (in-state), UW ~$45k (out-of-state + merit aid potential), UT Austin ~$52k (strong scholarship opportunities).",
      detail: "Analyzing net price calculators and financial aid data",
      duration: 1200 
    },
    { 
      text: "Matching campus culture preferences\nAnalyzing student reviews and environment data", 
      thinking: "Tech startup alignment: San Diego (biotech), Seattle (Amazon/Microsoft), Austin (startup culture). UCSD = research-focused, UW = academics + outdoors, UT = school spirit.",
      detail: "Comparing your interests with student reviews and campus data",
      duration: 1100 
    },
    { 
      text: "Generating recommendations\nCalculating fit scores and match probabilities", 
      thinking: "Top choice: UCSD (78% fit) - excellent CS, reasonable cost, research. UW (74% fit) - industry connections. UT Austin (71% fit) - value + culture. All are matches, not reaches.",
      detail: "Ranking colleges by fit score and admission probability",
      duration: 1000 
    }
  ];

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = textareaRef.current.scrollHeight + 'px';
    }
  }, [message]);

  // Chain of Thought functions
  const toggleCotExpansion = (messageIndex: number) => {
    setExpandedCotMessages(prev => {
      const newSet = new Set(prev);
      if (newSet.has(messageIndex)) {
        newSet.delete(messageIndex);
      } else {
        newSet.add(messageIndex);
      }
      return newSet;
    });
  };

  const startChainOfThought = () => {
    setIsThinking(true);
    setThoughtStep(0);
    setVisibleSteps(0);
    setCotCompleted(false);
    setAllCompletedSteps([]);
    setCurrentThinkingText('');
    setThinkingStepIndex(-1);
    
    // Create sequential items: [toolCall1, thinking1, toolCall2, thinking2, ...]
    const sequentialItems: Array<{type: 'tool' | 'thinking', stepIndex: number, duration: number}> = [];
    thoughtSteps.forEach((step, index) => {
      sequentialItems.push({type: 'tool', stepIndex: index, duration: step.duration * 0.6});
      sequentialItems.push({type: 'thinking', stepIndex: index, duration: step.duration * 0.4});
    });
    
    const runSequentialItem = (itemIndex: number) => {
      if (itemIndex >= sequentialItems.length) {
        setTimeout(() => {
          setIsThinking(false);
          setAllCompletedSteps(thoughtSteps);
          setCotCompleted(true);
          
          setTimeout(() => {
            startTypingResponse();
          }, 500);
        }, 400);
        return;
      }
      
      const item = sequentialItems[itemIndex];
      setVisibleSteps(itemIndex + 1);
      
      if (item.type === 'tool') {
        setThoughtStep(item.stepIndex);
        setThinkingStepIndex(-1);
        setCurrentThinkingText('');
        setTimeout(() => {
          runSequentialItem(itemIndex + 1);
        }, item.duration);
      } else if (item.type === 'thinking') {
        setThinkingStepIndex(item.stepIndex);
        typeThinkingText(thoughtSteps[item.stepIndex].thinking, () => {
          runSequentialItem(itemIndex + 1);
        });
      }
    };
    
    runSequentialItem(0);
  };

  const typeThinkingText = (text: string, onComplete: () => void) => {
    setCurrentThinkingText('');
    let currentIndex = 0;
    
    const typingInterval = setInterval(() => {
      if (currentIndex < text.length) {
        setCurrentThinkingText(text.substring(0, currentIndex + 1));
        currentIndex++;
      } else {
        clearInterval(typingInterval);
        setTimeout(onComplete, 300); // Small pause before next item
      }
    }, 15); // Fast typing speed
  };

  const startTypingResponse = () => {
    setIsTyping(true);
    setTypedText('');
    
    const fullResponse = "Based on my analysis of your academic profile and comprehensive database search, I've identified several colleges that would be excellent fits for you. After cross-referencing admission statistics from the Common Data Set, program rankings from US News and Princeton Review, and financial aid data, here are my personalized recommendations:\n\n**Top Matches:**\n• **University of California, San Diego** - 78% fit score, strong in your intended major\n• **University of Washington** - 74% fit score, excellent research opportunities\n• **University of Texas at Austin** - 71% fit score, great value for out-of-state students\n\nThese recommendations consider your GPA, test scores, financial needs, and campus culture preferences. Would you like me to dive deeper into any specific aspects like admission requirements, financial aid, or campus life?";
    
    let currentIndex = 0;
    const typingInterval = setInterval(() => {
      if (currentIndex < fullResponse.length) {
        setTypedText(fullResponse.substring(0, currentIndex + 1));
        currentIndex++;
      } else {
        clearInterval(typingInterval);
        setTimeout(() => {
          setIsTyping(false);
          setMessages(prev => [...prev, { 
            id: Date.now().toString(), 
            text: fullResponse, 
            isUser: false, 
            timestamp: new Date(),
            fromCOT: true 
          }]);
          setTypedText('');
          setCotCompleted(false);
          setExpandedCotMessages(prev => {
            const newSet = new Set(prev);
            newSet.delete(-1);
            return newSet;
          });
        }, 800);
      }
    }, 25);
  };

  const handleSendMessage = () => {
    if (!message.trim() || isCollapsed) return;
    
    const newMessage = {
      id: Date.now().toString(),
      text: message,
      isUser: true,
      timestamp: new Date()
    };
    
    setMessages(prev => [...prev, newMessage]);
    const currentMessage = message.toLowerCase();
    setMessage('');
    
    // Check if user typed "cot" to trigger chain of thought
    if (currentMessage === 'cot') {
      startChainOfThought();
    } else {
      // Simulate normal AI response
      setTimeout(() => {
        const aiResponse = {
          id: (Date.now() + 1).toString(),
          text: 'I understand. Let me help you with that.',
          isUser: false,
          timestamp: new Date()
        };
        setMessages(prev => [...prev, aiResponse]);
      }, 1000);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleImageUpload = () => {
    // Placeholder for image upload functionality
    console.log('Image upload clicked');
  };

  // Simple markdown formatter for AI responses
  const formatMarkdown = (text: string) => {
    const lines = text.split('\n');
    const result: React.ReactElement[] = [];
    
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      
      // Handle bold text
      const parts = line.split(/(\*\*.*?\*\*)/g);
      const formattedParts = parts.map((part, partIndex) => {
        if (part.startsWith('**') && part.endsWith('**')) {
          return (
            <strong key={partIndex} className="font-semibold">
              {part.slice(2, -2)}
            </strong>
          );
        }
        return part;
      });

      // Handle bullet points
      if (line.trim().startsWith('•') || line.trim().startsWith('-')) {
        result.push(
          <div key={i} className="flex items-start space-x-2 ml-2 my-1">
            <span className="text-blue-500 mt-0.5 text-xs">•</span>
            <span className="flex-1">{formattedParts}</span>
          </div>
        );
      }
      // Handle section headers (lines that end with colon)
      else if (line.trim().endsWith(':') && line.trim().length > 1) {
        result.push(
          <div key={i} className="font-medium text-gray-800 dark:text-gray-100 mt-3 mb-1">
            {formattedParts}
          </div>
        );
      }
      // Handle empty lines (paragraph breaks)
      else if (line.trim() === '') {
        result.push(<div key={i} className="h-2"></div>);
      }
      // Regular lines
      else if (line.trim().length > 0) {
        result.push(
          <div key={i} className="mb-1">
            {formattedParts}
          </div>
        );
      }
    }
    
    return result;
  };

  if (isCollapsed) {
    return (
      <button
        onClick={onToggleCollapse}
        className="h-full w-full bg-white/95 dark:bg-gray-900/95 backdrop-blur-sm border-l border-gray-200/50 dark:border-gray-700/50 flex flex-col items-center justify-start pt-6 hover:bg-gray-100/50 dark:hover:bg-gray-700/50 transition-all duration-200"
        title="Expand chat"
      >
        <ChevronLeft className="w-4 h-4 text-gray-400 dark:text-gray-500 mb-4" />
        <div className="flex-1 flex items-center justify-center">
          <MessageCircle className="w-5 h-5 text-gray-300 dark:text-gray-600" />
        </div>
      </button>
    );
  }

  return (
    <div className="h-full bg-white/95 dark:bg-gray-900/95 backdrop-blur-sm border-l border-gray-200/50 dark:border-gray-700/50 flex flex-col">
      <style dangerouslySetInnerHTML={{__html: cotAnimationStyles}} />
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200/30 dark:border-gray-700/30 flex-shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
          <h2 className="text-sm font-medium text-gray-600 dark:text-gray-300">AI Assistant</h2>
        </div>
        <button
          onClick={onToggleCollapse}
          className="p-1.5 hover:bg-gray-100/50 dark:hover:bg-gray-700/50 rounded-md transition-all duration-200"
          title="Collapse chat"
        >
          <ChevronRight className="w-4 h-4 text-gray-400 dark:text-gray-500" />
        </button>
      </div>
      
      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4 scrollbar-thin scrollbar-thumb-gray-300 dark:scrollbar-thumb-gray-600 scrollbar-track-transparent">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className="w-full"
          >
            {msg.isUser ? (
              <div className="w-full group">
                <div className="bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg px-4 py-3 mb-2">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                      <span className="text-xs font-medium text-gray-500 dark:text-gray-400">You</span>
                    </div>
                    <span className="text-xs text-gray-400 dark:text-gray-500 opacity-0 group-hover:opacity-100 transition-opacity">
                      {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>
                  <p className="text-sm text-gray-700 dark:text-gray-200 leading-relaxed font-normal">{msg.text}</p>
                </div>
              </div>
            ) : (
              <div className="w-full group">
                {/* Show completed COT summary before the bot response */}
                {msg.fromCOT && (
                  <div className="mb-3">
                    <div className="bg-green-50/50 dark:bg-green-900/20 border border-green-200/30 dark:border-green-700/30 rounded-lg p-2">
                      <button
                        onClick={() => toggleCotExpansion(parseInt(msg.id))}
                        className="flex items-center justify-between w-full text-left hover:bg-green-500/5 dark:hover:bg-green-500/10 rounded p-1 transition-all duration-200"
                      >
                        <div className="flex items-center space-x-2">
                          <div className="w-2 h-2 rounded-full bg-green-500"></div>
                          <span className="text-green-700 dark:text-green-300 font-medium text-xs">Completed ({allCompletedSteps.length} steps)</span>
                        </div>
                        <div className={`text-green-600 dark:text-green-400 transition-transform duration-200 ${expandedCotMessages.has(parseInt(msg.id)) ? 'rotate-180' : ''}`}>
                          <ChevronRight className="w-3 h-3" />
                        </div>
                      </button>
                      
                      {expandedCotMessages.has(parseInt(msg.id)) && (
                        <div className="mt-2 space-y-2">
                          {allCompletedSteps.map((step, index) => (
                            <div 
                              key={`summary-${index}`}
                              className="space-y-2"
                            >
                              <div className="flex items-center space-x-2 p-1.5 rounded bg-green-500/5 dark:bg-green-500/10">
                                <div className="w-1 h-1 rounded-full bg-green-500"></div>
                                <div className="flex-1 min-w-0">
                                  <div className="text-xs font-medium text-green-700 dark:text-green-300 whitespace-pre-line">
                                    {step.text}
                                  </div>
                                </div>
                              </div>
                              <div className="px-4 py-2">
                                <div className="text-xs leading-relaxed text-gray-600 dark:text-gray-300">
                                  {step.thinking}
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                )}
                
                <div className="mb-2">
                  <div className="text-sm text-gray-700 dark:text-gray-200 leading-relaxed font-normal space-y-1">
                    {formatMarkdown(msg.text)}
                  </div>
                </div>
                <span className="text-xs text-gray-400 dark:text-gray-500 opacity-0 group-hover:opacity-100 transition-opacity">
                  {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>
              </div>
            )}
          </div>
        ))}
        
        {/* Chain of Thought Animation */}
        {isThinking && (
          <div className="w-full mb-4">
            <div className="bg-gray-50/50 dark:bg-gray-800/50 border border-gray-200/30 dark:border-gray-700/30 rounded-lg p-2">
              <div className="flex items-center space-x-2 mb-2">
                <div className="w-3 h-3 border border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                <span className="text-gray-600 dark:text-gray-300 font-medium text-xs">Thinking...</span>
              </div>
              
              <div className="space-y-2">
                {thoughtSteps.map((step, stepIndex) => {
                  const toolCallVisible = visibleSteps > stepIndex * 2;
                  const thinkingVisible = visibleSteps > stepIndex * 2 + 1;
                  const isCurrentStep = stepIndex === thoughtStep;
                  const isCompletedStep = stepIndex < thoughtStep;
                  
                  return (
                    <div key={stepIndex} className="space-y-2">
                      {/* Tool Call Block */}
                      {toolCallVisible && (
                        <div 
                          className={`flex items-start space-x-2 px-2 py-2 rounded transition-all duration-300 cot-step-appear ${
                            isCurrentStep 
                              ? 'bg-blue-500/10 dark:bg-blue-500/20 cot-step-active' 
                              : isCompletedStep 
                                ? 'bg-green-500/5 dark:bg-green-500/10' 
                                : 'opacity-50'
                          }`}
                        >
                          <div className={`w-1.5 h-1.5 rounded-full mt-1 transition-all duration-300 ${
                            isCurrentStep 
                              ? 'bg-blue-500' 
                              : isCompletedStep 
                                ? 'bg-green-500' 
                                : 'bg-gray-400 dark:bg-gray-500'
                          }`}></div>
                          <div className="flex-1 min-w-0">
                            <div className={`font-medium text-xs transition-colors duration-300 whitespace-pre-line ${
                              isCurrentStep 
                                ? 'text-blue-700 dark:text-blue-300' 
                                : isCompletedStep 
                                  ? 'text-green-700 dark:text-green-300' 
                                  : 'text-gray-500 dark:text-gray-400'
                            }`}>
                              {step.text}
                            </div>
                          </div>
                          {isCurrentStep && visibleSteps === stepIndex * 2 + 1 && (
                            <div className="flex space-x-0.5 mt-1">
                              <div className="w-1 h-1 bg-blue-500 rounded-full cot-dot-bounce"></div>
                              <div className="w-1 h-1 bg-blue-500 rounded-full cot-dot-bounce" style={{animationDelay: '0.1s'}}></div>
                              <div className="w-1 h-1 bg-blue-500 rounded-full cot-dot-bounce" style={{animationDelay: '0.2s'}}></div>
                            </div>
                          )}
                        </div>
                      )}
                      
                      {/* Thinking Text */}
                      {thinkingVisible && (
                        <div className={`px-4 py-2 transition-all duration-300 cot-step-appear ${
                          isCompletedStep || visibleSteps > stepIndex * 2 + 2 ? 'opacity-100' : 'opacity-70'
                        }`}>
                          <div className={`text-xs leading-relaxed transition-colors duration-300 ${
                            isCompletedStep || visibleSteps > stepIndex * 2 + 2
                              ? 'text-gray-600 dark:text-gray-300' 
                              : 'text-gray-500 dark:text-gray-400'
                          }`}>
                            {thinkingStepIndex === stepIndex ? (
                              <>
                                {currentThinkingText}
                                {currentThinkingText.length < step.thinking.length && (
                                  <span className="animate-pulse text-blue-500">|</span>
                                )}
                              </>
                            ) : thinkingStepIndex > stepIndex || visibleSteps > stepIndex * 2 + 2 ? (
                              step.thinking
                            ) : (
                              step.thinking
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}
        
        {/* Typing Animation */}
        {isTyping && (
          <div className="w-full mb-4">
            {/* Show completed COT summary above typing when it's a COT response */}
            {cotCompleted && (
              <div className="mb-3">
                <div className="bg-green-50/50 dark:bg-green-900/20 border border-green-200/30 dark:border-green-700/30 rounded-lg p-2">
                  <button
                    onClick={() => toggleCotExpansion(-1)}
                    className="flex items-center justify-between w-full text-left hover:bg-green-500/5 dark:hover:bg-green-500/10 rounded p-1 transition-all duration-200"
                  >
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 rounded-full bg-green-500"></div>
                      <span className="text-green-700 dark:text-green-300 font-medium text-xs">Completed ({allCompletedSteps.length} steps)</span>
                    </div>
                    <div className={`text-green-600 dark:text-green-400 transition-transform duration-200 ${expandedCotMessages.has(-1) ? 'rotate-180' : ''}`}>
                      <ChevronRight className="w-3 h-3" />
                    </div>
                  </button>
                  
                  {expandedCotMessages.has(-1) && (
                    <div className="mt-2 space-y-2">
                      {allCompletedSteps.map((step, index) => (
                        <div 
                          key={`summary-${index}`}
                          className="space-y-2"
                        >
                          <div className="flex items-center space-x-2 p-1.5 rounded bg-green-500/5 dark:bg-green-500/10">
                            <div className="w-1 h-1 rounded-full bg-green-500"></div>
                            <div className="flex-1 min-w-0">
                              <div className="text-xs font-medium text-green-700 dark:text-green-300 whitespace-pre-line">
                                {step.text}
                              </div>
                            </div>
                          </div>
                          <div className="px-4 py-2">
                            <div className="text-xs leading-relaxed text-gray-600 dark:text-gray-300">
                              {step.thinking}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}
            
            <div className="w-full group">
              <div className="mb-1">
                <div className="text-sm text-gray-700 dark:text-gray-200 leading-relaxed font-normal space-y-1">
                  {formatMarkdown(typedText)}
                  <span className="animate-pulse text-blue-500">|</span>
                </div>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>
      
      {/* Input */}
      <div className="px-6 py-4 border-t border-gray-200/30 dark:border-gray-700/30 flex-shrink-0">
        <div className="relative bg-gray-50/50 dark:bg-gray-800/50 rounded-xl border border-gray-200/40 dark:border-gray-600/40 focus-within:border-blue-400/60 focus-within:ring-2 focus-within:ring-blue-400/20 transition-all duration-200">
          <div className="flex items-end gap-3 p-3">
            {/* Image Upload Button */}
            <button
              onClick={handleImageUpload}
              className="flex-shrink-0 p-1.5 text-gray-400 hover:text-gray-600 dark:text-gray-500 dark:hover:text-gray-300 hover:bg-gray-100/50 dark:hover:bg-gray-700/50 rounded-lg transition-all duration-200"
              title="Add image"
            >
              <ImagePlus className="w-4 h-4" />
            </button>
            
            {/* Textarea */}
            <textarea
              ref={textareaRef}
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask me anything..."
              className="flex-1 bg-transparent text-gray-700 dark:text-gray-200 placeholder-gray-400 dark:placeholder-gray-500 resize-none focus:outline-none text-sm leading-6 max-h-32 min-h-[24px]"
              rows={1}
              style={{ height: 'auto' }}
            />
            
            {/* Send Button */}
            <button
              onClick={handleSendMessage}
              className={`flex-shrink-0 p-2 rounded-lg transition-all duration-200 ${
                message.trim() 
                  ? 'bg-blue-600 hover:bg-blue-700 text-white shadow-sm hover:shadow-md transform hover:scale-105' 
                  : 'bg-gray-200/60 dark:bg-gray-600/60 text-gray-400 dark:text-gray-500 cursor-not-allowed'
              }`}
              disabled={!message.trim()}
            >
              <ArrowUp className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
} 