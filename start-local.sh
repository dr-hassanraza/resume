#!/bin/bash

# AI-Powered Resume Optimizer - Local Setup Script
# This script sets up and starts the entire application locally

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
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

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to wait for service to be ready
wait_for_service() {
    local host=$1
    local port=$2
    local service_name=$3
    local max_attempts=30
    local attempt=1

    print_status "Waiting for $service_name to be ready..."
    
    while [ $attempt -le $max_attempts ]; do
        if nc -z $host $port 2>/dev/null; then
            print_success "$service_name is ready!"
            return 0
        fi
        
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    print_error "$service_name failed to start within expected time"
    return 1
}

# Check prerequisites
print_status "Checking prerequisites..."

if ! command_exists docker; then
    print_error "Docker is not installed. Please install Docker and try again."
    echo "Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! command_exists docker-compose; then
    if ! command_exists docker compose; then
        print_error "Docker Compose is not installed. Please install Docker Compose and try again."
        echo "Visit: https://docs.docker.com/compose/install/"
        exit 1
    else
        # Use 'docker compose' instead of 'docker-compose'
        DOCKER_COMPOSE_CMD="docker compose"
    fi
else
    DOCKER_COMPOSE_CMD="docker-compose"
fi

print_success "Prerequisites check passed!"

# Check if .env file exists
if [ ! -f .env ]; then
    print_warning ".env file not found. Creating from .env.example..."
    if [ -f .env.example ]; then
        cp .env.example .env
        print_warning "Please edit .env file with your actual API keys before proceeding."
        print_warning "Required: OPENAI_API_KEY, ANTHROPIC_API_KEY (others are optional)"
        
        # Ask user if they want to continue
        read -p "Do you want to continue with default values? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_status "Please edit .env file and run this script again."
            exit 1
        fi
    else
        print_error ".env.example file not found. Cannot create .env file."
        exit 1
    fi
fi

# Create necessary directories
print_status "Creating necessary directories..."
mkdir -p backend/uploads
mkdir -p logs
mkdir -p nginx/ssl

# Stop any existing containers
print_status "Stopping any existing containers..."
$DOCKER_COMPOSE_CMD down --remove-orphans

# Pull latest images and build
print_status "Building and starting services..."
$DOCKER_COMPOSE_CMD build --no-cache
$DOCKER_COMPOSE_CMD up -d

# Wait for services to be ready
print_status "Waiting for services to start..."
sleep 10

# Check database
if wait_for_service localhost 5432 "PostgreSQL"; then
    print_success "Database is ready!"
else
    print_error "Failed to connect to database"
    $DOCKER_COMPOSE_CMD logs postgres
    exit 1
fi

# Check Redis
if wait_for_service localhost 6379 "Redis"; then
    print_success "Redis is ready!"
else
    print_error "Failed to connect to Redis"
    $DOCKER_COMPOSE_CMD logs redis
    exit 1
fi

# Check Backend
if wait_for_service localhost 8000 "Backend API"; then
    print_success "Backend API is ready!"
else
    print_error "Failed to start Backend API"
    $DOCKER_COMPOSE_CMD logs backend
    exit 1
fi

# Check Frontend
if wait_for_service localhost 3000 "Frontend"; then
    print_success "Frontend is ready!"
else
    print_error "Failed to start Frontend"
    $DOCKER_COMPOSE_CMD logs frontend
    exit 1
fi

# Display status
print_success "🚀 AI-Powered Resume Optimizer is now running!"
echo
echo "======================================================"
echo "📱 APPLICATION URLS:"
echo "======================================================"
echo "🌐 Frontend (Web App):     http://localhost:3000"
echo "🔧 Backend API:            http://localhost:8000"
echo "📊 API Documentation:      http://localhost:8000/docs"
echo "💾 Database (PostgreSQL):  localhost:5432"
echo "⚡ Redis Cache:            localhost:6379"
echo
echo "======================================================"
echo "🔑 DEFAULT CREDENTIALS (Development Only):"
echo "======================================================"
echo "📧 Demo User: demo@example.com"
echo "🔑 Password:  password123"
echo "👤 Admin:     admin@resumeoptimizer.com"
echo "🔑 Password:  password123"
echo
echo "======================================================"
echo "🛠️  USEFUL COMMANDS:"
echo "======================================================"
echo "📋 View logs:        $DOCKER_COMPOSE_CMD logs -f [service_name]"
echo "🔄 Restart service:  $DOCKER_COMPOSE_CMD restart [service_name]"
echo "⛔ Stop all:         $DOCKER_COMPOSE_CMD down"
echo "🧹 Clean up:         $DOCKER_COMPOSE_CMD down -v --remove-orphans"
echo
echo "======================================================"
echo "📚 NEXT STEPS:"
echo "======================================================"
echo "1. 🔐 Add your API keys to the .env file:"
echo "   - OPENAI_API_KEY (required for GPT models)"
echo "   - ANTHROPIC_API_KEY (required for Claude models)"
echo "   - QWEN_API_KEY (optional for Qwen models)"
echo
echo "2. 💳 Configure payment processing (optional):"
echo "   - STRIPE_SECRET_KEY"
echo "   - NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY"
echo
echo "3. 📧 Setup email notifications (optional):"
echo "   - SENDGRID_API_KEY"
echo
echo "4. 🎯 Test the application:"
echo "   - Upload a resume at http://localhost:3000"
echo "   - Try the AI chat interface"
echo "   - Explore the dashboard and analytics"
echo
print_success "Setup completed! Happy coding! 🎉"

# Show real-time logs
echo
read -p "Would you like to view real-time logs? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_status "Showing real-time logs (Press Ctrl+C to stop)..."
    $DOCKER_COMPOSE_CMD logs -f
fi