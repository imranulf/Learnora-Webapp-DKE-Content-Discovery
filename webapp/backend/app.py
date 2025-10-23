"""
Adaptive Learning Platform - Flask Backend
===========================================

Full-stack web application integrating:
- DKE (Dynamic Knowledge Evaluation)
- Content Discovery System
- User Authentication
- Chat Interface
- Learning Path Management
"""
from flask import Flask, request, jsonify, session
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import secrets
import sys
import os

# Add parent directory to path for DKE imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from dke import DKEPipeline, CATConfig, BKTParams, SelfAssessment, _build_demo_bank, _simulate_student
from dke_content_integration import AdaptiveLearningPipeline, create_demo_content
from Project import UserProfile as DKEUserProfile

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(32)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///learning_platform.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False  # Set True in production with HTTPS

# Enable CORS
CORS(app, supports_credentials=True, origins=['http://localhost:3000'])

# Initialize database
db = SQLAlchemy(app)

# Initialize DKE Pipeline (global - in production use per-user instances)
bank, skills = _build_demo_bank()
dke_pipeline = DKEPipeline(
    bank=bank,
    cat_cfg=CATConfig(max_items=10, se_stop=0.35),
    skills=skills,
    bkt_params=BKTParams(p_init=0.3, p_transit=0.25)
)
adaptive_pipeline = AdaptiveLearningPipeline(dke_pipeline=dke_pipeline)

# Add demo content
demo_content = create_demo_content()
if demo_content:
    adaptive_pipeline.discovery.vector_db.add_contents(demo_content)

# =====================
# Database Models
# =====================

class User(db.Model):
    """User model with authentication"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Learning profile
    preferred_formats = db.Column(db.String(200), default='article,video')
    learning_goals = db.Column(db.Text, default='')
    available_time_daily = db.Column(db.Integer, default=60)
    
    # Relationships
    chat_messages = db.relationship('ChatMessage', backref='user', lazy=True, cascade='all, delete-orphan')
    learning_paths = db.relationship('LearningPath', backref='user', lazy=True, cascade='all, delete-orphan')
    assessments = db.relationship('Assessment', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'preferred_formats': self.preferred_formats.split(',') if self.preferred_formats else [],
            'learning_goals': self.learning_goals.split(',') if self.learning_goals else [],
            'available_time_daily': self.available_time_daily,
            'created_at': self.created_at.isoformat()
        }


class ChatMessage(db.Model):
    """Chat messages for AI tutor interaction"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'message': self.message,
            'response': self.response,
            'timestamp': self.timestamp.isoformat()
        }


class LearningPath(db.Model):
    """Generated learning paths for users"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    content_items = db.Column(db.Text)  # JSON string of content IDs
    estimated_time = db.Column(db.Integer)  # minutes
    progress = db.Column(db.Integer, default=0)  # percentage
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    def to_dict(self):
        import json
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'content_items': json.loads(self.content_items) if self.content_items else [],
            'estimated_time': self.estimated_time,
            'progress': self.progress,
            'created_at': self.created_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }


class Assessment(db.Model):
    """User assessment results"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    theta = db.Column(db.Float)  # IRT ability estimate
    mastery_scores = db.Column(db.Text)  # JSON string
    learning_gaps = db.Column(db.Text)  # JSON string
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        import json
        return {
            'id': self.id,
            'theta': self.theta,
            'mastery_scores': json.loads(self.mastery_scores) if self.mastery_scores else {},
            'learning_gaps': json.loads(self.learning_gaps) if self.learning_gaps else [],
            'timestamp': self.timestamp.isoformat()
        }


# =====================
# Authentication Routes
# =====================

