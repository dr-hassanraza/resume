#!/bin/bash

# Quick Start Script - Minimal Dependencies
echo "🚀 Quick Start: Resume Optimizer Chatbot (Demo Mode)"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8+ first."
    echo "📥 Download from: https://python.org/downloads/"
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18+ first."
    echo "📥 Download from: https://nodejs.org/en/download/"
    exit 1
fi

echo "✅ Python and Node.js are installed"
echo ""

# Create frontend .env if needed
if [ ! -f frontend/.env ]; then
    echo "📝 Creating frontend environment file..."
    cat > frontend/.env << EOF
REACT_APP_API_URL=http://localhost:8080
REACT_APP_WS_URL=ws://localhost:8080
REACT_APP_ENV=development
EOF
fi

# Install minimal Python dependencies
echo "📦 Installing minimal Python dependencies..."
cd backend
python3 -m pip install fastapi uvicorn websockets python-multipart

# Start backend (simple version)
echo "▶️  Starting FastAPI backend (demo mode) on port 8080..."
python3 simple_main.py &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

# Start frontend
cd ../frontend
echo "📦 Installing frontend dependencies (this may take a moment)..."
npm install --silent

echo "▶️  Starting React frontend on port 3001..."
PORT=3001 npm start &
FRONTEND_PID=$!

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping servers..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo "👋 Goodbye!"
    exit
}

# Trap cleanup function on script exit
trap cleanup EXIT INT TERM

# Wait for services to start
echo ""
echo "⏳ Starting services..."
sleep 5

# Check if services are running
if ps -p $BACKEND_PID > /dev/null; then
    echo "✅ Backend is running"
else
    echo "❌ Backend failed to start"
fi

if ps -p $FRONTEND_PID > /dev/null; then
    echo "✅ Frontend is starting"
else
    echo "❌ Frontend failed to start"
fi

echo ""
echo "🎉 Application Started!"
echo ""
echo "📱 Access URLs:"
echo "   🌐 Main App: http://localhost:3001"
echo "   🔌 API: http://localhost:8080"
echo "   📚 API Docs: http://localhost:8080/docs"
echo ""
echo "💡 Demo Features:"
echo "   • User registration/login (demo mode)"
echo "   • Chat interface with AI responses"
echo "   • Resume upload simulation"
echo "   • Analytics dashboard"
echo ""
echo "⚠️  Note: This is DEMO MODE - no real AI processing"
echo "   Add your AI API keys to enable full functionality"
echo ""
echo "Press Ctrl+C to stop all servers"
echo ""

# Wait for background processes
wait