import React, { useState, useEffect } from 'react';
import axios from 'axios';
import ChatWindow from '../components/ChatWindow';
import LearningPaths from '../components/LearningPaths';
import AssessmentPanel from '../components/AssessmentPanel';

function Dashboard({ user, onLogout }) {
  const [assessments, setAssessments] = useState([]);
  const [learningPaths, setLearningPaths] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [assessmentsRes, pathsRes] = await Promise.all([
        axios.get('/api/assessment/history'),
        axios.get('/api/learning-paths')
      ]);
      
      setAssessments(assessmentsRes.data.assessments || []);
      setLearningPaths(pathsRes.data.learning_paths || []);
    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAssessmentComplete = () => {
    loadData(); // Reload data after assessment
  };

  if (loading) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <p>Loading your dashboard...</p>
      </div>
    );
  }

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <div className="header-logo">
          <img src="/learnora_logo.png" alt="Learnora" className="dashboard-logo" />
          <h1>Learnora</h1>
        </div>
        <div className="user-info">
          <span>Welcome, {user.username}!</span>
          <button className="logout-btn" onClick={onLogout}>
            Logout
          </button>
        </div>
      </div>

      <div className="dashboard-content">
        {/* Left Panel - Assessment */}
        <div className="panel">
          <AssessmentPanel 
            assessments={assessments} 
            onAssessmentComplete={handleAssessmentComplete}
          />
        </div>

        {/* Center Panel - Learning Paths */}
        <div className="panel">
          <LearningPaths 
            learningPaths={learningPaths}
            onUpdate={loadData}
          />
        </div>

        {/* Right Panel - Chat */}
        <div className="panel">
          <ChatWindow />
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
