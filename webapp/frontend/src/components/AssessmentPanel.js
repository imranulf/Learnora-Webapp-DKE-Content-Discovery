import React, { useState } from 'react';
import axios from 'axios';

function AssessmentPanel({ assessments, onAssessmentComplete }) {
  const [loading, setLoading] = useState(false);
  const [assessmentResult, setAssessmentResult] = useState(null);

  const handleStartAssessment = async () => {
    setLoading(true);
    setAssessmentResult(null);

    try {
      const response = await axios.post('/api/assessment/start');
      setAssessmentResult(response.data.assessment);
      onAssessmentComplete();
    } catch (error) {
      console.error('Assessment error:', error);
      alert('Assessment failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const latestAssessment = assessments[0];

  return (
    <>
      <h3>📊 Knowledge Assessment</h3>
      
      <button 
        className="assessment-btn"
        onClick={handleStartAssessment}
        disabled={loading}
      >
        {loading ? '⏳ Running Assessment...' : '🎯 Start New Assessment'}
      </button>

      {assessmentResult && (
        <div style={{ 
          background: '#f0f7ff', 
          padding: '20px', 
          borderRadius: '12px',
          marginBottom: '20px'
        }}>
          <h4 style={{ marginBottom: '12px', color: '#333' }}>
            ✅ Assessment Complete!
          </h4>
          <div className="mastery-item">
            <span>Ability Score (θ):</span>
            <span className="mastery-score">
              {assessmentResult.theta?.toFixed(2) || 'N/A'}
            </span>
          </div>
          <p style={{ 
            marginTop: '12px', 
            fontSize: '14px',
            color: '#666'
          }}>
            📚 New learning path created! Check your Learning Paths panel.
          </p>
        </div>
      )}

      {latestAssessment && (
        <>
          <h4 style={{ marginTop: '24px', marginBottom: '16px' }}>
            Latest Mastery Levels
          </h4>
          <div>
            {Object.entries(latestAssessment.mastery_scores || {}).map(([skill, score]) => (
              <div key={skill} className="mastery-item">
                <span className="mastery-skill">
                  {skill.charAt(0).toUpperCase() + skill.slice(1)}
                </span>
                <span className="mastery-score">
                  {(score * 100).toFixed(0)}%
                </span>
              </div>
            ))}
          </div>

          <h4 style={{ marginTop: '24px', marginBottom: '16px' }}>
            Learning Gaps
          </h4>
          {latestAssessment.learning_gaps?.length > 0 ? (
            latestAssessment.learning_gaps.map((gap, idx) => (
              <div 
                key={idx} 
                style={{
                  background: gap.priority === 'high' ? '#fee' : '#fef9e7',
                  padding: '12px',
                  borderRadius: '8px',
                  marginBottom: '8px',
                  fontSize: '14px'
                }}
              >
                <div style={{ fontWeight: 600, marginBottom: '4px' }}>
                  {gap.skill} - {gap.priority.toUpperCase()}
                </div>
                <div style={{ color: '#666' }}>
                  Mastery: {(gap.mastery_level * 100).toFixed(0)}% | 
                  Level: {gap.recommended_difficulty}
                </div>
              </div>
            ))
          ) : (
            <p style={{ color: '#666', fontSize: '14px' }}>
              No gaps identified. Great job!
            </p>
          )}
        </>
      )}

      {!latestAssessment && !assessmentResult && (
        <div style={{ 
          textAlign: 'center', 
          padding: '40px 20px',
          color: '#666'
        }}>
          <p>📝 Take your first assessment to get started!</p>
        </div>
      )}
    </>
  );
}

export default AssessmentPanel;
