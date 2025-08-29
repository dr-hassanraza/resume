# Troubleshooting Guide

## 🚀 Quick Start Options

### Option 1: Quick Demo (Recommended for First Run)
```bash
./quick-start.sh
```
- **Minimal dependencies**: Only Python + Node.js required
- **Demo mode**: Simulated AI responses for testing UI
- **No database**: Uses in-memory storage
- **Perfect for**: Testing the interface and functionality

### Option 2: Full Docker Setup
```bash
./setup.sh
```
- **Full features**: Real database, Redis, AI integration
- **Requires**: Docker and Docker Compose
- **Best for**: Production-like environment

### Option 3: Local Development
```bash
./start-local.sh
```
- **Virtual environment**: Isolated Python dependencies
- **SQLite database**: Local file-based storage
- **Good for**: Development and customization

## 🐛 Common Issues

### Issue 1: "command not found" errors

**Problem**: Missing Python or Node.js
```
❌ Python 3 is not installed
❌ Node.js is not installed
```

**Solution**:
1. Install Python 3.8+: https://python.org/downloads/
2. Install Node.js 18+: https://nodejs.org/en/download/
3. Verify installation:
   ```bash
   python3 --version
   node --version
   ```

### Issue 2: Port conflicts

**Problem**: Ports already in use
```
Error: Port 3001 is already in use
Error: Port 8080 is already in use
```

**Solution**: Kill existing processes
```bash
# Find and kill processes using the ports
lsof -ti:3001 | xargs kill -9
lsof -ti:8080 | xargs kill -9

# Or use different ports by editing the scripts
```

### Issue 3: Docker issues

**Problem**: Docker not running or permission errors

**Solution**:
1. Start Docker Desktop
2. Check Docker status: `docker --version`
3. Fix permissions (Mac/Linux):
   ```bash
   sudo usermod -aG docker $USER
   newgrp docker
   ```

### Issue 4: Frontend not loading

**Problem**: React app shows errors or blank page

**Solution**:
1. Check if backend is running: http://localhost:8080/health
2. Clear npm cache:
   ```bash
   cd frontend
   rm -rf node_modules package-lock.json
   npm install
   ```
3. Check browser console for errors

### Issue 5: Backend API errors

**Problem**: 500 errors or connection refused

**Solution**:
1. Check backend logs for errors
2. Verify environment variables in `.env` files
3. For demo mode, use `quick-start.sh` instead

## 🔧 Environment Setup

### Backend Environment (.env)
```bash
# Minimal for demo mode
DATABASE_URL=sqlite:///./resume_optimizer.db
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=["http://localhost:3001"]

# Add AI keys for full functionality
OPENAI_API_KEY=your_key_here
CLAUDE_API_KEY=your_key_here
NEBIUS_API_KEY=your_key_here
```

### Frontend Environment (.env)
```bash
REACT_APP_API_URL=http://localhost:8080
REACT_APP_WS_URL=ws://localhost:8080
```

## 🧪 Testing Steps

1. **Backend Health Check**:
   ```bash
   curl http://localhost:8080/health
   ```
   Should return: `{"status": "healthy"}`

2. **Frontend Access**:
   Visit: http://localhost:3001
   Should show login/register page

3. **WebSocket Connection**:
   Register → Login → Go to Chat
   Should connect and show welcome message

## 📝 Logs and Debugging

### View Backend Logs
```bash
# If using quick-start.sh
tail -f backend/app.log

# If using Docker
docker-compose logs backend
```

### View Frontend Logs
Check browser console (F12) for errors

### Common Log Messages
- ✅ `WebSocket connected` - Chat is working
- ✅ `Servers started!` - Application running
- ❌ `Connection refused` - Backend not running
- ❌ `CORS error` - Frontend/backend port mismatch

## 🔄 Reset and Clean Start

### Complete Reset
```bash
# Stop all processes
pkill -f "uvicorn\|node\|npm"

# Clean Docker (if using)
docker-compose down -v
docker system prune -f

# Clean frontend
cd frontend
rm -rf node_modules package-lock.json

# Clean backend
cd ../backend
rm -rf venv __pycache__ *.db

# Start fresh
./quick-start.sh
```

## 💡 Performance Tips

1. **Use Quick Start for Testing**: Fastest way to see the UI
2. **Enable AI Later**: Add API keys after confirming the app works
3. **Use Docker for Production**: Full setup with all features
4. **Check Resource Usage**: Monitor CPU/memory if slow

## 🆘 Getting Help

### Error Reporting
When reporting issues, please include:
1. Operating system (Mac/Windows/Linux)
2. Python version: `python3 --version`
3. Node.js version: `node --version`
4. Error messages (full output)
5. Which startup method you used

### Demo Account
- Email: demo@example.com
- Password: demo123
- Or register any new account (demo mode)

### Test Features
1. Register/Login ✅
2. Dashboard view ✅
3. Chat interface ✅
4. File upload simulation ✅
5. Analytics dashboard ✅

The application should work in demo mode even without AI API keys!