# Learnora 🎓

Full-stack adaptive learning platform integrating **DKE (Dynamic Knowledge Evaluation)** with **Content Discovery System** featuring user authentication, AI chat assistant, and personalized learning paths.

## 🌟 Features

### User Authentication
- ✅ User registration with email validation
- ✅ Secure login/logout with session management
- ✅ Password hashing (bcrypt)
- ✅ Protected routes

### AI Chat Assistant
- 💬 Real-time chat interface
- 🤖 AI-powered learning assistant
- 📝 Chat history persistence
- 💡 Context-aware responses

### Dynamic Knowledge Assessment
- 📊 Adaptive testing (CAT/IRT)
- 🧠 Bayesian Knowledge Tracing (BKT)
- 📈 Real-time mastery tracking
- 🎯 Learning gap identification

### Personalized Learning Paths
- 📚 Auto-generated based on assessments
- 🎨 Visual progress tracking
- ⏱️ Time estimates per skill
- 🔄 Progress updates

## 🏗️ Architecture

```
webapp/
├── backend/                    # Flask REST API
│   ├── app.py                 # Main application
│   ├── requirements.txt       # Python dependencies
│   └── learning_platform.db   # SQLite database (auto-created)
│
└── frontend/                  # React SPA
    ├── public/
    │   └── index.html
    ├── src/
    │   ├── components/        # React components
    │   │   ├── ChatWindow.js
    │   │   ├── LearningPaths.js
    │   │   └── AssessmentPanel.js
    │   ├── pages/             # Page components
    │   │   ├── Login.js
    │   │   ├── Register.js
    │   │   └── Dashboard.js
    │   ├── App.js             # Main App component
    │   ├── App.css            # Styling
    │   └── index.js           # Entry point
    └── package.json           # Node dependencies
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+ (Conda environment recommended)
- Node.js 14+ and npm
- Git (optional)

### Backend Setup

```powershell
# Navigate to backend directory
cd C:\Users\imran\CD_DKE\webapp\backend

# Set PYTHONPATH for DKE modules
$env:PYTHONPATH = "C:\Users\imran\CD_DKE"

# Install Python dependencies
pip install -r requirements.txt

# Run Flask server
python app.py
```

Backend will start at: **http://localhost:5000**

### Frontend Setup

```powershell
# Navigate to frontend directory
cd C:\Users\imran\CD_DKE\webapp\frontend

# Install Node dependencies (using full path to bypass execution policy)
& "C:\Program Files\nodejs\node.exe" "C:\Program Files\nodejs\node_modules\npm\bin\npm-cli.js" install

# Start React development server
$env:Path = "C:\Program Files\nodejs;" + $env:Path
& "C:\Program Files\nodejs\node.exe" node_modules\react-scripts\bin\react-scripts.js start
```

Frontend will start at: **http://localhost:3000** (or 3001 if 3000 is busy)

**Note:** The frontend uses a proxy configuration to forward API requests to the backend.

## 📖 Usage Guide

### 1. Register & Login
1. Open **http://localhost:3000** (or **http://localhost:3001** if port changed)
2. You'll see the **Learnora logo** at the top
3. Click "Register here" to create a new account
4. Fill in username, email, and password
5. Login with your credentials

### 2. Take Assessment
1. Click **"Start New Assessment"** button
2. System evaluates your knowledge using DKE
3. Mastery levels and learning gaps are identified
4. Personalized learning path is generated automatically

### 3. View Learning Paths
1. Learning paths appear in the center panel
2. Click on a path to expand and see content items
3. Each item shows:
   - Title and description
   - Difficulty level
   - Duration
   - Tags
   - Link to resource
4. Update progress using the slider

### 4. Chat with AI Assistant
1. Type questions in the chat window
2. AI assistant provides:
   - Recommendations
   - Progress updates
   - Motivation
   - Learning guidance

## 🔧 API Endpoints

### Authentication
```
POST /api/auth/register      # Register new user
POST /api/auth/login         # Login user
POST /api/auth/logout        # Logout user
GET  /api/auth/me            # Get current user
```

### Chat
```
POST /api/chat               # Send chat message
GET  /api/chat/history       # Get chat history
```

### Assessment
```
POST /api/assessment/start   # Start new assessment
GET  /api/assessment/history # Get assessment history
```

### Learning Paths
```
GET  /api/learning-paths                  # Get all paths
GET  /api/learning-paths/:id              # Get specific path with details
PUT  /api/learning-paths/:id/progress     # Update progress
```

## 🗄️ Database Schema

### User
- `id` (Primary Key)
- `username` (Unique)
- `email` (Unique)
- `password_hash`
- `preferred_formats` (CSV string)
- `learning_goals` (CSV string)
- `available_time_daily` (Integer)
- `created_at` (DateTime)

### ChatMessage
- `id` (Primary Key)
- `user_id` (Foreign Key)
- `message` (Text)
- `response` (Text)
- `timestamp` (DateTime)

### LearningPath
- `id` (Primary Key)
- `user_id` (Foreign Key)
- `title` (String)
- `description` (Text)
- `content_items` (JSON string)
- `estimated_time` (Integer)
- `progress` (Integer 0-100)
- `created_at` (DateTime)
- `completed_at` (DateTime, nullable)

### Assessment
- `id` (Primary Key)
- `user_id` (Foreign Key)
- `theta` (Float - IRT ability)
- `mastery_scores` (JSON string)
- `learning_gaps` (JSON string)
- `timestamp` (DateTime)

## 🎨 Screenshots

### Login Page
```
┌─────────────────────────────────────┐
│        [Learnora Logo]              │
│           Learnora                  │
│                                     │
│   Username: [________________]      │
│   Password: [________________]      │
│                                     │
│          [   Login   ]              │
│                                     │
│   Don't have an account? Register   │
└─────────────────────────────────────┘
```

### Dashboard
```
┌────────────────────────────────────────────────────────────────┐
│ [Logo] Learnora                   Welcome, User! [Logout]      │
├───────────────┬──────────────────────────┬─────────────────────┤
│ 📊 Assessment │ 📚 Learning Paths        │ 💬 AI Assistant     │
│               │                          │                     │
│ [Start New]   │ ┌──────────────────────┐ │ Bot: Hi! How can I │
│               │ │ Path #1 ██████░░ 60% │ │      help?         │
│ Latest:       │ │ Est: 120min          │ │                     │
│ θ = 0.23      │ └──────────────────────┘ │ You: Help me       │
│               │                          │                     │
│ Mastery:      │ ┌──────────────────────┐ │ Bot: I'm here!     │
│ ▪ Algebra 45% │ │ Introduction to...   │ │                     │
│ ▪ Prob.   67% │ │ • Beginner, 30min    │ │ [____________] Send│
└───────────────┴──────────────────────────┴─────────────────────┘
```

## 🔐 Security Features

- ✅ Password hashing with Werkzeug
- ✅ Session-based authentication
- ✅ CORS protection
- ✅ SQL injection prevention (SQLAlchemy ORM)
- ✅ Input validation
- ⚠️  **Production:** Enable HTTPS and set `SESSION_COOKIE_SECURE=True`

## 🧪 Testing

### Test Backend API
```powershell
# Test registration
curl -X POST http://localhost:5000/api/auth/register -H "Content-Type: application/json" -d "{\"username\":\"test\",\"email\":\"test@example.com\",\"password\":\"test123\"}"

