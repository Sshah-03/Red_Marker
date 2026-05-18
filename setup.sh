#!/bin/bash

# Red Marker Pro - Setup Script
# This script sets up the enhanced Red Marker application

echo "🔴 Red Marker Pro - Setup Script"
echo "=================================="
echo ""

# Check Python version
echo "✓ Checking Python version..."
python_version=$(python3 --version 2>&1)
echo "  Found: $python_version"

# Create virtual environment
echo ""
echo "✓ Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "  Virtual environment created"
else
    echo "  Virtual environment already exists"
fi

# Activate virtual environment
echo ""
echo "✓ Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo ""
echo "✓ Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories
echo ""
echo "✓ Creating directories..."
mkdir -p data
mkdir -p temp
mkdir -p logs

# Initialize database
echo ""
echo "✓ Initializing database..."
python3 << EOF
from src.database import init_db
init_db()
print("  Database initialized successfully")
EOF

# Create .env file template
echo ""
echo "✓ Creating environment file template..."
if [ ! -f ".env" ]; then
    cat > .env << EOF
# Red Marker Pro - Environment Configuration
GEMINI_API_KEY=your-api-key-here
ENVIRONMENT=development
LOG_LEVEL=INFO
EOF
    echo "  .env file created - please add your GEMINI_API_KEY"
else
    echo "  .env file already exists"
fi

echo ""
echo "=================================="
echo "✅ Setup Complete!"
echo ""
echo "Next steps:"
echo "1. Add your GEMINI_API_KEY to .env file"
echo "2. Run: python run.py"
echo "3. Open: http://localhost:5000"
echo ""
echo "For more information, see README_PRO.md"
