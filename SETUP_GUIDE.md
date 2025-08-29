# 🚀 Local Hosting Setup Guide

Complete guide to set up and run the AI-Powered Resume Optimizer locally on your machine.

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

### Required Software
- **Docker Desktop** (v20.0+) - [Download here](https://docs.docker.com/get-docker/)
- **Docker Compose** (v2.0+) - Usually included with Docker Desktop
- **Git** - [Download here](https://git-scm.com/downloads)

### Optional (for development)
- **Node.js** (v18+) - [Download here](https://nodejs.org/)
- **Python** (v3.9+) - [Download here](https://python.org/)

## 🔑 Required API Keys

To use all features, you'll need the following API keys:

### Essential (Required)
1. **OpenAI API Key** - [Get it here](https://platform.openai.com/api-keys)
   - Used for GPT models in resume analysis
   - Free tier available with limited usage

2. **Anthropic API Key** - [Get it here](https://console.anthropic.com/login)
   - Used for Claude models in resume analysis
   - Free tier available with limited usage

### Optional (Enhanced Features)
3. **Qwen API Key** - [Get it here](https://dashscope.aliyun.com/)
   - Additional AI model for resume analysis
   - Free tier available

4. **Stripe API Keys** - [Get them here](https://dashboard.stripe.com/apikeys)
   - For subscription and payment processing
   - Test keys available for development

5. **SendGrid API Key** - [Get it here](https://app.sendgrid.com/settings/api_keys)
   - For email notifications
   - Free tier available

## 🚀 Quick Start (Automated Setup)

### Option 1: One-Click Setup (Recommended)

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd resume_optimizer_chatbot
   ```

2. **Run the setup script:**
   ```bash
   ./start-local.sh
   ```
   
   This script will:
   - Check all prerequisites
   - Create necessary directories
   - Copy environment variables
   - Build and start all services
   - Wait for services to be ready
   - Display access URLs and credentials

3. **Add your API keys:**
   - The script will create a `.env` file from `.env.example`
   - Edit the `.env` file and add your API keys:
     ```bash
     # Essential API Keys
     OPENAI_API_KEY=your_openai_key_here
     ANTHROPIC_API_KEY=your_anthropic_key_here
     
     # Optional API Keys
     QWEN_API_KEY=your_qwen_key_here
     STRIPE_SECRET_KEY=sk_test_your_stripe_secret
     NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_your_stripe_public
     SENDGRID_API_KEY=your_sendgrid_key_here
     ```

4. **Restart services (if you added API keys):**
   ```bash
   docker-compose restart backend
   ```

### Option 2: Manual Setup

If you prefer to run commands manually:

1. **Clone and navigate:**
   ```bash
   git clone <repository-url>
   cd resume_optimizer_chatbot
   ```

2. **Create environment file:**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Create directories:**
   ```bash
   mkdir -p backend/uploads logs nginx/ssl
   ```

4. **Start services:**
   ```bash
   docker-compose up -d --build
   ```

5. **Check status:**
   ```bash
   docker-compose ps
   docker-compose logs -f
   ```

## 🌐 Access Your Application

Once setup is complete, access your application:

| Service | URL | Description |
|---------|-----|-------------|
| **Web App** | http://localhost:3000 | Main application interface |
| **API Server** | http://localhost:8000 | Backend API |
| **API Docs** | http://localhost:8000/docs | Interactive API documentation |
| **Database** | localhost:5432 | PostgreSQL database |
| **Cache** | localhost:6379 | Redis cache server |

## 👥 Default Accounts

For testing purposes, the following accounts are pre-created:

| Account Type | Email | Password | Subscription |
|--------------|-------|----------|--------------|
| Demo User | demo@example.com | password123 | Professional |
| Admin User | admin@resumeoptimizer.com | password123 | Enterprise Plus |

## 🧪 Testing the Application

### 1. Basic Functionality Test
- Navigate to http://localhost:3000
- Sign in with demo credentials
- Upload a sample resume (PDF/DOCX)
- Try the AI chat interface
- Check the analytics dashboard

### 2. API Testing
- Visit http://localhost:8000/docs
- Use the interactive API documentation
- Test endpoints with the demo user credentials

### 3. Mobile App (Optional)
```bash
cd mobile
npm install
npm start
```

## 🔧 Development Mode

For development with hot reloading:

### Frontend Development
```bash
cd frontend
npm install
npm run dev
# Access at http://localhost:3001 (different port to avoid conflicts)
```

### Backend Development
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001
# Access at http://localhost:8001 (different port to avoid conflicts)
```

## 🛠️ Common Management Commands

### Docker Compose Commands
```bash
# View all services status
docker-compose ps

# View logs (all services)
docker-compose logs -f

# View logs (specific service)
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres
docker-compose logs -f redis

# Restart a specific service
docker-compose restart backend

# Stop all services
docker-compose down

# Stop and remove volumes (clean slate)
docker-compose down -v --remove-orphans

# Rebuild specific service
docker-compose build backend --no-cache
docker-compose up -d backend
```

### Database Management
```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U postgres -d resume_optimizer

# Backup database
docker-compose exec postgres pg_dump -U postgres resume_optimizer > backup.sql

# Restore database
docker-compose exec -T postgres psql -U postgres resume_optimizer < backup.sql
```

### Redis Cache Management
```bash
# Connect to Redis
docker-compose exec redis redis-cli -a redis123

# Clear all cache
docker-compose exec redis redis-cli -a redis123 FLUSHALL
```

## 🐛 Troubleshooting

### Common Issues and Solutions

#### 1. Port Already in Use
**Error:** `Port 3000 is already in use`

**Solution:**
```bash
# Find what's using the port
lsof -i :3000
# Kill the process or change ports in docker-compose.yml
```

#### 2. Docker Out of Space
**Error:** `No space left on device`

**Solution:**
```bash
# Clean up Docker
docker system prune -a --volumes
docker-compose down -v --remove-orphans
```

#### 3. Services Not Starting
**Error:** Services fail to start or keep restarting

**Solution:**
```bash
# Check logs for specific errors
docker-compose logs -f [service-name]

# Common fixes:
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

#### 4. Database Connection Issues
**Error:** `Connection to database failed`

**Solution:**
```bash
# Wait for database to be ready
docker-compose logs postgres

# Reset database
docker-compose down -v
docker-compose up -d
```

#### 5. Missing API Keys
**Error:** `API key not found` errors in logs

**Solution:**
1. Ensure `.env` file has your API keys
2. Restart the backend service:
   ```bash
   docker-compose restart backend
   ```

#### 6. Frontend Build Issues
**Error:** Frontend fails to build or start

**Solution:**
```bash
# Clear node modules and rebuild
docker-compose down
docker-compose build frontend --no-cache
docker-compose up -d
```

### Health Checks

Check if services are healthy:
```bash
# Check backend health
curl http://localhost:8000/health

# Check database connection
docker-compose exec postgres pg_isready -U postgres

# Check Redis connection
docker-compose exec redis redis-cli -a redis123 ping
```

## 📊 Monitoring

### Service Logs
Monitor application logs in real-time:
```bash
# All services
docker-compose logs -f

# Backend only
docker-compose logs -f backend

# Frontend only  
docker-compose logs -f frontend
```

### Resource Usage
Monitor Docker resource usage:
```bash
# Show resource usage
docker stats

# Show specific containers
docker stats resume_optimizer_backend resume_optimizer_frontend
```

## 🔒 Security Notes

### Development vs Production

This setup is configured for **development only**. For production:

1. **Change default passwords** in `.env`
2. **Use strong JWT secrets** 
3. **Enable SSL/TLS** with proper certificates
4. **Configure firewall** rules
5. **Set up proper monitoring** and logging
6. **Use production-grade database** settings
7. **Implement proper backup** strategies

### Default Credentials
The default credentials are for development only:
- Database: `postgres:password123`
- Redis: `redis123`
- Demo users: `password123`

**Change these in production!**

## 🆘 Getting Help

If you encounter issues:

1. **Check the logs** first:
   ```bash
   docker-compose logs -f
   ```

2. **Verify prerequisites** are installed and working

3. **Check environment variables** in `.env`

4. **Try a clean restart**:
   ```bash
   docker-compose down -v --remove-orphans
   docker-compose build --no-cache
   docker-compose up -d
   ```

5. **Review this guide** for missed steps

## 🎉 Success!

If everything is working correctly, you should see:
- ✅ All services running (`docker-compose ps`)
- ✅ Web app accessible at http://localhost:3000
- ✅ API docs at http://localhost:8000/docs
- ✅ Ability to sign in with demo credentials
- ✅ AI chat responding to messages
- ✅ Resume upload and analysis working

**Happy coding! 🚀**