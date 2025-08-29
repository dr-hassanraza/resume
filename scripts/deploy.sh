#!/bin/bash

# Production Deployment Script
echo "🚀 Deploying Resume Optimizer Chatbot to Production..."

# Build production images
echo "🏗️  Building production images..."
docker-compose -f docker-compose.yml -f docker-compose.prod.yml build

# Pull latest images
echo "📥 Pulling latest base images..."
docker-compose pull

# Stop existing services
echo "⏹️  Stopping existing services..."
docker-compose down

# Start services with production profile
echo "▶️  Starting production services..."
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Wait for services
echo "⏳ Waiting for services to start..."
sleep 60

# Run database migrations
echo "🗄️  Running database migrations..."
docker-compose exec backend alembic upgrade head

# Health checks
echo "🏥 Running health checks..."
for i in {1..30}; do
    if curl -f http://localhost/api/health >/dev/null 2>&1; then
        echo "✅ Application is healthy"
        break
    fi
    echo "⏳ Waiting for application... ($i/30)"
    sleep 2
done

echo "🎉 Deployment complete!"
echo "🌐 Application is available at: http://your-domain.com"