import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';

function ChatWindow() {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    loadChatHistory();
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const loadChatHistory = async () => {
    try {
      const response = await axios.get('/api/chat/history');
      const history = response.data.messages || [];
      
      // Convert to chat format
      const formattedMessages = [];
      history.forEach(msg => {
        formattedMessages.push({ text: msg.message, sender: 'user' });
        formattedMessages.push({ text: msg.response, sender: 'bot' });
      });
      
      setMessages(formattedMessages);
    } catch (error) {
      console.error('Error loading chat history:', error);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSend = async () => {
    if (!inputMessage.trim() || loading) return;

    const userMessage = inputMessage.trim();
    setInputMessage('');
    setLoading(true);

    // Add user message immediately
    setMessages(prev => [...prev, { text: userMessage, sender: 'user' }]);

    try {
      const response = await axios.post('/api/chat', { message: userMessage });
      
      // Add bot response
      setMessages(prev => [...prev, { 
        text: response.data.response, 
        sender: 'bot' 
      }]);
    } catch (error) {
      console.error('Chat error:', error);
      setMessages(prev => [...prev, { 
        text: 'Sorry, I encountered an error. Please try again.', 
        sender: 'bot' 
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <>
      <h3>💬 AI Learning Assistant</h3>
      <div className="chat-container">
        <div className="chat-messages">
          {messages.length === 0 && (
            <div className="chat-message bot">
              <p>👋 Hi! I'm your AI learning assistant. Ask me anything about your learning journey!</p>
            </div>
          )}
          
          {messages.map((msg, index) => (
            <div key={index} className={`chat-message ${msg.sender}`}>
              {msg.text}
            </div>
          ))}
          
          {loading && (
            <div className="chat-message bot">
              <em>Typing...</em>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        <div className="chat-input-container">
          <input
            type="text"
            className="chat-input"
            placeholder="Ask me anything..."
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            disabled={loading}
          />
          <button 
            className="chat-send-btn" 
            onClick={handleSend}
            disabled={loading || !inputMessage.trim()}
          >
            Send
          </button>
        </div>
      </div>
    </>
  );
}

export default ChatWindow;
