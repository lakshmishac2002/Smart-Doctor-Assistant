import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';

const AppContext = createContext();

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

export const AppProvider = ({ children }) => {
  const [doctors, setDoctors] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // **USER ISOLATION: Get or create unique user identifier**
  const [userEmail, setUserEmail] = useState(() => {
    // Try to get from localStorage
    const stored = localStorage.getItem('smart_doctor_user_email');
    if (stored) return stored;

    // Generate unique identifier (in real app, this would be from auth)
    // For demo: use timestamp + random
    const uniqueEmail = `patient_${Date.now()}_${Math.random().toString(36).substr(2, 9)}@demo.local`;
    localStorage.setItem('smart_doctor_user_email', uniqueEmail);
    return uniqueEmail;
  });

  // Fetch doctors on mount
  useEffect(() => {
    fetchDoctors();
  }, []);

  const fetchDoctors = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_BASE_URL}/doctors`);
      setDoctors(response.data.doctors);
      setError(null);
    } catch (err) {
      setError('Failed to fetch doctors');
      console.error('Error fetching doctors:', err);
    } finally {
      setLoading(false);
    }
  };

  const value = {
    doctors,
    loading,
    error,
    fetchDoctors,
    API_BASE_URL,
    userEmail,  // ← USER ISOLATION: Expose to components
    setUserEmail
  };

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
};

export const useApp = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within AppProvider');
  }
  return context;
};
