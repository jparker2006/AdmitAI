"""CLI command for starting the debug frontend server."""

import argparse
import sys
from pathlib import Path

def add_frontend_commands(subparsers):
    """Add frontend-related commands to the CLI parser."""
    
    # Frontend debug server command
    frontend_parser = subparsers.add_parser(
        'frontend',
        help='Start the debug frontend interface'
    )
    frontend_parser.add_argument(
        '--host',
        default='127.0.0.1',
        help='Host to bind to (default: 127.0.0.1)'
    )
    frontend_parser.add_argument(
        '--port',
        type=int,
        default=8000,
        help='Port to bind to (default: 8000)'
    )
    frontend_parser.add_argument(
        '--no-reload',
        action='store_true',
        help='Disable auto-reload for development'
    )
    frontend_parser.set_defaults(func=run_frontend)

def run_frontend(args):
    """Run the debug frontend server."""
    try:
        from .server import start_server
        
        print("🚀 Starting Essay Agent Debug Frontend...")
        print(f"📍 Interface will be available at: http://{args.host}:{args.port}")
        print("🔧 Features available:")
        print("   • Real-time chat with agent")
        print("   • Memory state visualization")
        print("   • Tool execution monitoring")
        print("   • Planner decision tracking")
        print("   • Error logging and debugging")
        print("   • Debug data export functionality")
        print()
        print("Press Ctrl+C to stop the server")
        print("=" * 60)
        
        start_server(
            host=args.host,
            port=args.port,
            reload=not args.no_reload
        )
        
    except ImportError as e:
        print(f"❌ Error: Missing dependencies for frontend: {e}")
        print("Install with: pip install fastapi uvicorn")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 Frontend server stopped")
    except Exception as e:
        print(f"❌ Error starting frontend: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Allow running directly for testing
    parser = argparse.ArgumentParser(description="Essay Agent Debug Frontend")
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8000, help='Port to bind to')
    parser.add_argument('--no-reload', action='store_true', help='Disable auto-reload')
    
    args = parser.parse_args()
    run_frontend(args) 