# Essay Agent Debug Frontend

A comprehensive web-based debug interface for the Essay Agent system that provides real-time visualization of all internal agent processes.

## 🎯 Purpose

This frontend is designed for:
- **Development & Debugging**: See exactly what the agent is doing internally
- **Tool Validation**: Verify all 54+ tools are working correctly
- **API Testing**: Test the agent's API responses before integrating with production UI
- **Performance Analysis**: Monitor tool execution times and success rates
- **Memory Inspection**: Understand how the agent's memory system works

## 🚀 Getting Started

### Prerequisites

```bash
pip install fastapi uvicorn
```

### Quick Start

1. **Start the debug server:**
   ```bash
   essay-agent frontend
   ```

2. **Open your browser:**
   ```
   http://localhost:8000
   ```

3. **Start debugging:**
   - Type messages in the chat interface
   - Watch real-time tool executions
   - Monitor memory state changes
   - View error logs

### Command Line Options

```bash
# Custom host and port
essay-agent frontend --host 0.0.0.0 --port 8080

# Disable auto-reload for production
essay-agent frontend --no-reload

# Get help
essay-agent frontend --help
```

## 📊 Interface Overview

### Chat Panel (Left Side)
- **Real-time chat** with the essay agent
- **Message history** with timestamps
- **Loading indicators** during processing
- **Error messages** if requests fail

### Memory Panel (Top Right)
- **Working Memory**: Recent chat history
- **Profile Data**: College, essay prompt, user info
- **Conversation Stats**: Message count, session info
- **Context Snapshots**: Current agent context

### Tool Execution Panel (Middle Right)
- **Tool Sequence**: Order of tool execution
- **Execution Times**: Performance metrics for each tool
- **Tool Arguments**: Parameters passed to tools
- **Tool Results**: Formatted output from each tool
- **Success/Failure Status**: Visual indicators

### Error Log Panel (Bottom Right)
- **Real-time Error Tracking**: All errors as they occur
- **Stack Traces**: Detailed error information
- **Error Context**: User input that caused errors
- **Timestamps**: When errors occurred

## 🔧 API Endpoints

The frontend exposes several useful API endpoints:

### Chat API
```http
POST /chat
Content-Type: application/json

{
  "message": "Help me brainstorm essay ideas",
  "user_id": "debug_user",
  "clear_history": false
}
```

### Debug Data
```http
GET /debug/full-state       # Complete debug state
POST /debug/clear           # Clear all debug data
GET /debug/tools            # List all available tools
```

### Frontend
```http
GET /                       # Main debug interface
```

## 🧪 Testing Tools & Examples

### Validate Tool Coverage
```bash
# Run the frontend evaluation script
python essay_agent/eval_frontend.py

# Test specific number of tools
FRONTEND_EVAL_LIMIT=20 python essay_agent/eval_frontend.py
```

### Example Test Messages
Try these messages to test different tools:

```
"Help me brainstorm essay ideas"           # Triggers brainstorm tools
"Create an outline for my essay"           # Triggers outline tools  
"Write a draft about overcoming challenges" # Triggers draft tools
"Revise this paragraph to be more vivid"   # Triggers revision tools
"Polish my essay for final submission"     # Triggers polish tools
"Score my essay on the admissions rubric"  # Triggers evaluation tools
```

## 📈 Monitoring Features

### Real-Time Updates
- **Live tool execution** with progress indicators
- **Memory state changes** after each interaction
- **Error logging** with context
- **Performance metrics** (execution times, success rates)

### Debug Data Export
- Click **"Export Debug Data"** to download complete session data
- Includes chat history, tool executions, memory snapshots, and errors
- Perfect for sharing debug sessions with team members

### Session Management
- **Clear History** button resets all state
- **Persistent sessions** maintain state across page refreshes
- **Multiple user support** via user_id parameter

## 🛠️ Development

### File Structure
```
essay_agent/frontend/
├── __init__.py          # Package initialization
├── server.py            # FastAPI server with debug capture
├── index.html           # Main interface (responsive design)
├── index.js             # Frontend JavaScript logic
├── cli.py               # CLI integration
└── README.md            # This file
```

### Key Features in Code

**DebugAgent Class** (`server.py`):
- Extends `AutonomousEssayAgent` with debug capture
- Hooks into reasoning, planning, and tool execution
- Captures planner prompts and tool sequences
- Sanitizes data for JSON serialization

**Frontend Interface** (`index.html` + `index.js`):
- Responsive grid layout
- Real-time updates via fetch API
- Color-coded status indicators
- Expandable JSON viewers

## 🎨 Customization

### Styling
The interface uses a dark theme optimized for development:
- **Color coding**: Green for success, red for errors, blue for info
- **Monospace fonts**: For code/JSON display
- **Responsive design**: Works on different screen sizes

### Adding New Panels
To add new debug panels:

1. **Update HTML**: Add new panel div in `index.html`
2. **Add JavaScript**: Create update function in `index.js`
3. **Extend Server**: Add data capture in `server.py`
4. **Update API**: Include new data in chat response

## 🔍 Troubleshooting

### Common Issues

**"Frontend files not found"**
- Ensure you're running from the correct directory
- Check that `index.html` exists in `essay_agent/frontend/`

**"Missing dependencies"**
- Run: `pip install fastapi uvicorn`
- Check that all requirements are installed

**"No tools executed"**
- Verify tools are registered in `TOOL_REGISTRY`
- Check that examples exist in `EXAMPLE_REGISTRY`
- Run the evaluation script to identify issues

**"Agent errors"**
- Check the error log panel for details
- Verify environment variables (API keys, etc.)
- Try simpler test messages first

### Debug Environment Variables

```bash
export ESSAY_AGENT_OFFLINE_TEST=1        # Use offline mode
export ESSAY_AGENT_SHOW_PROMPTS=1        # Show planner prompts
export ESSAY_AGENT_DEBUG_MEMORY=1        # Show memory details
export FRONTEND_EVAL_LIMIT=50            # Test more tools
```

## 🚀 Next Steps

1. **Run evaluation**: `python essay_agent/eval_frontend.py`
2. **Start frontend**: `essay-agent frontend`
3. **Test tools**: Try different message types
4. **Export data**: Use for API integration planning
5. **Share findings**: Export debug sessions for team review

This debug frontend provides complete visibility into the essay agent's internal workings, making it perfect for development, debugging, and API testing before production deployment! 