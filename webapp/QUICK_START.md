# Learnora - Quick Start Commands

## 🚀 Starting the Application

### Option 1: Manual Start (Recommended for Windows)

#### Terminal 1 - Backend
```powershell
cd C:\Users\imran\CD_DKE\webapp\backend
$env:PYTHONPATH = "C:\Users\imran\CD_DKE"
python app.py
```
✅ Backend starts at: **http://localhost:5000**

#### Terminal 2 - Frontend
```powershell
cd C:\Users\imran\CD_DKE\webapp\frontend
$env:Path = "C:\Program Files\nodejs;" + $env:Path
& "C:\Program Files\nodejs\node.exe" node_modules\react-scripts\bin\react-scripts.js start
```
✅ Frontend starts at: **http://localhost:3000** or **http://localhost:3001**

---

## 🔍 Checking Status

### Backend Health Check
```powershell
# Open browser to:
http://localhost:5000/api/auth/me
# Should return: {"error": "Not authenticated"}
```

### Frontend Access
```powershell
# Open browser to:
http://localhost:3001
# Should see Learnora logo and login page
```

---

## 🛑 Stopping the Application

### Stop Backend
```powershell
# In backend terminal:
Press Ctrl+C
```

### Stop Frontend
```powershell
# In frontend terminal:
Press Ctrl+C
```

---

## 🔄 Restarting After Changes

### After Backend Code Changes
```powershell
# Flask auto-reloads in debug mode
# Just save the file and it restarts automatically
# Or manually restart with Ctrl+C then re-run python app.py
```

### After Frontend Code Changes
```powershell
# React auto-reloads via Hot Module Replacement (HMR)
# Just save the file and browser refreshes automatically
```

### After package.json Changes
```powershell
# Must restart the frontend server
# 1. Press Ctrl+C in frontend terminal
# 2. Re-run the frontend start command
```

### After requirements.txt Changes
```powershell
# Install new packages:
cd C:\Users\imran\CD_DKE\webapp\backend
pip install -r requirements.txt
# Then restart backend
```

---

## 📦 Fresh Install Commands

### First Time Setup - Backend
```powershell
cd C:\Users\imran\CD_DKE\webapp\backend
pip install -r requirements.txt
```

### First Time Setup - Frontend
```powershell
cd C:\Users\imran\CD_DKE\webapp\frontend
& "C:\Program Files\nodejs\node.exe" "C:\Program Files\nodejs\node_modules\npm\bin\npm-cli.js" install
```

---

## 🧹 Clean Install (If Issues Occur)

### Backend Clean Install
```powershell
cd C:\Users\imran\CD_DKE\webapp\backend
# Remove database
Remove-Item learning_platform.db -ErrorAction SilentlyContinue
# Reinstall packages
pip install -r requirements.txt --force-reinstall
# Start server (database will be recreated)
python app.py
```

### Frontend Clean Install
```powershell
cd C:\Users\imran\CD_DKE\webapp\frontend
# Remove node_modules and package-lock
Remove-Item -Recurse -Force node_modules -ErrorAction SilentlyContinue
Remove-Item package-lock.json -ErrorAction SilentlyContinue
# Reinstall
& "C:\Program Files\nodejs\node.exe" "C:\Program Files\nodejs\node_modules\npm\bin\npm-cli.js" install
```

---

## 🐛 Troubleshooting Commands

### Check if Port 5000 is in Use
```powershell
netstat -ano | findstr :5000
# If occupied, kill the process:
taskkill /PID <PID> /F
```

### Check if Port 3000/3001 is in Use
```powershell
netstat -ano | findstr :3000
netstat -ano | findstr :3001
# If occupied, kill the process:
taskkill /PID <PID> /F
```

### Check Python Environment
```powershell
python --version
# Should show: Python 3.13.5
pip list | findstr Flask
# Should show Flask 3.0.0 and related packages
```

### Check Node.js Installation
```powershell
& "C:\Program Files\nodejs\node.exe" --version
# Should show: v20.x or similar
```

### View Backend Logs
```powershell
# Backend logs appear in the terminal where python app.py is running
# Look for:
# - "Learnora Backend Starting..."
# - "Running on http://127.0.0.1:5000"
```

### View Frontend Logs
```powershell
# Frontend logs appear in the terminal where npm start is running
# Look for:
# - "Compiled successfully!"
# - "Local: http://localhost:3001"
```

---

## 📝 Common Tasks

### Create a Test User via API
```powershell
# Using curl (if installed):
curl -X POST http://localhost:5000/api/auth/register `
  -H "Content-Type: application/json" `
  -d '{"username":"testuser","email":"test@example.com","password":"test123"}'
```

### Reset Database
```powershell
cd C:\Users\imran\CD_DKE\webapp\backend
Remove-Item learning_platform.db
python app.py
# Database will be recreated with empty tables
```

### View Database Contents (using SQLite browser)
```powershell
# Install DB Browser for SQLite: https://sqlitebrowser.org/
# Then open: C:\Users\imran\CD_DKE\webapp\backend\learning_platform.db
```

---

## 🎯 Quick Access URLs

| Service | URL | Purpose |
|---------|-----|---------|
| Frontend | http://localhost:3001 | Main application |
| Backend API | http://localhost:5000 | REST API |
| Auth Check | http://localhost:5000/api/auth/me | Test authentication |
| Learning Paths | http://localhost:5000/api/learning-paths | View paths API |

---

## 🔐 Default Test Credentials

**None created by default**

Create your first user through:
1. Frontend UI: http://localhost:3001/register
2. Or API: POST to `/api/auth/register`

---

## 💡 Pro Tips

1. **Keep both terminals visible** - You can see errors immediately
2. **Use browser DevTools (F12)** - Check Console and Network tabs for frontend issues
3. **Check backend terminal** - All API calls are logged there
4. **Save files to see changes** - Both React and Flask auto-reload
5. **Use meaningful test data** - Makes debugging easier

---

## 🚨 Emergency Reset

If everything breaks:

```powershell
# 1. Stop both servers (Ctrl+C in both terminals)

# 2. Clean backend
cd C:\Users\imran\CD_DKE\webapp\backend
Remove-Item learning_platform.db -ErrorAction SilentlyContinue

# 3. Clean frontend
cd C:\Users\imran\CD_DKE\webapp\frontend
Remove-Item -Recurse -Force node_modules -ErrorAction SilentlyContinue

# 4. Reinstall frontend
& "C:\Program Files\nodejs\node.exe" "C:\Program Files\nodejs\node_modules\npm\bin\npm-cli.js" install

# 5. Start backend
cd C:\Users\imran\CD_DKE\webapp\backend
$env:PYTHONPATH = "C:\Users\imran\CD_DKE"
python app.py

# 6. Start frontend (in new terminal)
cd C:\Users\imran\CD_DKE\webapp\frontend
$env:Path = "C:\Program Files\nodejs;" + $env:Path
& "C:\Program Files\nodejs\node.exe" node_modules\react-scripts\bin\react-scripts.js start
```

---

**Last Updated**: October 22, 2025  
**Platform**: Learnora - Adaptive Learning Platform  
**Version**: 1.0.0
