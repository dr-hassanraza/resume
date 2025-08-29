# 🐳 Docker Installation Guide for macOS

## Quick Installation Steps

### Option 1: Download Docker Desktop Directly
1. **Download Docker Desktop for Mac (Apple Silicon)**
   - Visit: https://desktop.docker.com/mac/main/arm64/Docker.dmg
   - Download the .dmg file
   - Double-click the downloaded file
   - Drag Docker to Applications folder
   - Open Docker Desktop from Applications

### Option 2: Using Homebrew (if available)
```bash
brew install --cask docker
```

### Option 3: Manual Download
1. Go to https://docs.docker.com/desktop/install/mac-install/
2. Click "Docker Desktop for Mac with Apple Chip"
3. Install and run Docker Desktop

## After Installation

### 1. Start Docker Desktop
- Open Docker Desktop from Applications
- Wait for it to start (whale icon in menu bar)
- Accept terms and conditions if prompted

### 2. Verify Installation
```bash
docker --version
docker-compose --version
```

### 3. Test Docker
```bash
docker run hello-world
```

## Once Docker is Ready

### Start the Full Application
```bash
# Navigate to project directory
cd /Users/macair2020/Desktop/resume_optimizer_chatbot

# Option 1: Use the automated script
./start-local.sh

# Option 2: Use Makefile
make install
make prod

# Option 3: Manual Docker Compose
docker-compose up -d --build
```

## What You'll Get

✅ **Full Enterprise Platform:**
- 🌐 Web App at http://localhost:3000
- 🔧 API Server at http://localhost:8000
- 📊 API Docs at http://localhost:8000/docs
- 🗄️ PostgreSQL Database
- ⚡ Redis Cache
- 📱 Mobile App Ready

✅ **All Features Working:**
- AI-powered resume analysis
- Real-time chat with WebSocket
- File upload and processing
- Team collaboration
- API monetization
- Advanced analytics
- Mobile app support

## Troubleshooting

### If Docker won't start:
```bash
# Reset Docker Desktop
killall Docker
open -a "Docker Desktop"
```

### If ports are in use:
```bash
# Check what's using ports
lsof -i :3000
lsof -i :8000
lsof -i :5432

# Kill processes if needed
sudo killall -9 node
sudo killall -9 python
```

### If build fails:
```bash
# Clean up and rebuild
docker system prune -af
docker-compose build --no-cache
docker-compose up -d
```

## Next Steps After Docker is Running

1. **Configure API Keys** in `.env`:
   ```bash
   OPENAI_API_KEY=your_key_here
   ANTHROPIC_API_KEY=your_key_here
   ```

2. **Access the Application**:
   - Web: http://localhost:3000
   - API: http://localhost:8000/docs

3. **Test with Demo Account**:
   - Email: demo@example.com
   - Password: password123

---

**Need Help?** Run `./start-local.sh` for automated setup with health checks!