# Essay Editor v3 - Functional Specification

## Overview
Evolution of the Essay Editor to include a powerful hierarchical navigation system with a collapsible left panel and quick-access recent tabs, optimized for speed and discoverability.

## 1. Layout Architecture

### 1.1 Main Layout Structure
```
┌─────────────────────────────────────────────────────────────┐
│ [Top Toolbar - Word Count, Save, Settings, etc.]           │
├─────────────────────────────────────────────────────────────┤
│ [Recent Essays Tabs Row]                                    │
├─────────────────────────────────────────────────────────────┤
│ [Left Panel] │ [Main Editor Area]          │ [Right Tools] │
│              │                             │               │
│              │                             │               │
│              │                             │               │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Panel Dimensions
- **Left Panel**: 280px default width (resizable 200px-400px)
- **Recent Tabs Row**: 48px height
- **Main Editor**: Remaining space
- **Right Tools**: 60px width (unchanged)

## 2. Left Panel Hierarchy System

### 2.1 Tree Structure
```
📁 My Essays
├── 📁 Stanford University (3)
│   ├── 📄 Personal Statement (2)
│   │   ├── 📝 Draft v1.0 (Current)
│   │   └── 📝 Draft v0.9
│   ├── 📄 Short Answer - Community (1)
│   │   └── 📝 Draft v1.0
│   └── 📄 Leadership Essay (0)
├── 📁 MIT (1)
│   └── 📄 Personal Statement (1)
│       └── 📝 Draft v1.0
└── 📁 + Add New School
```

### 2.2 Node Types & Behaviors

#### Root Node: "My Essays"
- **Always visible and expanded**
- **Count**: Total essays across all schools
- **Actions**: None (system root)

#### School Nodes (Level 1)
- **Display**: School name + count of total essays
- **States**: Expanded/Collapsed (persistent per session)
- **Default**: Most recently used school expanded
- **Context Menu**: Rename School, Delete School, Add New Prompt
- **Keyboard**: Enter to toggle expand/collapse

#### Prompt Nodes (Level 2)
- **Display**: Prompt title + count of drafts/versions
- **States**: Expanded/Collapsed (persistent per session)
- **Default**: Currently active prompt expanded
- **Context Menu**: Rename Prompt, Delete Prompt, New Version, Duplicate Prompt
- **Keyboard**: Enter to toggle expand/collapse

#### Draft Nodes (Level 3 - Leaf)
- **Display**: "Draft v{version}" or custom name + status indicators
- **Status Indicators**: 
  - (Current) - actively being edited
  - (Saved 2m ago) - last save time
  - (Unsaved) - has unsaved changes
- **Context Menu**: Rename Draft, Delete Draft, Duplicate Draft, Export
- **Keyboard**: Enter to open in editor

### 2.3 Visual Indicators
- **Folder Icons**: Different icons for schools vs prompts vs drafts
- **Expand/Collapse**: Arrow indicators (▶ collapsed, ▼ expanded)
- **Count Badges**: Numbers in parentheses showing item counts
- **Active State**: Currently selected draft highlighted
- **Hover States**: Subtle background change on hover
- **Loading States**: Spinner for async operations

## 3. Quick-Access Controls

### 3.1 Search/Filter Input
- **Position**: Top of left panel, above tree
- **Placeholder**: "Filter by school or prompt..."
- **Behavior**: Real-time filtering as user types
- **Scope**: Searches school names, prompt titles, and draft names
- **Results**: Collapses non-matching branches, highlights matches
- **Clear**: X icon to clear filter and restore full tree

### 3.2 New Essay Button
- **Position**: Below search input, above tree
- **Style**: Primary button with + icon
- **Label**: "+ New Essay"
- **Behavior**: 
  - Shows dropdown with recent schools + "Add New School"
  - If school selected: Shows prompt selection dialog
  - If "Add New School": Shows school creation dialog
  - Creates new draft under selected school/prompt

### 3.3 Panel Header Actions
- **Collapse Button**: Arrow icon to collapse panel to icon rail
- **Refresh Button**: Sync icon to refresh tree data
- **Settings Button**: Gear icon for panel preferences

## 4. Recent Essays Tabs System

### 4.1 Tab Structure
```
[Stanford - Personal Statement - v1.0] [×] [MIT - Essay 1 - v2.0] [×] [More ▼]
```

### 4.2 Tab Behavior
- **Display Format**: "School - Prompt - Version"
- **Maximum Visible**: 5 tabs (responsive)
- **Overflow**: "More..." dropdown menu
- **Active State**: Currently selected tab highlighted
- **Close Button**: × icon on each tab (except active if it's the only tab)
- **Reordering**: Drag-and-drop to reorder tabs
- **Scrolling**: Horizontal scroll on narrow screens

### 4.3 Tab Actions
- **Left Click**: Switch to that essay
- **Right Click**: Context menu with:
  - Open in New Window
  - Pin Tab (prevents accidental closure)
  - Close Tab
  - Close Other Tabs
  - Duplicate Essay
- **Middle Click**: Close tab (if not pinned)
- **Keyboard**: Cmd+1-5 to switch to tab by position

### 4.4 Tab States
- **Active**: Currently editing
- **Modified**: Has unsaved changes (dot indicator)
- **Pinned**: Pin icon, cannot be closed accidentally
- **Loading**: Spinner while loading essay content

## 5. Contextual Sync System

### 5.1 Tree-to-Editor Sync
- **Selection**: Clicking any draft node loads it in editor
- **Auto-Tab**: If essay not in recent tabs, adds new tab
- **Auto-Highlight**: Brief highlight animation on tree node selection
- **Auto-Expand**: Expands parent nodes if needed to show selection

### 5.2 Tab-to-Tree Sync
- **Tab Switch**: Highlights corresponding draft node in tree
- **Tree Scroll**: Auto-scrolls tree to show highlighted node
- **Expand Parents**: Expands school/prompt nodes to show active draft
- **Highlight Duration**: 2-second highlight fade on tree node

### 5.3 Editor-to-Both Sync
- **Save Action**: Updates both tab and tree node indicators
- **Version Change**: Updates version numbers in both locations
- **Status Updates**: Reflects unsaved changes in both UI areas

## 6. Keyboard Navigation & Accessibility

### 6.1 Tree Navigation
- **Arrow Keys**: Up/Down to navigate nodes, Left/Right to collapse/expand
- **Enter**: Open draft or toggle folder expansion
- **Space**: Select/deselect node
- **Delete**: Delete selected node (with confirmation)
- **F2**: Rename selected node
- **Cmd+N**: New essay dialog
- **Cmd+F**: Focus search input

### 6.2 Tab Navigation
- **Cmd+T**: New tab
- **Cmd+W**: Close current tab
- **Cmd+Shift+W**: Close all tabs
- **Cmd+1-5**: Switch to tab by position
- **Cmd+Shift+Left/Right**: Reorder tabs
- **Tab**: Cycle through tabs

### 6.3 Panel Navigation
- **Cmd+B**: Toggle panel collapse/expand
- **Cmd+Shift+E**: Focus tree view
- **Cmd+Shift+F**: Focus search input
- **Escape**: Clear search or close context menus

### 6.4 Accessibility Features
- **ARIA Labels**: All interactive elements properly labeled
- **Screen Reader**: Tree structure announced correctly
- **Focus Management**: Logical tab order throughout interface
- **High Contrast**: Sufficient contrast ratios for all text/backgrounds
- **Reduced Motion**: Respects prefers-reduced-motion settings

## 7. Responsive Behavior

### 7.1 Panel Resizing
- **Drag Handle**: Vertical gutter between panel and editor
- **Resize Range**: 200px minimum, 400px maximum
- **Snap Points**: 280px (default), 240px (compact), 320px (expanded)
- **Persistence**: Remembers width across sessions

### 7.2 Panel Collapse States
- **Collapsed**: 48px wide icon rail
- **Icons**: School/prompt icons with tooltip on hover
- **Hover Expand**: Temporarily expands on hover (300ms delay)
- **Quick Access**: Click to expand permanently

### 7.3 Mobile Adaptations (< 768px)
- **Panel**: Slides over editor as overlay
- **Tabs**: Horizontal scroll with momentum
- **Touch**: Swipe gestures for navigation
- **Compact**: Reduced padding and font sizes

### 7.4 Tablet Adaptations (768px - 1024px)
- **Panel**: Narrower default width (240px)
- **Tabs**: Show 3-4 tabs maximum
- **Touch**: Larger touch targets
- **Hybrid**: Supports both touch and mouse

## 8. Zero Scroll Fit Requirements

### 8.1 Viewport Optimization (1080p)
- **Total Height**: 1080px available
- **Top Toolbar**: 64px
- **Recent Tabs**: 48px
- **Remaining**: 968px for panel + editor
- **Panel Height**: Auto-fits with internal scroll
- **Editor Height**: Fills remaining space

### 8.2 Overflow Handling
- **Tree View**: Internal scroll when content exceeds height
- **Tab Row**: Horizontal scroll or "More..." menu
- **Editor**: Internal scroll for content
- **No Double Scroll**: Prevent nested scrollable areas

### 8.3 Content Prioritization
- **Tree**: Always shows root + first level
- **Tabs**: Always shows active tab
- **Editor**: Always visible with minimum 400px height
- **Overflow**: Graceful degradation with scroll or menus

## 9. Performance & UX Optimizations

### 9.1 Loading Strategies
- **Tree Lazy Loading**: Load school contents on first expansion
- **Tab Preloading**: Preload adjacent tabs for instant switching
- **Search Debouncing**: 300ms delay before filtering
- **Virtual Scrolling**: For large lists of drafts

### 9.2 Animation & Transitions
- **Tree Expand/Collapse**: 200ms ease-out
- **Tab Switching**: 150ms ease-in-out
- **Panel Resize**: Real-time during drag
- **Hover Effects**: 100ms ease-in

### 9.3 Data Persistence
- **Panel State**: Width, collapsed state, expanded nodes
- **Tab State**: Open tabs, order, pinned status
- **Recent Activity**: Most recently used essays
- **Search History**: Recent search terms

## 10. Implementation Priority

### Phase 1: Core Structure
1. Left panel layout with resizable gutter
2. Basic tree view with expand/collapse
3. Recent tabs row with basic switching
4. Tree-to-editor navigation

### Phase 2: Enhanced Features
1. Search/filter functionality
2. Context menus for all node types
3. Drag-and-drop tab reordering
4. Keyboard navigation

### Phase 3: Advanced UX
1. Contextual sync animations
2. Mobile/tablet responsive design
3. Performance optimizations
4. Accessibility enhancements

### Phase 4: Polish
1. Advanced tab features (pinning, right-click menus)
2. Panel collapse/expand animations
3. Zero-scroll optimizations
4. User preferences and persistence

## 11. Success Metrics

### 11.1 Speed Metrics
- **Essay Opening**: < 200ms from click to content load
- **Tree Navigation**: < 100ms for expand/collapse
- **Tab Switching**: < 150ms transition time
- **Search Results**: < 300ms for filter results

### 11.2 Usability Metrics
- **Discoverability**: Users find essays in < 3 clicks
- **Efficiency**: 50% reduction in navigation time vs. v2
- **Error Reduction**: 90% fewer accidental closures
- **Accessibility**: 100% keyboard navigable

This specification provides a comprehensive blueprint for implementing the Essay Editor v3 with powerful hierarchical navigation and recent tabs system, prioritizing speed, discoverability, and minimal clicks while maintaining accessibility and responsive design. 