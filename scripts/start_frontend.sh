#!/bin/bash

# Start Frontend Server Script
# Agentic Ethical Hacker - Vulnerability Analysis Tool

set -e

echo "🎨 Starting Agentic Ethical Hacker Frontend..."

# Check if we're in the right directory
if [ ! -f "frontend/package.json" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

# Change to frontend directory
cd frontend

# Check if Node.js is available
if ! command -v node &> /dev/null; then
    echo "❌ Error: Node.js is required but not installed"
    echo "Please install Node.js 18+ from https://nodejs.org/"
    exit 1
fi

# Check Node.js version
NODE_VERSION=$(node --version | cut -d'v' -f2)
REQUIRED_VERSION="18.0.0"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$NODE_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ Error: Node.js 18 or higher is required. Found: v$NODE_VERSION"
    echo "Please update Node.js from https://nodejs.org/"
    exit 1
fi

echo "✅ Node.js version check passed: v$NODE_VERSION"

# Check if npm is available
if ! command -v npm &> /dev/null; then
    echo "❌ Error: npm is required but not available"
    exit 1
fi

# Install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
else
    echo "📦 Dependencies already installed, checking for updates..."
    npm audit fix --only=prod || true
fi

# Build the application for production (optional)
# echo "🏗️  Building application..."
# npm run build

echo "🌟 Starting Next.js development server..."
echo "🎨 Frontend will be available at: http://localhost:3000"
echo "🔄 Hot reload is enabled for development"
echo ""
echo "Make sure the backend is running on http://localhost:8000"
echo "Press Ctrl+C to stop the server"

# Start the development server
npm run dev

echo "👋 Frontend server stopped"