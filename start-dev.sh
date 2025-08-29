#!/bin/bash

# AI-Powered Resume Optimizer - Development Setup Script
# This script sets up the development environment with hot reloading

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
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

print_dev() {
    echo -e "${PURPLE}[DEV]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to get local IP address
get_local_ip() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        LOCAL_IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -1)
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        LOCAL_IP=$(hostname -I | awk '{print $1}')
    else
        # Fallback
        LOCAL_IP="192.168.1.100"
        print_warning "Could not detect local IP. Using fallback: $LOCAL_IP"
    fi
    echo $LOCAL_IP
}

# ASCII Art Banner
echo -e "${PURPLE}"
cat << "EOF"
    ____                                   ____        __  _           _              
   / __ \___  _______  ______ ___  ___   / __ \____  / /_(_)___ ___  (_)___  ___  ____
  / /_/ / _ \/ ___/ / / / __ `__ \/ _ \ / / / / __ \/ __/ / __ `__ \/ /_  / / _ \/ __/
 / _, _/  __(__  ) /_/ / / / / / /  __// /_/ / /_/ / /_/ / / / / / / / / /_/  __/ /   
/_/ |_|\___/____/\__,_/_/ /_/ /_/\___/ \____/ .___/\__/_/_/ /_/ /_/_/ /___/\___/_/    
                                          /_/                                        
                    DEVELOPMENT MODE 🚀
EOF
echo -e "${NC}"

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
        DOCKER_COMPOSE_CMD="docker compose"
    fi
else
    DOCKER_COMPOSE_CMD="docker-compose"
fi

print_success "Prerequisites check passed!"

# Get local IP for mobile development
LOCAL_IP=$(get_local_ip)
print_dev "Detected local IP: $LOCAL_IP"

# Check if .env file exists
if [ ! -f .env ]; then
    print_warning ".env file not found. Creating from .env.example..."
    if [ -f .env.example ]; then
        cp .env.example .env
        print_warning "Please edit .env file with your actual API keys."
        print_warning "Essential: OPENAI_API_KEY, ANTHROPIC_API_KEY"
    else
        print_error ".env.example file not found. Cannot create .env file."
        exit 1
    fi
fi

# Create necessary directories
print_status "Creating development directories..."
mkdir -p backend/uploads
mkdir -p logs
mkdir -p frontend/.next
mkdir -p mobile/node_modules

# Update mobile docker compose with local IP
print_dev "Configuring mobile development with IP: $LOCAL_IP"
sed -i.bak "s/REACT_NATIVE_PACKAGER_HOSTNAME=.*/REACT_NATIVE_PACKAGER_HOSTNAME=$LOCAL_IP/" docker-compose.dev.yml

# Stop any existing containers
print_status "Stopping any existing containers..."
$DOCKER_COMPOSE_CMD -f docker-compose.yml down --remove-orphans 2>/dev/null || true
$DOCKER_COMPOSE_CMD -f docker-compose.dev.yml down --remove-orphans 2>/dev/null || true

# Build and start development services
print_dev "Building and starting development services..."
print_dev "This includes: Frontend, Backend, Database, Redis, pgAdmin, Redis Commander"

$DOCKER_COMPOSE_CMD -f docker-compose.dev.yml build --no-cache
$DOCKER_COMPOSE_CMD -f docker-compose.dev.yml up -d

# Wait for services
print_status "Waiting for services to start..."
sleep 15

# Check service health
print_dev "Checking service health..."

services=("postgres:5432:Database" "redis:6379:Redis" "backend-dev:8000:Backend" "frontend-dev:3000:Frontend")

for service_info in "${services[@]}"; do
    IFS=':' read -r service port name <<< "$service_info"
    
    if nc -z localhost $port 2>/dev/null; then
        print_success "$name is ready!"
    else
        print_warning "$name is not responding on port $port (this might be normal during startup)"
    fi
done

# Display development information
print_success "🚀 Development environment is starting up!"
echo
echo "======================================================="
echo "📱 DEVELOPMENT URLS:"
echo "======================================================="
echo "🌐 Frontend (Next.js):     http://localhost:3000"
echo "🔧 Backend API:            http://localhost:8000"
echo "📊 API Documentation:      http://localhost:8000/docs"
echo "🗄️  pgAdmin (DB Admin):     http://localhost:5050"
echo "⚡ Redis Commander:        http://localhost:8081"
echo "📱 Mobile Expo DevTools:   http://localhost:19000"
echo "🌍 Mobile Web Preview:     http://localhost:19006"
echo

echo "======================================================="
echo "🔑 DEVELOPMENT CREDENTIALS:"
echo "======================================================="
echo "📧 Demo User: demo@example.com / password123"
echo "👤 Admin:     admin@resumeoptimizer.com / password123"
echo "🗄️  pgAdmin:   admin@resumeoptimizer.com / admin123"
echo "⚡ Redis:     admin / admin123"
echo

echo "======================================================="
echo "📱 MOBILE DEVELOPMENT:"
echo "======================================================="
echo "📋 Your local IP: $LOCAL_IP"
echo "📱 Expo DevTools: http://localhost:19000"
echo "🔗 To test on device:"
echo "   1. Install Expo Go app on your phone"
echo "   2. Scan QR code from http://localhost:19000"
echo "   3. Or connect to: http://$LOCAL_IP:19000"
echo

echo "======================================================="
echo "🛠️  DEVELOPMENT COMMANDS:"
echo "======================================================="
echo "📋 View logs:           $DOCKER_COMPOSE_CMD -f docker-compose.dev.yml logs -f"
echo "🔄 Restart service:     $DOCKER_COMPOSE_CMD -f docker-compose.dev.yml restart [service]"
echo "🏗️  Rebuild service:    $DOCKER_COMPOSE_CMD -f docker-compose.dev.yml build [service] --no-cache"
echo "⛔ Stop development:    $DOCKER_COMPOSE_CMD -f docker-compose.dev.yml down"
echo "🧹 Clean volumes:       $DOCKER_COMPOSE_CMD -f docker-compose.dev.yml down -v"
echo

echo "======================================================="
echo "🔧 HOT RELOADING ENABLED:"
echo "======================================================="
echo "✅ Backend: Auto-reloads on Python file changes"
echo "✅ Frontend: Auto-reloads on React/TypeScript changes"
echo "✅ Mobile: Metro bundler with fast refresh"
echo "✅ Database: pgAdmin for easy management"
echo "✅ Cache: Redis Commander for debugging"
echo

echo "======================================================="
echo "📚 DEVELOPMENT TIPS:"
echo "======================================================="
echo "🐛 Debug Backend:  Check logs with 'docker-compose -f docker-compose.dev.yml logs -f backend-dev'"
echo "🎨 Frontend Debug: Open browser DevTools at http://localhost:3000"
echo "📱 Mobile Debug:   Use React DevTools and Expo DevTools"
echo "🗄️  Database:       Use pgAdmin at http://localhost:5050 for DB management"
echo "⚡ Redis:          Use Redis Commander at http://localhost:8081 for cache inspection"
echo

print_success "Development environment setup complete! 🎉"
print_dev "All services have hot reloading enabled for rapid development"

# Show real-time logs
echo
read -p "Would you like to view real-time development logs? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_dev "Showing real-time development logs (Press Ctrl+C to stop)..."
    $DOCKER_COMPOSE_CMD -f docker-compose.dev.yml logs -f
fi