#!/usr/bin/env python3
"""
Red Marker Pro - Quick Start Script
Run this script to start the application with proper setup
"""

import os
import sys
import subprocess
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

def check_dependencies():
    """Check if all dependencies are installed"""
    print("🔍 Checking dependencies...")
    
    required_packages = [
        'fastapi',
        'uvicorn',
        'sqlalchemy',
        'pydantic',
        'pillow'
    ]
    
    try:
        for package in required_packages:
            __import__(package.replace('-', '_'))
        print("✅ All dependencies installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Run: pip install -r requirements.txt")
        return False

def initialize_database():
    """Initialize the database"""
    print("🗄️  Initializing database...")
    
    try:
        from src.database import init_db
        init_db()
        print("✅ Database initialized")
        return True
    except Exception as e:
        print(f"❌ Database initialization error: {e}")
        return False

def check_api_key():
    """Check if Gemini API key is configured"""
    print("🔑 Checking API configuration...")
    
    api_key = os.getenv("GEMINI_API_KEY")
    
    if api_key and api_key != "":
        print("✅ Gemini API key configured")
        return True
    else:
        print("⚠️  Warning: GEMINI_API_KEY not set")
        print("   Image generation will not work without it")
        print("   Set it with: export GEMINI_API_KEY='your-key'")
        return False

def create_directories():
    """Create necessary directories"""
    print("📁 Creating directories...")
    
    directories = [
        'data',
        'temp',
        'logs'
    ]
    
    for directory in directories:
        dir_path = project_root / directory
        dir_path.mkdir(exist_ok=True)
    
    print("✅ Directories created")

def start_server():
    """Start the FastAPI server"""
    print("\n" + "="*50)
    print("🚀 Starting Red Marker Pro...")
    print("="*50)
    print("\n📱 Access the application at: http://localhost:5000")
    print("📚 API Documentation at: http://localhost:5000/docs")
    print("\nPress Ctrl+C to stop the server\n")
    
    try:
        subprocess.run([
            "uvicorn",
            "app:app",
            "--host", "0.0.0.0",
            "--port", "5000",
            "--reload"
        ])
    except KeyboardInterrupt:
        print("\n\n✅ Server stopped")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        sys.exit(1)

def main():
    """Main setup and startup function"""
    print("\n" + "="*50)
    print("🔴 Red Marker Pro - Quick Start")
    print("="*50 + "\n")
    
    # Run checks
    if not check_dependencies():
        sys.exit(1)
    
    create_directories()
    
    if not initialize_database():
        print("⚠️  Continuing despite database initialization error...")
    
    check_api_key()
    
    # Start server
    print("\n" + "-"*50 + "\n")
    start_server()

if __name__ == "__main__":
    main()
