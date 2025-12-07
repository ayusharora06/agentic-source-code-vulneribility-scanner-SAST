#!/bin/bash

# Quick Start Script
# Agentic Ethical Hacker - Vulnerability Analysis Tool

set -e

echo "🛡️  Agentic Ethical Hacker - Quick Start"
echo "======================================="
echo ""

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if a port is in use
port_in_use() {
    lsof -ti:$1 >/dev/null 2>&1
}

echo "🔍 Checking system requirements..."

# Check Python
if ! command_exists python3; then
    echo "❌ Python 3 is not installed"
    echo "Please install Python 3.8+ from https://python.org/"
    exit 1
fi

# Check Node.js
if ! command_exists node; then
    echo "❌ Node.js is not installed"
    echo "Please install Node.js 18+ from https://nodejs.org/"
    exit 1
fi

# Check npm
if ! command_exists npm; then
    echo "❌ npm is not available"
    echo "Please install Node.js which includes npm"
    exit 1
fi

echo "✅ All requirements are satisfied"

# Check if ports are available
if port_in_use 8000; then
    echo "⚠️  Port 8000 is already in use (backend)"
    echo "Please stop the service using port 8000 or use a different port"
    exit 1
fi

if port_in_use 3000; then
    echo "⚠️  Port 3000 is already in use (frontend)"
    echo "Please stop the service using port 3000 or use a different port"
    exit 1
fi

echo "✅ Ports 3000 and 8000 are available"

# Make scripts executable
chmod +x scripts/*.sh

echo ""
echo "🚀 Starting services..."
echo ""

# Function to cleanup background processes
cleanup() {
    echo ""
    echo "🛑 Shutting down services..."
    
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
        echo "✅ Backend stopped"
    fi
    
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
        echo "✅ Frontend stopped"
    fi
    
    echo "👋 Quick start stopped"
    exit 0
}

# Set up cleanup trap
trap cleanup SIGINT SIGTERM

# Start backend in background
echo "🔧 Starting backend server..."
./scripts/start_backend.sh > backend.log 2>&1 &
BACKEND_PID=$!

# Wait for backend to start
echo "⏳ Waiting for backend to initialize..."
sleep 10

# Check if backend is still running
if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo "❌ Backend failed to start. Check backend.log for details:"
    tail -n 20 backend.log
    exit 1
fi

# Start frontend in background  
echo "🎨 Starting frontend server..."
./scripts/start_frontend.sh > frontend.log 2>&1 &
FRONTEND_PID=$!

# Wait for frontend to start
echo "⏳ Waiting for frontend to initialize..."
sleep 15

# Check if frontend is still running
if ! kill -0 $FRONTEND_PID 2>/dev/null; then
    echo "❌ Frontend failed to start. Check frontend.log for details:"
    tail -n 20 frontend.log
    cleanup
    exit 1
fi

echo ""
echo "🎉 Agentic Ethical Hacker is now running!"
echo ""
echo "📊 Dashboard: http://localhost:3000"
echo "🔧 Backend API: http://localhost:8000"
echo "📖 API Docs: http://localhost:8000/docs"
echo ""
echo "📝 Logs:"
echo "   Backend: ./backend.log"
echo "   Frontend: ./frontend.log"
echo ""
echo "🔍 Quick Test:"
echo "   1. Open http://localhost:3000 in your browser"
echo "   2. Try uploading a source code file for analysis"
echo "   3. Watch real-time vulnerability detection"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for user interrupt
while true; do
    sleep 1
    
    # Check if processes are still running
    if ! kill -0 $BACKEND_PID 2>/dev/null; then
        echo "❌ Backend process died unexpectedly"
        cleanup
        exit 1
    fi
    
    if ! kill -0 $FRONTEND_PID 2>/dev/null; then
        echo "❌ Frontend process died unexpectedly" 
        cleanup
        exit 1
    fi
done