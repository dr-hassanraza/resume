#!/bin/bash

# Simple startup script without Docker
# This runs the frontend and backend directly on your system

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "package.json" ] && [ ! -d "frontend" ]; then
    print_error "Please run this script from the project root directory"
    exit 1
fi

print_status "🚀 Starting AI-Powered Resume Optimizer (Simple Mode)"
print_warning "Note: This runs without Docker - some enterprise features may not work without a database"

# Create .env if it doesn't exist
if [ ! -f .env ]; then
    print_status "Creating .env file from template..."
    cp .env.example .env
    print_warning "Please edit .env file with your API keys!"
fi

# Create necessary directories
mkdir -p backend/uploads
mkdir -p logs

# Start backend in background
print_status "Starting backend server..."
cd backend

# Check if virtual environment exists, create if not
if [ ! -d "venv" ]; then
    print_status "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install backend dependencies
if [ ! -f "venv/installed.flag" ]; then
    print_status "Installing backend dependencies..."
    pip install --upgrade pip
    pip install fastapi uvicorn python-multipart websockets python-dotenv pydantic aiofiles
    pip install openai anthropic httpx requests aiohttp
    pip install python-jose passlib bcrypt python-dateutil
    pip install python-docx pypdf2
    touch venv/installed.flag
fi

# Start backend server
print_status "Starting FastAPI backend on port 8000..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

cd ..

# Wait a bit for backend to start
sleep 3

# Start frontend
print_status "Starting frontend server..."
cd frontend

# Install frontend dependencies
if [ ! -d "node_modules" ]; then
    print_status "Installing frontend dependencies..."
    npm install
fi

# Create environment file for frontend
cat > .env.local << EOF
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
EOF

print_status "Starting React frontend on port 3000..."
npm start &
FRONTEND_PID=$!

cd ..

# Wait for services to start
print_status "Waiting for services to start..."
sleep 5

# Check if services are running
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    print_success "✅ Backend is running!"
else
    print_warning "⚠️  Backend might still be starting..."
fi

if curl -s http://localhost:3000 > /dev/null 2>&1; then
    print_success "✅ Frontend is running!"
else
    print_warning "⚠️  Frontend might still be starting..."
fi

print_success "🎉 Application is starting up!"
echo
echo "======================================================="
echo "📱 APPLICATION URLS:"
echo "======================================================="
echo "🌐 Web Application:  http://localhost:3000"
echo "🔧 Backend API:      http://localhost:8000"
echo "📊 API Documentation: http://localhost:8000/docs"
echo
echo "======================================================="
echo "⚠️  IMPORTANT NOTES:"
echo "======================================================="
echo "🔑 Add your API keys to the .env file:"
echo "   - OPENAI_API_KEY (required)"
echo "   - ANTHROPIC_API_KEY (required)"
echo
echo "🗄️  Database: Some features won't work without a database"
echo "   - For full functionality, install Docker and use ./start-local.sh"
echo
echo "⛔ To stop the application:"
echo "   - Press Ctrl+C, then run: kill $BACKEND_PID $FRONTEND_PID"
echo
print_success "Visit http://localhost:3000 to start using the application!"

# Keep script running and handle cleanup
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM

# Open browser (optional)
sleep 2
if command -v open >/dev/null 2>&1; then
    print_status "Opening web browser..."
    open http://localhost:3000
elif command -v xdg-open >/dev/null 2>&1; then
    print_status "Opening web browser..."
    xdg-open http://localhost:3000
fi

# Wait for processes
wait