/**
 * Essay Agent Debug Frontend JavaScript
 * Handles chat interface and debug data visualization
 */

// Global state
let isLoading = false;
let debugHistory = [];
let isOnboarded = false;

// DOM elements
const chatMessages = document.getElementById('chat-messages');
const messageInput = document.getElementById('message-input');
const memoryContent = document.getElementById('memory-content');
const toolsContent = document.getElementById('tools-content');
const errorsContent = document.getElementById('errors-content');
const statusElement = document.getElementById('status');

// Onboarding elements
const onboardingContainer = document.getElementById('onboarding-container');
const mainContainer = document.getElementById('main-container');
const onboardingForm = document.getElementById('onboarding-form');
const essayPromptInput = document.getElementById('essay-prompt');
const schoolInput = document.getElementById('school');
const wordCountElement = document.getElementById('word-count');
const setupError = document.getElementById('setup-error');

// Initialize the interface
document.addEventListener('DOMContentLoaded', function() {
    console.log('Essay Agent Debug Interface initialized');
    updateStatus('Setup Required', 'pending');
    
    // Check if already onboarded
    checkOnboardingStatus();
    
    // Setup onboarding event listeners
    setupOnboardingListeners();
    
    // Load any existing debug state
    loadDebugState();
});

/**
 * Handle enter key press in message input
 */
function handleKeyPress(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
}

/**
 * Check onboarding status and show appropriate interface
 */
async function checkOnboardingStatus() {
    try {
        const response = await fetch('/debug/full-state');
        if (response.ok) {
            const debugState = await response.json();
            
            // Check if user has completed onboarding
            const latestMemory = debugState.memory_snapshots?.[debugState.memory_snapshots.length - 1];
            if (latestMemory?.onboarding_completed) {
                isOnboarded = true;
                showChatInterface();
                updateStatus('Ready', 'success');
            } else {
                showOnboardingInterface();
            }
        } else {
            showOnboardingInterface();
        }
    } catch (error) {
        console.log('No existing session found, showing onboarding');
        showOnboardingInterface();
    }
}

/**
 * Show onboarding interface
 */
function showOnboardingInterface() {
    onboardingContainer.style.display = 'flex';
    mainContainer.style.display = 'none';
    updateStatus('Setup Required', 'pending');
    
    // Focus on first input
    if (essayPromptInput) {
        essayPromptInput.focus();
    }
}

/**
 * Show chat interface
 */
function showChatInterface() {
    onboardingContainer.style.display = 'none';
    mainContainer.style.display = 'grid';
    updateStatus('Ready', 'success');
    
    // Focus on chat input
    if (messageInput) {
        messageInput.focus();
    }
}

/**
 * Setup onboarding event listeners
 */
function setupOnboardingListeners() {
    // Word count for essay prompt
    if (essayPromptInput && wordCountElement) {
        essayPromptInput.addEventListener('input', updateWordCount);
    }
    
    // Form submission
    if (onboardingForm) {
        onboardingForm.addEventListener('submit', handleSetupSubmission);
    }
}

/**
 * Update word count display
 */
function updateWordCount() {
    const text = essayPromptInput.value.trim();
    const words = text ? text.split(/\s+/).length : 0;
    
    wordCountElement.textContent = words;
    
    // Add warning/error classes
    wordCountElement.className = '';
    if (words > 650) {
        wordCountElement.className = 'error';
    } else if (words > 600) {
        wordCountElement.className = 'warning';
    }
}

/**
 * Handle setup form submission
 */
async function handleSetupSubmission(event) {
    event.preventDefault();
    
    const essayPrompt = essayPromptInput.value.trim();
    const school = schoolInput.value.trim();
    
    // Clear any previous errors
    hideSetupError();
    
    // Validate inputs
    if (!essayPrompt) {
        showSetupError('Please enter your essay prompt');
        return;
    }
    
    if (!school) {
        showSetupError('Please enter the school name');
        return;
    }
    
    // Check word count
    const words = essayPrompt.split(/\s+/).length;
    if (words > 650) {
        showSetupError(`Essay prompt is too long (${words} words). Please keep it under 650 words.`);
        return;
    }
    
    // Submit setup
    await submitSetup(essayPrompt, school);
}

