# 🚀 Netlify Deployment Guide - Resume Optimizer

## 📋 **Deployment Overview**

Your Resume Optimizer is a **full-stack application** that requires:
- **Frontend**: Next.js app (can deploy on Netlify)
- **Backend**: FastAPI Python server (needs separate hosting)

## 🌐 **Frontend Deployment on Netlify**

### **1. Automatic Deployment Setup**
Since you've already connected your GitHub repo to Netlify:

1. **Go to Netlify Dashboard**: https://app.netlify.com/projects/resumeoptimize/
2. **Site Settings** → **Build & deploy**
3. **Configure build settings**:
   - **Base directory**: Leave empty or set to `/`
   - **Build command**: `cd frontend && npm install && npm run build`
   - **Publish directory**: `frontend/.next` (for Next.js static export)

### **2. Environment Variables**
In Netlify Dashboard → **Site settings** → **Environment variables**, add:

```bash
# Frontend environment variables
NEXT_PUBLIC_API_URL=https://your-backend-url.herokuapp.com
NEXT_PUBLIC_WS_URL=wss://your-backend-url.herokuapp.com
NODE_VERSION=18
NEXT_TELEMETRY_DISABLED=1
```

### **3. Build Configuration**
The `netlify.toml` file is already created with optimal settings.

## 🐍 **Backend Deployment Options**

Your FastAPI backend needs separate hosting. Choose one:

### **Option 1: Heroku (Recommended)**
```bash
# 1. Install Heroku CLI
brew install heroku/brew/heroku

# 2. Create Heroku app
heroku create your-resume-backend

# 3. Deploy backend
git subtree push --prefix=backend heroku main
```

### **Option 2: Railway**
1. Visit https://railway.app
2. Connect your GitHub repo
3. Select `backend` folder as root
4. Railway auto-detects Python and deploys

### **Option 3: Render**
1. Visit https://render.com
2. Connect GitHub repo
3. Create Web Service from `backend` directory

### **Option 4: DigitalOcean App Platform**
1. Visit https://cloud.digitalocean.com/apps
2. Connect GitHub repo
3. Configure Python app from `backend` folder

## 🔧 **Complete Deployment Steps**

### **Step 1: Deploy Backend First**
```bash
# Example with Heroku
cd /Users/macair2020/Desktop/resume-optimizer-github/backend
heroku create resume-optimizer-backend
git init
git add .
git commit -m "Backend deployment"
heroku git:remote -a resume-optimizer-backend
git push heroku main
```

### **Step 2: Update Frontend Environment**
1. Get your backend URL (e.g., `https://resume-optimizer-backend.herokuapp.com`)
2. Update Netlify environment variables with the real backend URL

### **Step 3: Deploy Frontend**
1. Push the updated `netlify.toml` to your GitHub repo
2. Netlify will automatically redeploy

## 🗄️ **Database Setup**

For production, you'll need a hosted database:

### **Option 1: PostgreSQL (Recommended)**
```bash
# Add PostgreSQL addon to Heroku
heroku addons:create heroku-postgresql:mini -a resume-optimizer-backend
```

### **Option 2: PlanetScale (MySQL)**
1. Visit https://planetscale.com
2. Create database
3. Update DATABASE_URL in backend environment

### **Option 3: Supabase (PostgreSQL)**
1. Visit https://supabase.com
2. Create project
3. Use connection string in backend

## 🛠️ **Environment Variables Setup**

### **Backend Environment Variables**
Set these in your backend hosting platform (Heroku/Railway/Render):

```bash
DATABASE_URL=your_production_database_url
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
Z_AI_API_KEY=your_z_ai_key
JWT_SECRET=your_jwt_secret_for_production
SECRET_KEY=your_app_secret_for_production
CORS_ORIGINS=https://resumeoptimize.netlify.app
```

### **Frontend Environment Variables**
Set these in Netlify:

```bash
NEXT_PUBLIC_API_URL=https://your-backend-url.herokuapp.com
NEXT_PUBLIC_WS_URL=wss://your-backend-url.herokuapp.com
```

## 🚀 **Quick Deployment Commands**

```bash
# 1. Navigate to your GitHub project
cd /Users/macair2020/Desktop/resume-optimizer-github

# 2. Add netlify.toml to git
git add netlify.toml NETLIFY_DEPLOYMENT.md
git commit -m "Add Netlify deployment configuration"
git push origin main

# 3. Netlify will automatically deploy the frontend
# 4. Deploy backend separately using your chosen platform
```

## 🌟 **Final Result**

After deployment:
- **Frontend**: https://resumeoptimize.netlify.app (your custom domain)
- **Backend**: https://your-backend-url.herokuapp.com
- **Full functionality**: Resume upload, AI chat, analytics dashboard

## ⚠️ **Important Notes**

1. **Backend Deployment Required**: Netlify only hosts static sites, so your Python backend needs separate hosting
2. **Database Required**: You'll need a production database (not the local SQLite)
3. **Environment Variables**: Must be set in both Netlify (frontend) and backend hosting platform
4. **CORS Configuration**: Make sure backend allows requests from your Netlify domain

## 🆘 **Troubleshooting**

- **Build Fails**: Check Node.js version (should be 18+)
- **API Calls Fail**: Verify backend URL in NEXT_PUBLIC_API_URL
- **CORS Errors**: Add Netlify domain to backend CORS_ORIGINS
- **Database Connection**: Ensure DATABASE_URL is correctly set in backend

Your resume optimizer will be live and fully functional! 🎉