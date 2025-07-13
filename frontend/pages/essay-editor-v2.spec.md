# Essay Writer & Editor v2 - Functional Design Specification

## Overview
A streamlined essay writing workspace that prioritizes the editor experience above all else. The interface eliminates scrolling, maximizes writing space, and provides contextual access to all tools through overlays and floating panels. The design ensures the essay draft remains front and center while keeping powerful features just a click away.

## Core Design Principles
- **Editor-First**: Text editor dominates 90%+ of the workspace
- **Zero-Scroll**: All functionality fits in viewport without vertical scrolling
- **Contextual Access**: Tools appear when needed, hide when not
- **Fluid Responsiveness**: Layout adapts while prioritizing editor space
- **Keyboard-First**: Full functionality available via shortcuts

## Page Structure & Layout

### Main Layout Grid
```
┌─────────────────────────────────────────────────────────────────┐
│ Top Toolbar (Fixed Height: 56px)                               │
├─┬───────────────────────────────────────────────────────────┬─┤
│L│                                                           │R│
│e│               MAIN EDITOR                                 │i│
│f│            (Full Height)                                  │g│
│t│                                                           │h│
│ │                                                           │t│
│I│                                                           │ │
│c│                                                           │A│
│o│                                                           │I│
│n│                                                           │ │
│s│                                                           │I│
│ │                                                           │c│
│(│                                                           │o│
│4│                                                           │n│
│8│                                                           │(│
│p│                                                           │4│
│x│                                                           │8│
│)│                                                           │p│
│ │                                                           │x│
│ │                                                           │)│
└─┴───────────────────────────────────────────────────────────┴─┘
```

### Component Hierarchy
1. **Top Toolbar** (Fixed, 56px height)
2. **Left Icon Bar** (Fixed, 48px width, toggleable)
3. **Main Editor** (Fluid, fills remaining space)
4. **Right AI Icon** (Fixed, 48px width)
5. **Overlay Panels** (Contextual, over editor)
6. **Floating Toolbars** (Contextual, over editor)

## Component Specifications

### 1. Top Toolbar (Fixed, Single Row)

#### Structure
- **Left Section** (30%): University & Prompt Info
- **Center Section** (40%): Word Count & Progress
- **Right Section** (30%): Version Control & Status

#### Left Section Components
- University badge with institution logo/name
- Prompt title (truncated with tooltip on hover)
- Edit icon to open prompt selector overlay

#### Center Section Components
- Current word count / target (e.g., "247 / 650")
- Horizontal progress bar (12px height)
- Progress percentage and status indicator

#### Right Section Components
- Version dropdown (compact, shows current version)
- Auto-save timestamp ("Saved 2 min ago")
- Settings icon for preferences
- Export/share icons

### 2. Left Icon Bar (Collapsible)

#### Default State
- 48px width vertical bar
- 4 primary icons vertically stacked
- Hover reveals tooltips
- Click toggles associated overlay panel

#### Icon Functions
1. **Prompts Icon**: Opens university/prompt management overlay
2. **Outline Icon**: Slides in outline builder panel from left
3. **History Icon**: Opens version history overlay
4. **Tips Icon**: Opens writing tips overlay