/**
 * Submit setup data to backend
 */
async function submitSetup(essayPrompt, school) {
    const setupBtn = document.getElementById('setup-btn');
    
    try {
        // Show loading state
        setupBtn.disabled = true;
        setupBtn.innerHTML = '<div class="loading"></div> Setting up...';
        
        const response = await fetch('/api/setup', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                essay_prompt: essayPrompt,
                school: school,
                user_id: 'debug_user'
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            isOnboarded = true;
            showChatInterface();
            
            // Add welcome message to chat
            addMessageToChat('agent', `Great! I'm ready to help you with your ${school} essay. What would you like to work on first?`);
            
            // Update memory panel with setup info
            updateMemoryPanel({
                essay_prompt: essayPrompt,
                college: school,
                onboarding_completed: true
            });
            
        } else {
            showSetupError(data.detail || 'Setup failed. Please try again.');
        }
        
    } catch (error) {
        console.error('Setup error:', error);
        showSetupError('Network error. Please check your connection and try again.');
    } finally {
        // Restore button state
        setupBtn.disabled = false;
        setupBtn.innerHTML = 'Start Essay Session';
    }
}

/**
 * Show setup error message
 */
function showSetupError(message) {
    setupError.textContent = message;
    setupError.style.display = 'block';
}

/**
 * Hide setup error message
 */
function hideSetupError() {
    setupError.style.display = 'none';
}

/**
 * Send a message to the agent
 */
async function sendMessage() {
    if (!isOnboarded) {
        showSetupError('Please complete setup first');
        return;
    }
    
    const message = messageInput.value.trim();
    if (!message || isLoading) return;
    
    // Add user message to chat
    addMessageToChat('user', message);
    
    // Clear input
    messageInput.value = '';
    
    // Show loading state
    setLoading(true);
    updateStatus('Processing...', 'pending');
    
    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                user_id: 'debug_user'
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        // Add agent response to chat
        addMessageToChat('agent', data.response);
        
        // Update debug panels with the received data
        updateDebugPanels(data.debug_data);
        
        // Store in debug history
        debugHistory.push({
            timestamp: new Date().toISOString(),
            user_message: message,
            agent_response: data.response,
            debug_data: data.debug_data
        });
        
        updateStatus('Ready', 'success');
        
    } catch (error) {
        console.error('Error sending message:', error);
        addMessageToChat('system', `Error: ${error.message}`);
        updateStatus('Error', 'error');
        
        // Add to error log
        addErrorToLog(error.message, message);
    } finally {
        setLoading(false);
        messageInput.focus();
    }
}

/**
 * Add a message to the chat display
 */
function addMessageToChat(type, content) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    
    const contentDiv = document.createElement('div');
    contentDiv.textContent = content;
    
    const timeDiv = document.createElement('div');
    timeDiv.className = 'message-time';
    timeDiv.textContent = new Date().toLocaleTimeString();
    
    messageDiv.appendChild(contentDiv);
    messageDiv.appendChild(timeDiv);
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

/**
 * Update all debug panels with new data
 */
function updateDebugPanels(debugData) {
    updateMemoryPanel(debugData.current_memory);
    updateToolsPanel(debugData.recent_tools);
    updateErrorsPanel(debugData.recent_errors);
}

/**
 * Update the memory panel
 */
