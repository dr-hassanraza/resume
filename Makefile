# AI-Powered Resume Optimizer - Makefile
# Convenient commands for development and deployment

# Colors
RED=\033[0;31m
GREEN=\033[0;32m
YELLOW=\033[1;33m
BLUE=\033[0;34m
NC=\033[0m # No Color

# Docker Compose commands
DOCKER_COMPOSE = docker-compose
DOCKER_COMPOSE_DEV = docker-compose -f docker-compose.dev.yml

.PHONY: help install start stop restart logs clean dev prod test lint format backup restore

# Default target
help: ## Show this help message
	@echo "$(BLUE)AI-Powered Resume Optimizer - Development Commands$(NC)"
	@echo ""
	@echo "$(YELLOW)Available commands:$(NC)"
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z_-]+:.*?##/ { printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2 }' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(YELLOW)Examples:$(NC)"
	@echo "  make dev          # Start development environment"
	@echo "  make prod         # Start production environment"
	@echo "  make logs         # View all logs"
	@echo "  make clean        # Clean up everything"

install: ## Install and set up the project
	@echo "$(BLUE)Setting up AI-Powered Resume Optimizer...$(NC)"
	@chmod +x start-local.sh start-dev.sh
	@if [ ! -f .env ]; then cp .env.example .env; echo "$(YELLOW)Created .env file - please add your API keys$(NC)"; fi
	@mkdir -p backend/uploads logs frontend/.next mobile/node_modules
	@echo "$(GREEN)Setup complete! Edit .env file and run 'make dev' or 'make prod'$(NC)"

start: prod ## Alias for prod (start production)

prod: ## Start production environment
	@echo "$(BLUE)Starting production environment...$(NC)"
	@./start-local.sh

dev: ## Start development environment with hot reloading
	@echo "$(BLUE)Starting development environment...$(NC)"
	@./start-dev.sh

stop: ## Stop all services
	@echo "$(YELLOW)Stopping all services...$(NC)"
	@$(DOCKER_COMPOSE) down 2>/dev/null || true
	@$(DOCKER_COMPOSE_DEV) down 2>/dev/null || true
	@echo "$(GREEN)All services stopped$(NC)"

restart: stop ## Restart all services
	@echo "$(BLUE)Restarting services...$(NC)"
	@make start

restart-dev: ## Restart development services
	@echo "$(BLUE)Restarting development services...$(NC)"
	@$(DOCKER_COMPOSE_DEV) restart
	@echo "$(GREEN)Development services restarted$(NC)"

logs: ## View logs from all services
	@echo "$(BLUE)Viewing logs (Press Ctrl+C to stop)...$(NC)"
	@$(DOCKER_COMPOSE) logs -f 2>/dev/null || $(DOCKER_COMPOSE_DEV) logs -f 2>/dev/null || echo "$(RED)No services running$(NC)"

logs-backend: ## View backend logs only
	@$(DOCKER_COMPOSE) logs -f backend 2>/dev/null || $(DOCKER_COMPOSE_DEV) logs -f backend-dev 2>/dev/null || echo "$(RED)Backend not running$(NC)"

logs-frontend: ## View frontend logs only
	@$(DOCKER_COMPOSE) logs -f frontend 2>/dev/null || $(DOCKER_COMPOSE_DEV) logs -f frontend-dev 2>/dev/null || echo "$(RED)Frontend not running$(NC)"

logs-db: ## View database logs only
	@$(DOCKER_COMPOSE) logs -f postgres 2>/dev/null || $(DOCKER_COMPOSE_DEV) logs -f postgres 2>/dev/null || echo "$(RED)Database not running$(NC)"

status: ## Show status of all services
	@echo "$(BLUE)Service Status:$(NC)"
	@$(DOCKER_COMPOSE) ps 2>/dev/null || echo "$(YELLOW)Production services not running$(NC)"
	@$(DOCKER_COMPOSE_DEV) ps 2>/dev/null || echo "$(YELLOW)Development services not running$(NC)"

clean: ## Clean up Docker containers, volumes, and networks
	@echo "$(YELLOW)Cleaning up Docker resources...$(NC)"
	@$(DOCKER_COMPOSE) down -v --remove-orphans 2>/dev/null || true
	@$(DOCKER_COMPOSE_DEV) down -v --remove-orphans 2>/dev/null || true
	@docker system prune -f
	@echo "$(GREEN)Cleanup complete$(NC)"

clean-all: clean ## Clean up everything including images
	@echo "$(YELLOW)Cleaning up all Docker resources including images...$(NC)"
	@docker system prune -af --volumes
	@echo "$(GREEN)Complete cleanup done$(NC)"

build: ## Build all Docker images
	@echo "$(BLUE)Building all Docker images...$(NC)"
	@$(DOCKER_COMPOSE) build --no-cache
	@echo "$(GREEN)Build complete$(NC)"

build-dev: ## Build development Docker images
	@echo "$(BLUE)Building development Docker images...$(NC)"
	@$(DOCKER_COMPOSE_DEV) build --no-cache
	@echo "$(GREEN)Development build complete$(NC)"

# Database commands
db-connect: ## Connect to PostgreSQL database
	@echo "$(BLUE)Connecting to database...$(NC)"
	@$(DOCKER_COMPOSE) exec postgres psql -U postgres -d resume_optimizer 2>/dev/null || $(DOCKER_COMPOSE_DEV) exec postgres psql -U postgres -d resume_optimizer 2>/dev/null

db-backup: ## Backup database to file
	@echo "$(BLUE)Creating database backup...$(NC)"
	@$(DOCKER_COMPOSE) exec postgres pg_dump -U postgres resume_optimizer > backup_$(shell date +%Y%m%d_%H%M%S).sql 2>/dev/null || $(DOCKER_COMPOSE_DEV) exec postgres pg_dump -U postgres resume_optimizer > backup_$(shell date +%Y%m%d_%H%M%S).sql 2>/dev/null
	@echo "$(GREEN)Database backup created$(NC)"

db-restore: ## Restore database from backup (usage: make db-restore FILE=backup.sql)
	@if [ -z "$(FILE)" ]; then echo "$(RED)Usage: make db-restore FILE=backup.sql$(NC)"; exit 1; fi
	@echo "$(BLUE)Restoring database from $(FILE)...$(NC)"
	@$(DOCKER_COMPOSE) exec -T postgres psql -U postgres resume_optimizer < $(FILE) 2>/dev/null || $(DOCKER_COMPOSE_DEV) exec -T postgres psql -U postgres resume_optimizer < $(FILE) 2>/dev/null
	@echo "$(GREEN)Database restored$(NC)"

# Redis commands
redis-connect: ## Connect to Redis
	@echo "$(BLUE)Connecting to Redis...$(NC)"
	@$(DOCKER_COMPOSE) exec redis redis-cli -a redis123 2>/dev/null || $(DOCKER_COMPOSE_DEV) exec redis redis-cli -a redis123 2>/dev/null

redis-flush: ## Clear Redis cache
	@echo "$(YELLOW)Clearing Redis cache...$(NC)"
	@$(DOCKER_COMPOSE) exec redis redis-cli -a redis123 FLUSHALL 2>/dev/null || $(DOCKER_COMPOSE_DEV) exec redis redis-cli -a redis123 FLUSHALL 2>/dev/null
	@echo "$(GREEN)Redis cache cleared$(NC)"

# Development commands
shell-backend: ## Open shell in backend container
	@$(DOCKER_COMPOSE) exec backend bash 2>/dev/null || $(DOCKER_COMPOSE_DEV) exec backend-dev bash 2>/dev/null

shell-frontend: ## Open shell in frontend container
	@$(DOCKER_COMPOSE) exec frontend sh 2>/dev/null || $(DOCKER_COMPOSE_DEV) exec frontend-dev sh 2>/dev/null

# Testing commands
test: ## Run tests
	@echo "$(BLUE)Running tests...$(NC)"
	@echo "$(YELLOW)Backend tests:$(NC)"
	@$(DOCKER_COMPOSE_DEV) exec backend-dev pytest tests/ -v || true
	@echo "$(YELLOW)Frontend tests:$(NC)"
	@$(DOCKER_COMPOSE_DEV) exec frontend-dev npm test || true

test-backend: ## Run backend tests only
	@echo "$(BLUE)Running backend tests...$(NC)"
	@$(DOCKER_COMPOSE_DEV) exec backend-dev pytest tests/ -v

test-frontend: ## Run frontend tests only
	@echo "$(BLUE)Running frontend tests...$(NC)"
	@$(DOCKER_COMPOSE_DEV) exec frontend-dev npm test

# Code quality commands
lint: ## Run linting
	@echo "$(BLUE)Running linting...$(NC)"
	@echo "$(YELLOW)Backend linting:$(NC)"
	@$(DOCKER_COMPOSE_DEV) exec backend-dev flake8 app/ || true
	@echo "$(YELLOW)Frontend linting:$(NC)"
	@$(DOCKER_COMPOSE_DEV) exec frontend-dev npm run lint || true

format: ## Format code
	@echo "$(BLUE)Formatting code...$(NC)"
	@echo "$(YELLOW)Backend formatting:$(NC)"
	@$(DOCKER_COMPOSE_DEV) exec backend-dev black app/ || true
	@echo "$(YELLOW)Frontend formatting:$(NC)"
	@$(DOCKER_COMPOSE_DEV) exec frontend-dev npm run format || true

# Health checks
health: ## Check health of all services
	@echo "$(BLUE)Health Check Results:$(NC)"
	@echo -n "Frontend:  "; curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 2>/dev/null && echo "$(GREEN)✓ Running$(NC)" || echo "$(RED)✗ Down$(NC)"
	@echo -n "Backend:   "; curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health 2>/dev/null && echo "$(GREEN)✓ Running$(NC)" || echo "$(RED)✗ Down$(NC)"
	@echo -n "Database:  "; nc -z localhost 5432 2>/dev/null && echo "$(GREEN)✓ Running$(NC)" || echo "$(RED)✗ Down$(NC)"
	@echo -n "Redis:     "; nc -z localhost 6379 2>/dev/null && echo "$(GREEN)✓ Running$(NC)" || echo "$(RED)✗ Down$(NC)"

# Documentation
docs: ## Open API documentation
	@echo "$(BLUE)Opening API documentation...$(NC)"
	@open http://localhost:8000/docs 2>/dev/null || echo "Visit: http://localhost:8000/docs"

app: ## Open web application
	@echo "$(BLUE)Opening web application...$(NC)"
	@open http://localhost:3000 2>/dev/null || echo "Visit: http://localhost:3000"

# Mobile development
mobile: ## Start mobile development server
	@echo "$(BLUE)Starting mobile development...$(NC)"
	@$(DOCKER_COMPOSE_DEV) up -d mobile-dev
	@echo "$(GREEN)Mobile development server started$(NC)"
	@echo "Visit: http://localhost:19000 for Expo DevTools"

mobile-logs: ## View mobile development logs
	@$(DOCKER_COMPOSE_DEV) logs -f mobile-dev

# Security
security-check: ## Run security checks
	@echo "$(BLUE)Running security checks...$(NC)"
	@echo "$(YELLOW)Checking for security vulnerabilities...$(NC)"
	@$(DOCKER_COMPOSE_DEV) exec backend-dev pip-audit 2>/dev/null || echo "Install pip-audit for security scanning"
	@$(DOCKER_COMPOSE_DEV) exec frontend-dev npm audit 2>/dev/null || true

# Performance monitoring
monitor: ## Show resource usage
	@echo "$(BLUE)Resource Usage:$(NC)"
	@docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}"

# Quick setup for new developers
quick-start: install ## Quick setup and start development environment
	@echo "$(BLUE)Quick start for new developers...$(NC)"
	@make dev