#### Collapsed State
- Toggleable via hamburger icon at top
- When collapsed, icons move to top toolbar as overflow menu
- Keyboard shortcut: `Ctrl/Cmd + \`

### 3. Main Editor (Full-Space Priority)

#### Editor Container
- **Dimensions**: Fills all remaining space after toolbars/sidebars
- **Minimum Height**: Viewport height - 56px (toolbar)
- **Width**: 100% of available horizontal space
- **Padding**: 24px all sides for comfortable reading

#### Editor Features
- Plain text or rich text toggle
- Paragraph numbering (optional, toggleable)
- Real-time word count
- Auto-save every 30 seconds
- Undo/redo with Ctrl+Z/Ctrl+Y
- Find/replace with Ctrl+F

#### Text Selection Toolbar
- **Trigger**: Appears when user selects text (>5 words)
- **Position**: Floating above selection
- **Actions**: Improve Style, Shorten, Elaborate, Clarify, Comment
- **Animation**: Fade in/out with smooth positioning

#### Keyboard Shortcuts
- `Ctrl/Cmd + O`: Toggle outline panel
- `Ctrl/Cmd + H`: Toggle history panel
- `Ctrl/Cmd + T`: Toggle tips panel
- `Ctrl/Cmd + P`: Open prompt selector
- `Ctrl/Cmd + Enter`: Get AI feedback
- `Ctrl/Cmd + S`: Manual save & create version

### 4. Right AI Icon (Fixed Position)

#### Default State
- 48px width chat/AI icon
- Positioned at right edge, vertically centered
- Subtle animation or indicator when AI is processing
- Click expands AI assistant panel

#### AI Assistant Panel
- **Trigger**: Click on AI icon
- **Layout**: Overlay panel, 320px width
- **Position**: Slides in from right edge
- **Backdrop**: Semi-transparent overlay (20% opacity)
- **Height**: 70% of viewport height, vertically centered

#### Panel Contents
- AI chat interface at top
- Quick action buttons (Generate Outline, Draft Section, Get Feedback)
- AI operation status and history
- Close button (X) in top-right corner

### 5. Overlay Panels (Contextual)

#### Outline Builder Overlay
- **Trigger**: Left icon bar "Outline" or Ctrl+O
- **Layout**: 320px width panel sliding from left
- **Content**: Hierarchical outline with drag-and-drop
- **Features**: Add/edit/delete items, expand/collapse, lock items
- **Toggle**: Click outline icon again or click outside panel

#### Version History Overlay
- **Trigger**: Left icon bar "History" or Ctrl+H
- **Layout**: 400px width panel sliding from left
- **Content**: Chronological version list with previews
- **Features**: Compare versions, restore, export specific version
- **Pagination**: Show 10 versions at a time with load more

#### Writing Tips Overlay
- **Trigger**: Left icon bar "Tips" or Ctrl+T
- **Layout**: 300px width panel sliding from left
- **Content**: Categorized tips with examples
- **Features**: Search tips, bookmark favorites, contextual suggestions
- **Categories**: Structure, Style, Grammar, Content

#### Prompt Management Overlay
- **Trigger**: Left icon bar "Prompts" or edit icon in toolbar
- **Layout**: Modal dialog, 600px width, centered
- **Content**: University search, prompt cards, word limits
- **Features**: Add/edit/delete prompts, reorder, set active

### 6. Responsive Behavior

#### Breakpoint Adaptations

**Desktop (1200px+)**
- Full layout as specified
- All panels and toolbars visible
- Maximum editor space utilization

**Tablet (768px - 1199px)**
- Left icon bar auto-collapses to save space
- Overlay panels reduce to 280px width
- Top toolbar sections adjust proportionally

**Mobile (< 768px)**
- Left icon bar moves to top toolbar as hamburger menu
- AI panel becomes full-width bottom sheet
- Top toolbar sections stack or hide non-essential items
- Text selection toolbar becomes bottom-anchored

#### Window Height Adaptations
- **Minimum Height**: 600px for functional editing
- **Short Viewports** (< 800px): Compress toolbar to 48px height
- **Tall Viewports** (> 1200px): Maintain proportions, maximize editor

### 7. Zero-Scroll Implementation

#### Vertical Space Management
- Top toolbar: Fixed 56px
- Left sidebar: Fixed 48px width (when visible)
- Right AI icon: Fixed 48px width
- Editor: Remaining space with internal scrolling only

#### Content Overflow Strategies
- **Long Outlines**: Internal scrolling within outline panel
- **Version History**: Pagination with "Load More" button
- **Writing Tips**: Accordion sections with expand/collapse
- **AI Chat**: Internal scrolling within AI panel

#### Fluid Layout Calculations
```
Editor Height = Viewport Height - Top Toolbar Height
Editor Width = Viewport Width - Left Bar Width - Right Icon Width
```

### 8. Accessibility & Keyboard Navigation

#### Focus Management
- Tab order: Toolbar → Left Icons → Editor → AI Icon
- Escape key closes any open overlay
- Arrow keys navigate within overlays
- Enter activates buttons and toggles

#### Screen Reader Support
- ARIA labels for all interactive elements
- Live regions for word count and save status
- Proper heading hierarchy in overlays
- Alternative text for icons and buttons

#### Keyboard Shortcuts Summary
```
Ctrl/Cmd + O     - Toggle outline panel
Ctrl/Cmd + H     - Toggle history panel  
Ctrl/Cmd + T     - Toggle tips panel
Ctrl/Cmd + P     - Open prompt selector
Ctrl/Cmd + \     - Toggle left sidebar
Ctrl/Cmd + Enter - Get AI feedback
Ctrl/Cmd + S     - Save & create version
Ctrl/Cmd + F     - Find in document
Escape           - Close active overlay
```

## User Workflows

### Primary Workflow: Focused Writing
1. User opens essay editor
2. Editor fills screen with minimal UI
3. Begin typing immediately in full-screen editor
4. Access tools via keyboard shortcuts or quick icons
5. Tools appear as overlays, never disrupting editor flow

### Secondary Workflow: Outline-First Writing
1. Press Ctrl+O to open outline panel
2. Build outline structure with drag-and-drop
3. Close outline panel (Ctrl+O again)
4. Draft directly in editor using outline as reference
5. Reopen outline as needed for navigation

### Tertiary Workflow: AI-Assisted Revision
1. Select text that needs improvement
2. Floating toolbar appears with AI options
3. Choose improvement type (style, length, clarity)
4. AI suggestions appear in right panel
5. Accept/reject changes without leaving editor

## Technical Requirements

### Performance Targets
- **Initial Load**: < 1.5 seconds
- **Panel Animations**: 60fps, 300ms duration
- **Text Selection Response**: < 100ms
- **Auto-save**: Non-blocking, < 500ms

### Browser Support
- Chrome 90+, Firefox 88+, Safari 14+, Edge 90+
- CSS Grid and Flexbox required
- JavaScript ES2020 features
- Local storage for preferences and drafts

### Responsive Performance
- Smooth animations on all devices
- Touch-friendly targets (44px minimum)
- Gesture support for mobile panel controls
- Adaptive typography scaling

## Success Metrics

### User Experience
- **Time to First Word**: < 5 seconds from page load
- **Writing Flow Interruption**: < 10% of sessions with UI-related stops
- **Tool Accessibility**: All features reachable within 2 clicks/keystrokes

### Technical Performance
- **Layout Stability**: No content shifting during panel animations
- **Memory Usage**: < 100MB for typical essay session
- **Battery Impact**: Minimal drain from animations and auto-save

### Content Quality
- **Word Count Accuracy**: Real-time tracking within 1 word
- **Auto-save Reliability**: 99.9% success rate
- **Version Integrity**: No data loss during version management

This specification creates a distraction-free writing environment that puts the essay draft at the absolute center of the user experience while maintaining easy access to all powerful features through contextual, overlay-based interactions. 