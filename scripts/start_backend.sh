#!/bin/bash

# Start Backend Server Script
# Agentic Ethical Hacker - Vulnerability Analysis Tool

set -e

echo "🚀 Starting Agentic Ethical Hacker Backend..."

# Check if we're in the right directory
if [ ! -f "backend/requirements.txt" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

# Change to backend directory
cd backend

# Check if Python 3.8+ is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is required but not installed"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.8"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ Error: Python 3.8 or higher is required. Found: $PYTHON_VERSION"
    exit 1
fi

echo "✅ Python version check passed: $PYTHON_VERSION"

# Check if virtual environment exists, create if not
if [ ! -d "venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install/upgrade dependencies
echo "📦 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Set environment variables if .env file exists
if [ -f ".env" ]; then
    echo "🔧 Loading environment variables from .env"
    export $(cat .env | xargs)
fi

# Create logs directory
mkdir -p logs

# Check if database directory exists
mkdir -p database

echo "🏗️  Initializing database..."

# Run database initialization (if needed)
# python3 -c "import asyncio; from src.database.models import Database; asyncio.run(Database().initialize())"

echo "🌟 Starting FastAPI server..."
echo "📊 Dashboard will be available at: http://localhost:8000"
echo "📡 WebSocket endpoint: ws://localhost:8000/ws/dashboard"
echo "🔧 API documentation: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"

# Start the server
python3 -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

echo "👋 Backend server stopped"