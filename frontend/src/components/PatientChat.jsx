import React, { useState, useEffect, useRef, useMemo } from 'react';
import { useApp } from '../context/AppContext';
import { useChat } from '../hooks/useAPI';

function PatientChat() {
  const { doctors, loading: doctorsLoading } = useApp();
  const { messages, isLoading, sendMessage } = useChat();
  const [inputMessage, setInputMessage] = useState('');
  const messagesEndRef = useRef(null);

  // Welcome message
  useEffect(() => {
    if (messages.length === 0) {
      const welcomeMessage = {
        role: 'assistant',
        content: 'Hello! I\'m your Smart Doctor Assistant powered by AI and MCP tools. I can help you:\n\n' +
                 '• Check doctor availability\n' +
                 '• Book appointments\n' +
                 '• Answer questions about doctors and specializations\n\n' +
                 'How can I assist you today?',
        timestamp: new Date().toISOString()
      };
      // We can't call sendMessage here, so we'll handle this differently
      // For now, just show it when component mounts
    }
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;
    
    const messageText = inputMessage;
    setInputMessage('');
    
    try {
      await sendMessage(messageText, 'patient');
    } catch (error) {
      console.error('Failed to send message:', error);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const quickActions = useMemo(() => [
    "Check Dr. Ahuja's availability for tomorrow",
    "Show me all available doctors",
    "Book an appointment with a general physician",
    "I need to see a cardiologist"
  ], []);

  const handleQuickAction = (action) => {
    setInputMessage(action);
  };

  // Group doctors by specialization
  const doctorsBySpecialization = useMemo(() => {
    return doctors.reduce((acc, doctor) => {
      const spec = doctor.specialization;
      if (!acc[spec]) acc[spec] = [];
      acc[spec].push(doctor);
      return acc;
    }, {});
  }, [doctors]);

  return (
    <div className="patient-chat-container">
      <div className="chat-sidebar">
        <div className="sidebar-section">
          <h3>📋 Available Doctors</h3>
          {doctorsLoading ? (
            <div className="loading-placeholder">Loading doctors...</div>
          ) : (
            <div className="doctors-list">
              {Object.entries(doctorsBySpecialization).map(([specialization, docs]) => (
                <div key={specialization} className="specialization-group">
                  <h4 className="specialization-title">{specialization}</h4>
                  {docs.map(doctor => (
                    <div key={doctor.id} className="doctor-card">
                      <div className="doctor-name">{doctor.name}</div>
                      <div className="doctor-availability">
                        {doctor.available_days.slice(0, 3).join(', ')}
                        {doctor.available_days.length > 3 && '...'}
                      </div>
                    </div>
                  ))}
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="sidebar-section">
          <h3>⚡ Quick Actions</h3>
          <div className="quick-actions">
            {quickActions.map((action, index) => (
              <button
                key={index}
                className="quick-action-btn"
                onClick={() => handleQuickAction(action)}
                disabled={isLoading}
              >
                {action}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="chat-main">
        <div className="messages-container">
          {messages.length === 0 && (
            <div className="welcome-message">
              <div className="message assistant">
                <div className="message-header">
                  <span className="role">🤖 Assistant</span>
                </div>
                <div className="message-content">
                  Hello! I'm your Smart Doctor Assistant powered by AI and MCP tools. I can help you:
                  {'\n\n'}
                  • Check doctor availability
                  {'\n'}
                  • Book appointments
                  {'\n'}
                  • Answer questions about doctors and specializations
                  {'\n\n'}
                  How can I assist you today?
                </div>
              </div>
            </div>
          )}
          
          {messages.map((message, index) => (
            <div key={index} className={`message ${message.role}`}>
              <div className="message-header">
                <span className="role">
                  {message.role === 'user' ? '👤 You' : '🤖 Assistant'}
                </span>
                <span className="timestamp">
                  {formatTimestamp(message.timestamp)}
                </span>
              </div>
              <div className={`message-content ${message.isError ? 'error' : ''}`}>
                {message.content}
              </div>
              {message.toolCallsMade > 0 && (
                <div className="tool-indicator">
                  🔧 Used {message.toolCallsMade} MCP tool{message.toolCallsMade > 1 ? 's' : ''}
                </div>
              )}
            </div>
          ))}
          
          {isLoading && (
            <div className="message assistant">
              <div className="message-header">
                <span className="role">🤖 Assistant</span>
              </div>
              <div className="message-content loading">
                <div className="loading-dots">
                  <span>.</span><span>.</span><span>.</span>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="input-container">
          <textarea
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type your message... (e.g., 'I want to book an appointment with Dr. Ahuja tomorrow')"
            disabled={isLoading}
            rows={3}
          />
          <button 
            onClick={handleSendMessage} 
            disabled={isLoading || !inputMessage.trim()}
            className="send-button"
          >
            {isLoading ? '⏳ Sending...' : '📤 Send'}
          </button>
        </div>
      </div>
    </div>
  );
}

export default PatientChat;