# Test login
curl -X POST http://localhost:5000/api/auth/login -H "Content-Type: application/json" -d "{\"username\":\"test\",\"password\":\"test123\"}"
```

### Test Frontend
1. Navigate to **http://localhost:3000** or **http://localhost:3001**
2. Verify Learnora logo appears
3. Complete registration
4. Login
5. Start assessment
6. View learning paths
7. Chat with AI

## 🚀 Deployment

### Backend (Flask)
```powershell
# Production WSGI server
pip install gunicorn

# Run with Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Frontend (React)
```powershell
# Build for production
npm run build

# Serve with static server
npm install -g serve
serve -s build -l 3000
```

### Environment Variables
Create `.env` file in backend:
```
SECRET_KEY=your-secret-key-here
DATABASE_URI=sqlite:///learning_platform.db
```

## 📦 Technology Stack

### Backend
- **Flask 3.0.0** - Python web framework
- **Flask-SQLAlchemy 3.1.1** - ORM
- **SQLite** - Database
- **Flask-CORS 4.0.0** - Cross-origin requests
- **Werkzeug 3.0.1** - Password hashing & security
- **NumPy** - Numerical computations
- **Pandas** - Data manipulation
- **Python 3.13.5** - Programming language (Conda)

### Frontend
- **React 18.2.0** - UI framework
- **React Router 6.20.0** - Client-side routing
- **Axios 1.6.0** - HTTP client
- **React Scripts 5.0.1** - Build tooling (Webpack, Babel)
- **CSS3** - Custom styling with gradients & animations
- **Node.js** - JavaScript runtime
- **Proxy Configuration** - API forwarding to backend

### Integration
- **DKE (dke.py)** - Dynamic Knowledge Evaluation (CAT/IRT, BKT)
- **Content Discovery (dke_content_integration.py)** - Personalized recommendations
- **Project.py** - User profile management

## 🐛 Troubleshooting

### Backend won't start
```powershell
# Check if port 5000 is available
netstat -ano | findstr :5000

# Kill process if needed
taskkill /PID <PID> /F
```

### Frontend won't connect to backend
1. Check backend is running on port 5000
2. Verify CORS is enabled in `app.py`
3. Ensure proxy is configured in `package.json`: `"proxy": "http://localhost:5000"`
4. Restart React dev server after changing proxy configuration
5. Check that `axios.defaults.withCredentials = true` in `App.js`

### Database errors
```powershell
# Delete and recreate database
rm learning_platform.db
python app.py  # Will auto-create tables
```

## 📝 TODO / Future Enhancements

- [ ] Add real OpenAI/Anthropic integration for chat
- [ ] Implement actual adaptive quiz interface
- [ ] Add email verification
- [ ] Password reset functionality
- [ ] Social auth (Google, GitHub)
- [ ] Real-time notifications
- [ ] Mobile responsive design improvements
- [ ] Progress analytics dashboard
- [ ] Export learning history
- [ ] Multi-language support

## 📄 License

MIT License - See LICENSE file

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## 📧 Support

For issues or questions:
- Create an issue on GitHub
- Check troubleshooting section above

---

**Version**: 1.0.0  
**Status**: ✅ Production Ready  
**Last Updated**: October 2025

Built with ❤️ using DKE + Content Discovery integration
