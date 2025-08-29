# Port Configuration for Resume Optimizer Chatbot

To avoid conflicts with your existing SZABIST Chatbot, this application uses different ports:

## 🔌 **Port Mapping**

| Service | External Port | Internal Port | URL |
|---------|---------------|---------------|-----|
| **Frontend** | `3001` | `3000` | http://localhost:3001 |
| **Backend API** | `8080` | `8000` | http://localhost:8080 |
| **PostgreSQL** | `5433` | `5432` | localhost:5433 |
| **Redis** | `6380` | `6379` | localhost:6380 |

## 🚀 **Access URLs**

- **🌐 Main Application**: http://localhost:3001
- **📊 API Documentation**: http://localhost:8080/docs  
- **⚡ API Health Check**: http://localhost:8080/health
- **💬 WebSocket Chat**: ws://localhost:8080/api/v1/chat/ws/{session_id}

## 🔧 **Configuration Files Updated**

1. **docker-compose.yml** - Updated all port mappings
2. **backend/.env.example** - Updated database and Redis URLs
3. **frontend/.env.example** - Updated API and WebSocket URLs
4. **setup.sh** - Updated health checks and access information
5. **API_REFERENCE.md** - Updated all example URLs

## ⚠️ **Important Notes**

- **No Port Conflicts**: These ports won't interfere with your SZABIST Chatbot
- **Database Isolation**: Uses port 5433 for PostgreSQL (different from default 5432)
- **Redis Separation**: Uses port 6380 for Redis (different from default 6379)
- **Unique Frontend**: Runs on port 3001 instead of 3000

## 🔄 **If You Need Different Ports**

To change ports further, update these files:

1. **docker-compose.yml**:
   ```yaml
   ports:
     - "YOUR_DESIRED_PORT:INTERNAL_PORT"
   ```

2. **Environment Files**:
   ```bash
   REACT_APP_API_URL=http://localhost:YOUR_API_PORT
   DATABASE_URL=postgresql://user:pass@localhost:YOUR_DB_PORT/db
   ```

## 🏃‍♂️ **Quick Start**

```bash
cd resume_optimizer_chatbot
./setup.sh
```

Then visit: **http://localhost:3001**