#!/bin/bash

# Resume Optimizer Chatbot Setup Script
echo "🚀 Setting up Resume Optimizer Chatbot..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p backend/uploads
mkdir -p logs
mkdir -p ssl

# Copy environment files if they don't exist
if [ ! -f backend/.env ]; then
    echo "📝 Creating backend environment file..."
    cp backend/.env.example backend/.env
    echo "⚠️  Please update backend/.env with your API keys and configuration"
fi

if [ ! -f frontend/.env ]; then
    echo "📝 Creating frontend environment file..."
    cp frontend/.env.example frontend/.env
    echo "⚠️  Please update frontend/.env if needed"
fi

# Set permissions
echo "🔐 Setting permissions..."
chmod +x setup.sh
chmod +x scripts/*.sh 2>/dev/null || true

# Build and start services
echo "🏗️  Building and starting services..."
docker-compose up -d --build

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 30

# Check service health
echo "🏥 Checking service health..."
if curl -f http://localhost:8080/health >/dev/null 2>&1; then
    echo "✅ Backend API is healthy"
else
    echo "❌ Backend API is not responding"
fi

if curl -f http://localhost:3001 >/dev/null 2>&1; then
    echo "✅ Frontend is healthy"
else
    echo "❌ Frontend is not responding"
fi

# Display access information
echo ""
echo "🎉 Setup complete!"
echo ""
echo "📱 Access your application:"
echo "   Frontend: http://localhost:3001"
echo "   Backend API: http://localhost:8080"
echo "   API Docs: http://localhost:8080/docs"
echo ""
echo "🔧 Default credentials:"
echo "   Create a new account at http://localhost:3001/register"
echo ""
echo "📚 Next steps:"
echo "   1. Update your API keys in backend/.env"
echo "   2. Restart the backend: docker-compose restart backend"
echo "   3. Register a new account"
echo "   4. Start optimizing resumes!"
echo ""
echo "📖 For more information, check the README.md file"