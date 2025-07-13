'use client';

import { useState, useRef, useCallback, useEffect } from 'react';
import { GripVertical, ChevronLeft, ChevronRight } from 'lucide-react';

interface PanelResizerProps {
  defaultWidth: number;
  minWidth: number;
  maxWidth: number;
  isCollapsed: boolean;
  onWidthChange: (width: number) => void;
  onCollapseToggle: () => void;
  className?: string;
}

const PanelResizer: React.FC<PanelResizerProps> = ({
  defaultWidth,
  minWidth,
  maxWidth,
  isCollapsed,
  onWidthChange,
  onCollapseToggle,
  className = ''
}) => {
  const [isDragging, setIsDragging] = useState(false);
  const [currentWidth, setCurrentWidth] = useState(defaultWidth);
  const [isHovering, setIsHovering] = useState(false);
  
  const resizerRef = useRef<HTMLDivElement>(null);
  const dragStartRef = useRef<{ x: number; width: number } | null>(null);

  // Handle mouse down to start dragging
  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    if (isCollapsed) return;
    
    e.preventDefault();
    setIsDragging(true);
    
    dragStartRef.current = {
      x: e.clientX,
      width: currentWidth
    };
    
    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';
  }, [isCollapsed, currentWidth]);

  // Handle mouse move during drag
  const handleMouseMove = useCallback((e: MouseEvent) => {
    if (!isDragging || !dragStartRef.current) return;
    
    const deltaX = e.clientX - dragStartRef.current.x;
    const newWidth = Math.min(maxWidth, Math.max(minWidth, dragStartRef.current.width + deltaX));
    
    setCurrentWidth(newWidth);
    onWidthChange(newWidth);
  }, [isDragging, minWidth, maxWidth, onWidthChange]);

  // Handle mouse up to stop dragging
  const handleMouseUp = useCallback(() => {
    if (!isDragging) return;
    
    setIsDragging(false);
    dragStartRef.current = null;
    
    document.body.style.cursor = '';
    document.body.style.userSelect = '';
  }, [isDragging]);

  // Add global event listeners for drag
  useEffect(() => {
    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      
      return () => {
        document.removeEventListener('mousemove', handleMouseMove);
        document.removeEventListener('mouseup', handleMouseUp);
      };
    }
  }, [isDragging, handleMouseMove, handleMouseUp]);

  // Snap to preset widths
  const snapToPresetWidth = useCallback((targetWidth: number) => {
    setCurrentWidth(targetWidth);
    onWidthChange(targetWidth);
  }, [onWidthChange]);

  // Handle double-click to reset to default
  const handleDoubleClick = useCallback(() => {
    if (isCollapsed) {
      onCollapseToggle();
    } else {
      snapToPresetWidth(defaultWidth);
    }
  }, [isCollapsed, onCollapseToggle, snapToPresetWidth, defaultWidth]);

  // Handle keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.metaKey || e.ctrlKey) {
        switch (e.key) {
          case 'b':
            e.preventDefault();
            onCollapseToggle();
            break;
          case '[':
            e.preventDefault();
            if (!isCollapsed) {
              const newWidth = Math.max(minWidth, currentWidth - 40);
              snapToPresetWidth(newWidth);
            }
            break;
          case ']':
            e.preventDefault();
            if (!isCollapsed) {
              const newWidth = Math.min(maxWidth, currentWidth + 40);
              snapToPresetWidth(newWidth);
            }
            break;
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isCollapsed, currentWidth, minWidth, maxWidth, onCollapseToggle, snapToPresetWidth]);

  // Get snap points for visual feedback
  const getSnapPoints = () => {
    const snapPoints = [
      { width: 240, label: 'Compact' },
      { width: defaultWidth, label: 'Default' },
      { width: 320, label: 'Expanded' }
    ];
    
    return snapPoints.filter(point => point.width >= minWidth && point.width <= maxWidth);
  };

  return (
    <div className={`relative flex items-center ${className}`}>
      {/* Collapse Toggle Button */}
      <button
        onClick={onCollapseToggle}
        onDoubleClick={handleDoubleClick}
        className="absolute -right-6 top-1/2 transform -translate-y-1/2 z-10 w-6 h-8 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-r-md hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors flex items-center justify-center"
        title={isCollapsed ? 'Expand panel (Cmd+B)' : 'Collapse panel (Cmd+B)'}
        aria-label={isCollapsed ? 'Expand panel' : 'Collapse panel'}
      >
        {isCollapsed ? (
          <ChevronRight className="w-3 h-3 text-gray-500 dark:text-gray-400" />
        ) : (
          <ChevronLeft className="w-3 h-3 text-gray-500 dark:text-gray-400" />
        )}
      </button>

      {/* Resize Handle */}
      {!isCollapsed && (
        <div
          ref={resizerRef}
          className={`
            absolute -right-1 top-0 bottom-0 w-2 cursor-col-resize group
            hover:bg-blue-500 hover:bg-opacity-20 transition-colors
            ${isDragging ? 'bg-blue-500 bg-opacity-30' : ''}
          `}
          onMouseDown={handleMouseDown}
          onMouseEnter={() => setIsHovering(true)}
          onMouseLeave={() => setIsHovering(false)}
          onDoubleClick={handleDoubleClick}
          role="separator"
          aria-label="Resize panel"
          aria-orientation="vertical"
        >
          {/* Visible grip indicator */}
          <div className={`
            absolute inset-y-0 left-1/2 transform -translate-x-1/2 w-1 transition-all duration-200
            ${isDragging || isHovering ? 'bg-blue-500' : 'bg-gray-300 dark:bg-gray-600'}
          `} />
          
          {/* Grip icon (only show on hover) */}
          {(isHovering || isDragging) && (
            <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded p-1 shadow-sm">
              <GripVertical className="w-3 h-3 text-gray-500 dark:text-gray-400" />
            </div>
          )}
        </div>
      )}

      {/* Snap Points Indicator (only show while dragging) */}
      {isDragging && (
        <div className="absolute -right-20 top-0 bottom-0 w-16 pointer-events-none">
          <div className="relative h-full">
            {getSnapPoints().map((point, index) => {
              const isNearSnap = Math.abs(currentWidth - point.width) < 10;
              const position = (point.width - minWidth) / (maxWidth - minWidth);
              
              return (
                <div
                  key={point.width}
                  className={`
                    absolute w-2 h-2 rounded-full border-2 transform -translate-x-1/2 -translate-y-1/2
                    ${isNearSnap 
                      ? 'bg-blue-500 border-blue-500 scale-125' 
                      : 'bg-white dark:bg-gray-800 border-gray-300 dark:border-gray-600'
                    }
                  `}
                  style={{ 
                    top: `${position * 100}%`,
                    left: '50%'
                  }}
                />
              );
            })}
            
            {/* Current width indicator */}
            <div className="absolute left-4 top-1/2 transform -translate-y-1/2 bg-gray-900 dark:bg-gray-100 text-white dark:text-gray-900 text-xs px-2 py-1 rounded whitespace-nowrap">
              {currentWidth}px
            </div>
          </div>
        </div>
      )}

      {/* Keyboard shortcuts tooltip */}
      {isHovering && !isDragging && (
        <div className="absolute -right-32 top-1/2 transform -translate-y-1/2 bg-gray-900 dark:bg-gray-100 text-white dark:text-gray-900 text-xs px-2 py-1 rounded whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity delay-500">
          <div>Cmd+B: Toggle</div>
          <div>Cmd+[/]: Resize</div>
          <div>Double-click: Reset</div>
        </div>
      )}
    </div>
  );
};

export default PanelResizer; 