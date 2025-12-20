import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import '../styles/Login.css';

function Login() {
  const navigate = useNavigate();
  const [userType, setUserType] = useState('patient'); // 'patient' or 'doctor'
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      // For now, simulate login (you can add actual authentication later)
      await new Promise(resolve => setTimeout(resolve, 1000));

      // Navigate based on user type
      if (userType === 'patient') {
        navigate('/patient/dashboard');
      } else {
        navigate('/doctor/dashboard');
      }
    } catch (err) {
      setError('Login failed. Please check your credentials.');
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
            <a href="#" className="forgot-password">Forgot password?</a>
            <span className="separator">|</span>
            <a href="#" className="create-account">Create account</a>
          </div>
        </form>

        <div className="features-info">
          <h3>Features</h3>
          <ul>
            <li>AI-powered appointment scheduling</li>
            <li>Real-time doctor availability</li>
            <li>Email notifications</li>
            <li>Secure and FREE to use</li>
          </ul>
        </div>
      </div>
    </div>
  );
}

export default Login;
