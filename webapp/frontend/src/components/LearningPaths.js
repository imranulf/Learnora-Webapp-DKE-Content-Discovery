import React, { useState } from 'react';
import axios from 'axios';

function LearningPaths({ learningPaths, onUpdate }) {
  const [selectedPath, setSelectedPath] = useState(null);
  const [contentDetails, setContentDetails] = useState([]);
  const [loading, setLoading] = useState(false);

  const handleSelectPath = async (path) => {
    if (selectedPath?.id === path.id) {
      setSelectedPath(null);
      setContentDetails([]);
      return;
    }

    setLoading(true);
    setSelectedPath(path);

    try {
      const response = await axios.get(`/api/learning-paths/${path.id}`);
      setContentDetails(response.data.content_details || []);
    } catch (error) {
      console.error('Error loading path details:', error);
      setContentDetails([]);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateProgress = async (pathId, newProgress) => {
    try {
      await axios.put(`/api/learning-paths/${pathId}/progress`, {
        progress: newProgress
      });
      onUpdate();
    } catch (error) {
      console.error('Error updating progress:', error);
    }
  };

  return (
    <>
      <h3>📚 Your Learning Paths</h3>
      
      {learningPaths.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '40px', color: '#666' }}>
          <p>📝 No learning paths yet.</p>
          <p>Take an assessment to get personalized recommendations!</p>
        </div>
      ) : (
        <>
          {learningPaths.map(path => (
            <div key={path.id}>
              <div 
                className="learning-path" 
                onClick={() => handleSelectPath(path)}
              >
                <h4>{path.title}</h4>
                <p>{path.description}</p>
                <div style={{ 
                  display: 'flex', 
                  justifyContent: 'space-between', 
                  marginTop: '8px',
                  fontSize: '14px'
                }}>
                  <span>⏱️ {path.estimated_time} min</span>
                  <span>{path.progress}% Complete</span>
                </div>
                <div className="progress-bar">
                  <div 
                    className="progress-fill" 
                    style={{ width: `${path.progress}%` }}
                  />
                </div>
              </div>

              {selectedPath?.id === path.id && (
                <div style={{ marginBottom: '20px' }}>
                  {loading ? (
                    <p style={{ textAlign: 'center', padding: '20px' }}>Loading...</p>
                  ) : (
                    <>
                      {contentDetails.map((content, idx) => (
                        <div key={content.id} className="content-item">
                          <h5>{idx + 1}. {content.title}</h5>
                          <p>{content.description}</p>
                          <div style={{ 
                            display: 'flex', 
                            justifyContent: 'space-between',
                            marginBottom: '8px',
                            fontSize: '13px',
                            color: '#666'
                          }}>
                            <span>📊 {content.difficulty}</span>
                            <span>⏱️ {content.duration_minutes} min</span>
                            <span>📄 {content.content_type}</span>
                          </div>
                          <div className="tags">
                            {content.tags?.slice(0, 4).map((tag, i) => (
                              <span key={i} className="tag">{tag}</span>
                            ))}
                          </div>
                          <a 
                            href={content.url} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            style={{ 
                              display: 'inline-block',
                              marginTop: '8px',
                              color: '#667eea',
                              textDecoration: 'none',
                              fontWeight: 600
                            }}
                          >
                            View Resource →
                          </a>
                        </div>
                      ))}
                      
                      <div style={{ marginTop: '16px' }}>
                        <label style={{ 
                          display: 'block', 
                          marginBottom: '8px',
                          fontWeight: 600
                        }}>
                          Update Progress:
                        </label>
                        <input 
                          type="range" 
                          min="0" 
                          max="100" 
                          value={path.progress}
                          onChange={(e) => handleUpdateProgress(path.id, parseInt(e.target.value))}
                          style={{ width: '100%' }}
                        />
                      </div>
                    </>
                  )}
                </div>
              )}
            </div>
          ))}
        </>
      )}
    </>
  );
}

export default LearningPaths;
