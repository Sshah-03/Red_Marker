#!/usr/bin/env python3
"""
Entry point for Red Marker application
Run with: python run.py
"""

import uvicorn
from src.main import app
from src.config import HOST, PORT, DEBUG


if __name__ == "__main__":
    print("🔴 Red Marker - Image Annotation Tool")
    print(f"📍 Server: http://{HOST}:{PORT}")
    print(f"📚 API Docs: http://{HOST}:{PORT}/docs")
    print("⏹️  Press CTRL+C to shutdown\n")
    
    uvicorn.run(
        app,
        host=HOST,
        port=PORT,
        reload=DEBUG,
        log_level="info"
    )