function updateMemoryPanel(memoryData) {
    if (!memoryData || Object.keys(memoryData).length === 0) {
        memoryContent.innerHTML = `
            <div class="memory-item">
                <div class="memory-label">Status</div>
                <div class="memory-value">No memory data available</div>
            </div>
        `;
        return;
    }
    
    let html = '';
    
    // Working memory
    if (memoryData.working_memory && memoryData.working_memory.length > 0) {
        html += `
            <div class="memory-item">
                <div class="memory-label">Recent Chat (${memoryData.working_memory.length} messages)</div>
                <div class="memory-value">${memoryData.working_memory.slice(-3).join(' | ')}</div>
            </div>
        `;
    }
    
    // Profile data
    if (memoryData.profile) {
        html += `
            <div class="memory-item">
                <div class="memory-label">College</div>
                <div class="memory-value">${memoryData.profile || 'Not set'}</div>
            </div>
        `;
    }
    
    if (memoryData.essay_prompt) {
        html += `
            <div class="memory-item">
                <div class="memory-label">Essay Prompt</div>
                <div class="memory-value">${truncateText(memoryData.essay_prompt, 100)}</div>
            </div>
        `;
    }
    
    // Conversation stats
    if (memoryData.conversation_count !== undefined) {
        html += `
            <div class="memory-item">
                <div class="memory-label">Total Messages</div>
                <div class="memory-value">${memoryData.conversation_count}</div>
            </div>
        `;
    }
    
    if (!html) {
        html = `
            <div class="memory-item">
                <div class="memory-label">Status</div>
                <div class="memory-value">Memory initialized</div>
            </div>
        `;
    }
    
    memoryContent.innerHTML = html;
}

/**
 * Update the tools panel
 */
function updateToolsPanel(toolsData) {
    if (!toolsData || toolsData.length === 0) {
        toolsContent.innerHTML = `
            <div style="text-align: center; opacity: 0.6; padding: 20px;">
                No tools executed yet
            </div>
        `;
        return;
    }
    
    let html = '';
    
    toolsData.forEach((tool, index) => {
        const successClass = tool.success ? 'success' : 'error';
        const statusIcon = tool.success ? '✅' : '❌';
        
        html += `
            <div class="tool-execution ${successClass}">
                <div class="tool-header">
                    <span class="tool-name">${statusIcon} ${tool.tool_name || 'Unknown Tool'}</span>
                    <span class="tool-time">${tool.execution_time ? (tool.execution_time * 1000).toFixed(0) + 'ms' : 'N/A'}</span>
                </div>
                
                ${tool.tool_args && Object.keys(tool.tool_args).length > 0 ? `
                    <div class="tool-args">
                        <strong>Args:</strong> ${JSON.stringify(tool.tool_args, null, 2)}
                    </div>
                ` : ''}
                
                ${tool.result ? `
                    <div class="tool-result ${tool.success ? '' : 'error'}">
                        <strong>Result:</strong> ${formatToolResult(tool.result)}
                    </div>
                ` : ''}
                
                ${tool.error ? `
                    <div class="tool-result error">
                        <strong>Error:</strong> ${tool.error}
                    </div>
                ` : ''}
            </div>
        `;
    });
    
    toolsContent.innerHTML = html;
}

/**
 * Update the errors panel
 */
function updateErrorsPanel(errorsData) {
    if (!errorsData || errorsData.length === 0) {
        errorsContent.innerHTML = `
            <div style="text-align: center; opacity: 0.6; padding: 20px;">
                No errors logged
            </div>
        `;
        return;
    }
    
    let html = '';
    
    errorsData.forEach(error => {
        const timestamp = error.timestamp || new Date().toISOString();
        const errorMsg = error.error || error.message || 'Unknown error';
        
        html += `
            <div class="error-entry">
                <div class="error-time">${new Date(timestamp).toLocaleString()}</div>
                <div class="error-message">${escapeHtml(errorMsg)}</div>
            </div>
        `;
    });
    
    errorsContent.innerHTML = html;
}

/**
 * Add an error to the log
 */
function addErrorToLog(errorMessage, userInput = '') {
    const errorEntry = {
        timestamp: new Date().toISOString(),
        error: errorMessage,
        user_input: userInput
    };
    
    updateErrorsPanel([errorEntry]);
}

