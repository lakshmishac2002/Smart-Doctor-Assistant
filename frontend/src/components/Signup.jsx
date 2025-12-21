import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import '../styles/Login.css';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

function Signup() {
  const navigate = useNavigate();
  const [userType, setUserType] = useState('patient');
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    confirmPassword: '',
    phone: '',
    specialization: '' // Only for doctors
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    // Validation
    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    if (formData.password.length < 6) {
      setError('Password must be at least 6 characters long');
      return;
    }

    if (userType === 'doctor' && !formData.specialization) {
      setError('Specialization is required for doctors');
      return;
    }

    setIsLoading(true);

    try {
      // Call backend signup API
      const response = await axios.post(`${API_BASE_URL}/auth/signup`, {
        name: formData.name,
        email: formData.email,
        password: formData.password,
        phone: formData.phone,
        user_type: userType,
        specialization: userType === 'doctor' ? formData.specialization : null
      });

      if (response.data.success) {
        // Navigate to login page with success message
        navigate('/login', {
          state: {
            message: 'Account created successfully! Please login.'
          }
        });
      }
    } catch (err) {
      if (err.response?.data?.detail) {
        setError(err.response.data.detail);
      } else {
        setError('Registration failed. Please try again.');
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
          <h1>Create Account</h1>
          <p>Join Smart Doctor Assistant</p>
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
            <label htmlFor="name">Full Name</label>
            <input
              type="text"
              id="name"
              name="name"
              value={formData.name}
              onChange={handleChange}
              placeholder="Enter your full name"
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="email">Email Address</label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              placeholder="Enter your email"
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="phone">Phone Number</label>
            <input
              type="tel"
              id="phone"
              name="phone"
              value={formData.phone}
              onChange={handleChange}
              placeholder="Enter your phone number"
              required
            />
          </div>

          {userType === 'doctor' && (
            <div className="form-group">
              <label htmlFor="specialization">Specialization</label>
              <input
                type="text"
                id="specialization"
                name="specialization"
                value={formData.specialization}
                onChange={handleChange}
                placeholder="e.g., Cardiology, Neurology"
                required
              />
            </div>
          )}

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              type="password"
              id="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              placeholder="Create a password (min 6 characters)"
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="confirmPassword">Confirm Password</label>
            <input
              type="password"
              id="confirmPassword"
              name="confirmPassword"
              value={formData.confirmPassword}
              onChange={handleChange}
              placeholder="Re-enter your password"
              required
            />
          </div>

          {error && <div className="error-message">{error}</div>}

          <button
            type="submit"
            className="login-btn"
            disabled={isLoading}
          >
            {isLoading ? 'Creating account...' : 'Create Account'}
          </button>

          <div className="form-footer">
            <span>Already have an account?</span>
            <a href="/login" className="create-account">Sign in</a>
          </div>
        </form>

      </div>
    </div>
  );
}

export default Signup;
