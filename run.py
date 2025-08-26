#!/usr/bin/env python3
"""
Medical RAG Chatbot - Production Runner
"""

import os
import sys
import uvicorn
from pathlib import Path

def main():
    """Run the Medical RAG Chatbot application"""
    
    # Ensure we're in the right directory
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    # Add current directory to Python path
    sys.path.insert(0, str(project_root))
    
    print("🏥 Starting Medical RAG Chatbot...")
    print("=" * 50)
    print("📍 Project Directory:", project_root)
    print("🐍 Python Version:", sys.version)
    print("📦 Working Directory:", os.getcwd())
    print("=" * 50)
    
    try:
        # Import and run the FastAPI app
        uvicorn.run(
            "backend.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            reload_dirs=[str(project_root)],
            log_level="info",
            access_log=True
        )
    except KeyboardInterrupt:
        print("\n👋 Shutting down Medical RAG Chatbot...")
    except Exception as e:
        print(f"❌ Failed to start application: {e}")
        print("\n💡 Troubleshooting steps:")
        print("1. Make sure PostgreSQL is running")
        print("2. Check your .env file configuration")
        print("3. Run: pip install -r requirements.txt")
        print("4. Run: python migrate_db.py")
        sys.exit(1)

if __name__ == "__main__":
    main()