/**
 * Format tool results for display
 */
function formatToolResult(result) {
    if (typeof result === 'string') {
        return truncateText(result, 200);
    }
    
    if (typeof result === 'object') {
        try {
            return JSON.stringify(result, null, 2);
        } catch (e) {
            return String(result);
        }
    }
    
    return String(result);
}

/**
 * Update loading state
 */
function setLoading(loading) {
    isLoading = loading;
    const sendButton = document.querySelector('.chat-input .btn');
    
    if (loading) {
        sendButton.innerHTML = '<div class="loading"></div>';
        sendButton.disabled = true;
        messageInput.disabled = true;
    } else {
        sendButton.innerHTML = 'Send';
        sendButton.disabled = false;
        messageInput.disabled = false;
    }
}

/**
 * Update status indicator
 */
function updateStatus(text, type) {
    statusElement.textContent = text;
    statusElement.className = `status-${type}`;
}

/**
 * Clear chat history and debug state
 */
async function clearHistory() {
    if (!confirm('Are you sure you want to clear all history and return to setup?')) {
        return;
    }
    
    try {
        const response = await fetch('/debug/clear', {
            method: 'POST'
        });
        
        if (response.ok) {
            // Reset onboarding state
            isOnboarded = false;
            
            // Clear form inputs
            if (essayPromptInput) essayPromptInput.value = '';
            if (schoolInput) schoolInput.value = '';
            updateWordCount();
            hideSetupError();
            
            // Show onboarding interface
            showOnboardingInterface();
            
            // Clear debug history
            debugHistory = [];
        }
    } catch (error) {
        console.error('Error clearing history:', error);
        addErrorToLog(`Failed to clear history: ${error.message}`);
    }
}

/**
 * Export debug data
 */
function exportDebugData() {
    const exportData = {
        timestamp: new Date().toISOString(),
        debug_history: debugHistory,
        current_state: {
            chat_messages: Array.from(chatMessages.children).map(msg => ({
                type: msg.className.replace('message ', ''),
                content: msg.textContent
            }))
        }
    };
    
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = `essay-agent-debug-${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    
    URL.revokeObjectURL(url);
    
    updateStatus('Debug data exported', 'success');
}

/**
 * Load existing debug state from server
 */
async function loadDebugState() {
    try {
        const response = await fetch('/debug/full-state');
        if (response.ok) {
            const debugState = await response.json();
            
            // Load chat history if available
            if (debugState.chat_history && debugState.chat_history.length > 0) {
                chatMessages.innerHTML = ''; // Clear welcome message
                
                debugState.chat_history.forEach(exchange => {
                    addMessageToChat('user', exchange.user);
                    addMessageToChat('agent', exchange.agent);
                });
            }
            
            // Update debug panels
            if (debugState.memory_snapshots && debugState.memory_snapshots.length > 0) {
                updateMemoryPanel(debugState.memory_snapshots[debugState.memory_snapshots.length - 1]);
            }
            
            if (debugState.tool_executions) {
                updateToolsPanel(debugState.tool_executions.slice(-5));
            }
            
            if (debugState.error_log) {
                updateErrorsPanel(debugState.error_log.slice(-5));
            }
        }
    } catch (error) {
        console.log('No existing debug state found:', error);
    }
}

/**
 * Utility functions
 */
function truncateText(text, maxLength) {
    if (typeof text !== 'string') return String(text);
    return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Auto-refresh debug state periodically
setInterval(async () => {
    if (!isLoading) {
        try {
            const response = await fetch('/debug/tools');
            if (response.ok) {
                const data = await response.json();
                // Could update tool count in header or show available tools
                console.log(`Available tools: ${data.count}`);
            }
        } catch (error) {
            // Silently ignore refresh errors
        }
    }
}, 30000); // Refresh every 30 seconds 