@app.route('/api/auth/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.get_json()
        
        # Validate input
        if not data.get('username') or not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Check if user already exists
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'error': 'Username already exists'}), 400
        
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already exists'}), 400
        
        # Create new user
        user = User(
            username=data['username'],
            email=data['email']
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        # Set session
        session['user_id'] = user.id
        session['username'] = user.username
        
        return jsonify({
            'message': 'Registration successful',
            'user': user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/auth/login', methods=['POST'])
def login():
    """Login user"""
    try:
        data = request.get_json()
        
        user = User.query.filter_by(username=data.get('username')).first()
        
        if not user or not user.check_password(data.get('password', '')):
            return jsonify({'error': 'Invalid username or password'}), 401
        
        # Set session
        session['user_id'] = user.id
        session['username'] = user.username
        
        return jsonify({
            'message': 'Login successful',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/auth/logout', methods=['POST'])
def logout():
    """Logout user"""
    session.clear()
    return jsonify({'message': 'Logout successful'}), 200


@app.route('/api/auth/me', methods=['GET'])
def get_current_user():
    """Get current logged-in user"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({'user': user.to_dict()}), 200


# =====================
# Chat Routes
# =====================

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat messages with AI tutor"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        data = request.get_json()
        message = data.get('message', '')
        
        if not message:
            return jsonify({'error': 'Message cannot be empty'}), 400
        
        # Generate AI response (simplified - in production use OpenAI/Anthropic)
        response = generate_chat_response(message, user_id)
        
        # Save chat message
        chat_msg = ChatMessage(
            user_id=user_id,
            message=message,
            response=response
        )
        db.session.add(chat_msg)
        db.session.commit()
        
        return jsonify({
            'message': message,
            'response': response,
            'timestamp': chat_msg.timestamp.isoformat()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/chat/history', methods=['GET'])
def get_chat_history():
    """Get chat history for current user"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    limit = request.args.get('limit', 50, type=int)
    
    messages = ChatMessage.query.filter_by(user_id=user_id)\
        .order_by(ChatMessage.timestamp.desc())\
        .limit(limit)\
        .all()
    
    return jsonify({
        'messages': [msg.to_dict() for msg in reversed(messages)]
    }), 200


# =====================
# Assessment Routes
# =====================

@app.route('/api/assessment/start', methods=['POST'])
def start_assessment():
    """Start a new DKE assessment"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        user = User.query.get(user_id)
        
        # Create user profile for DKE
        user_profile = DKEUserProfile(
            user_id=str(user_id),
            preferred_formats=user.preferred_formats.split(',') if user.preferred_formats else [],
            learning_goals=user.learning_goals.split(',') if user.learning_goals else [],
            available_time_daily=user.available_time_daily
        )
        
        # Simulate student for demo (in production, use actual quiz responses)
        theta_true = 0.0  # Average ability
        oracle = _simulate_student(theta_true, bank)
        
        # Run assessment
        self_assess = SelfAssessment(confidence={"algebra": 2, "probability": 3, "functions": 3})
        
        bundle = adaptive_pipeline.run_assessment_and_recommend(
            user_id=str(user_id),
            response_free_text="I understand basic algebra concepts.",
            reference_text="Algebra involves variables and equations.",
            self_assess=self_assess,
            concept_edges=[("variable", "equation")],
            required_edges=[("variable", "equation"), ("equation", "solution")],
            oracle=oracle,
            user_profile=user_profile,
            context="mathematics"
        )
        
        # Save assessment
        import json
        assessment = Assessment(
            user_id=user_id,
            theta=bundle.assessment_summary['theta'],
            mastery_scores=json.dumps(bundle.assessment_summary['mastery_scores']),
            learning_gaps=json.dumps([{
                'skill': gap.skill,
                'mastery_level': gap.mastery_level,
                'priority': gap.priority,
                'recommended_difficulty': gap.recommended_difficulty
            } for gap in bundle.learning_gaps])
        )
        db.session.add(assessment)
        
        # Create learning path from recommendations
        if bundle.recommended_content:
            learning_path = LearningPath(
                user_id=user_id,
                title=f"Learning Path - {datetime.now().strftime('%Y-%m-%d')}",
                description=f"Personalized path based on assessment",
                content_items=json.dumps(bundle.learning_path),
                estimated_time=bundle.estimated_completion_time
            )
            db.session.add(learning_path)
        
        db.session.commit()
        
        return jsonify({
            'assessment': {
                'theta': bundle.assessment_summary['theta'],
                'mastery_scores': bundle.assessment_summary['mastery_scores'],
                'learning_gaps': [{
                    'skill': gap.skill,
                    'mastery_level': gap.mastery_level,
                    'priority': gap.priority,
                    'recommended_difficulty': gap.recommended_difficulty,
                    'estimated_study_time': gap.estimated_study_time
                } for gap in bundle.learning_gaps],
                'recommended_content': bundle.recommended_content
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/assessment/history', methods=['GET'])
def get_assessment_history():
    """Get assessment history"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    assessments = Assessment.query.filter_by(user_id=user_id)\
        .order_by(Assessment.timestamp.desc())\
        .all()
    
    return jsonify({
        'assessments': [a.to_dict() for a in assessments]
    }), 200


# =====================
# Learning Path Routes
# =====================

@app.route('/api/learning-paths', methods=['GET'])
def get_learning_paths():
    """Get all learning paths for current user"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    paths = LearningPath.query.filter_by(user_id=user_id)\
        .order_by(LearningPath.created_at.desc())\
        .all()
    
    return jsonify({
        'learning_paths': [path.to_dict() for path in paths]
    }), 200


@app.route('/api/learning-paths/<int:path_id>', methods=['GET'])
def get_learning_path(path_id):
    """Get specific learning path with content details"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    path = LearningPath.query.filter_by(id=path_id, user_id=user_id).first()
    if not path:
        return jsonify({'error': 'Learning path not found'}), 404
    
    # Get content details from discovery system
    import json
    content_ids = json.loads(path.content_items) if path.content_items else []
    content_details = []
    
    for content_id in content_ids:
        content = adaptive_pipeline.discovery.vector_db.contents.get(content_id)
        if content:
            content_details.append({
                'id': content.id,
                'title': content.title,
                'content_type': content.content_type,
                'difficulty': content.difficulty,
                'duration_minutes': content.duration_minutes,
                'description': content.description,
                'url': content.url,
                'tags': content.tags
            })
    
    return jsonify({
        'learning_path': path.to_dict(),
        'content_details': content_details
    }), 200


@app.route('/api/learning-paths/<int:path_id>/progress', methods=['PUT'])
def update_learning_path_progress(path_id):
    """Update progress on a learning path"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        data = request.get_json()
        progress = data.get('progress', 0)
        
        path = LearningPath.query.filter_by(id=path_id, user_id=user_id).first()
        if not path:
            return jsonify({'error': 'Learning path not found'}), 404
        
        path.progress = min(100, max(0, progress))
        
        if path.progress >= 100 and not path.completed_at:
            path.completed_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'learning_path': path.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# =====================
# Utility Functions
# =====================

def generate_chat_response(message, user_id):
    """Generate chat response (simplified AI tutor)"""
    message_lower = message.lower()
    
    # Simple rule-based responses (in production use LLM)
    if any(word in message_lower for word in ['help', 'stuck', 'confused']):
        return "I'm here to help! What specific topic are you struggling with? I can provide personalized resources based on your learning path."
    
    elif any(word in message_lower for word in ['assessment', 'test', 'quiz']):
        return "Would you like to take an assessment? This will help me understand your current knowledge level and create a personalized learning path for you. Click 'Start Assessment' to begin!"
    
    elif any(word in message_lower for word in ['recommend', 'learn', 'study']):
        user = User.query.get(user_id)
        latest_path = LearningPath.query.filter_by(user_id=user_id)\
            .order_by(LearningPath.created_at.desc()).first()
        
        if latest_path:
            return f"Based on your latest assessment, I recommend starting with '{latest_path.title}'. It's estimated to take {latest_path.estimated_time} minutes. Check your Learning Paths dashboard!"
        else:
            return "I'd love to recommend resources! First, let's assess your current knowledge. Click 'Start Assessment' to get personalized recommendations."
    
    elif any(word in message_lower for word in ['progress', 'doing', 'performance']):
        assessments = Assessment.query.filter_by(user_id=user_id)\
            .order_by(Assessment.timestamp.desc()).limit(2).all()
        
        if assessments:
            latest = assessments[0]
            import json
            mastery = json.loads(latest.mastery_scores)
            return f"Great question! Your current mastery levels: {', '.join([f'{k}: {v*100:.0f}%' for k, v in mastery.items()])}. Keep up the good work!"
        else:
            return "You haven't taken an assessment yet. Let's evaluate your knowledge to track your progress!"
    
    else:
        return f"Thanks for your message! I'm your AI learning assistant. I can help you with assessments, recommend learning materials, and track your progress. How can I assist you today?"


# =====================
# Database Initialization
# =====================

# Removed @app.before_first_request (deprecated in Flask 3.0)
# Database initialization moved to app_context below


# =====================
# Run Application
# =====================

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("Database initialized!")
    
    print("\n" + "="*60)
    print("Learnora Backend Starting...")
    print("="*60)
    print(f"Server: http://localhost:5000")
    print(f"DKE Pipeline: Initialized with {len(bank.items)} items")
    print(f"Content Database: {len(adaptive_pipeline.discovery.vector_db.contents)} items")
    print("="*60 + "\n")
    
    app.run(debug=True, port=5000, host='0.0.0.0')
