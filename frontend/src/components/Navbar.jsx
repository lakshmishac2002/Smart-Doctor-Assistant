import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import '../styles/Navbar.css';

function Navbar({ userType }) {
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    navigate('/login');
  };

  const isLoginPage = location.pathname === '/' || location.pathname === '/login';

  if (isLoginPage) {
    return null; // Don't show navbar on login page
  }

  return (
    <nav className="app-navbar">
      <div className="navbar-content">
        <div className="navbar-brand" onClick={() => navigate('/')}>
          <div className="brand-icon">
            <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
              <rect width="32" height="32" rx="8" fill="url(#gradient)" />
              <path d="M16 8L20 12H18V20H14V12H12L16 8Z" fill="white" />
              <path d="M10 20H22V22H10V20Z" fill="white" />
              <defs>
                <linearGradient id="gradient" x1="0" y1="0" x2="32" y2="32">
                  <stop offset="0%" stopColor="#667eea" />
                  <stop offset="100%" stopColor="#764ba2" />
                </linearGradient>
              </defs>
            </svg>
          </div>
          <span className="brand-name">Smart Doctor Assistant</span>
        </div>

        <div className="navbar-actions">
          {userType && (
            <div className="user-badge">
              <span className="user-type">{userType === 'patient' ? 'Patient' : 'Doctor'}</span>
            </div>
          )}
          <button className="logout-btn" onClick={handleLogout}>
            Logout
          </button>
        </div>
      </div>
    </nav>
  );
}

export default Navbar;
