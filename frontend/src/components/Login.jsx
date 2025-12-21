import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import axios from 'axios';
import '../styles/Login.css';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

function Login() {
  const navigate = useNavigate();
  const location = useLocation();
  const [userType, setUserType] = useState('patient'); // 'patient' or 'doctor'
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

  // Check for success message from signup
  useEffect(() => {
    if (location.state?.message) {
      setSuccessMessage(location.state.message);
      // Clear the message after 5 seconds
      setTimeout(() => setSuccessMessage(''), 5000);
    }
  }, [location]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccessMessage('');
    setIsLoading(true);

    try {
      // Call backend login API
      const response = await axios.post(`${API_BASE_URL}/auth/login`, {
        email: formData.email,
        password: formData.password,
        user_type: userType
      });

      if (response.data.success) {
        // Store user data in localStorage
        localStorage.setItem('user_email', response.data.user_data.email);
        localStorage.setItem('user_name', response.data.user_data.name);
        localStorage.setItem('user_type', userType);

        // Navigate based on user type
        if (userType === 'patient') {
          navigate('/patient/dashboard');
        } else {
          navigate('/doctor/dashboard');
        }
      }
    } catch (err) {
      if (err.response?.data?.detail) {
        setError(err.response.data.detail);
      } else {
        setError('Login failed. Please check your credentials.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <div className="login-header">
          <h1>Smart Doctor Assistant</h1>
          <p>AI-Powered Medical Appointment System</p>
        </div>

        <div className="user-type-selector">
          <button
            type="button"
            className={`type-btn ${userType === 'patient' ? 'active' : ''}`}
            onClick={() => setUserType('patient')}
          >
            <span className="icon">👤</span>
            <span>Patient</span>
          </button>
          <button
            type="button"
            className={`type-btn ${userType === 'doctor' ? 'active' : ''}`}
            onClick={() => setUserType('doctor')}
          >
            <span className="icon">🩺</span>
            <span>Doctor</span>
          </button>
        </div>

        <form onSubmit={handleSubmit} className="login-form">
          {successMessage && (
            <div className="success-message" style={{
              padding: '12px',
              background: '#d4edda',
              color: '#155724',
              borderRadius: '8px',
              marginBottom: '15px',
              fontSize: '14px'
            }}>
              {successMessage}
            </div>
          )}

          <div className="form-group">
            <label htmlFor="email">Email Address</label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              placeholder={`Enter your ${userType} email`}
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              type="password"
              id="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              placeholder="Enter your password"
              required
            />
          </div>

          {error && <div className="error-message">{error}</div>}

          <button
            type="submit"
            className="login-btn"
            disabled={isLoading}
          >
            {isLoading ? 'Signing in...' : `Sign in as ${userType === 'patient' ? 'Patient' : 'Doctor'}`}
          </button>

          <div className="form-footer">
            <span>Don't have an account?</span>
            <a href="/signup" className="create-account">Create account</a>
          </div>
        </form>

      </div>
    </div>
  );
}

export default Login;
