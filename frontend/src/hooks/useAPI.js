import { useState, useCallback, useEffect, useMemo } from 'react';
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

/**
 * Custom hook for chat functionality with persistence
 *
 * @param {string} userEmail - REQUIRED: User email for conversation isolation
 * @param {string} initialSessionId - Optional session ID
 */
export const useChat = (userEmail, initialSessionId = null) => {
  // **USER ISOLATION: Validate userEmail is provided**
  if (!userEmail) {
    throw new Error('userEmail is required for conversation isolation');
  }

  // **USER-SCOPED STORAGE KEYS** - Each user gets their own localStorage namespace
  const STORAGE_KEYS = useMemo(() => ({
    MESSAGES: `smart_doctor_messages_${userEmail}`,
    SESSION_ID: `smart_doctor_session_id_${userEmail}`
  }), [userEmail]);

  // **MIGRATION: Clear old global keys on first load**
  // This fixes the shared chat bug by removing old storage
  useEffect(() => {
    const OLD_KEYS = ['smart_doctor_messages', 'smart_doctor_session_id'];
    let cleared = false;
    OLD_KEYS.forEach(key => {
      if (localStorage.getItem(key)) {
        console.warn(`[MIGRATION] Removing old global storage key: ${key}`);
        localStorage.removeItem(key);
        cleared = true;
      }
    });
    if (cleared) {
      console.log('✅ Migration complete - old global keys removed');
    }
  }, []); // Run once on mount

  // Load from localStorage on initial mount (USER-SCOPED)
  const [messages, setMessages] = useState(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEYS.MESSAGES);
      return saved ? JSON.parse(saved) : [];
    } catch (error) {
      console.error('Error loading messages from localStorage:', error);
      return [];
    }
  });

  const [sessionId, setSessionId] = useState(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEYS.SESSION_ID);
      return saved || initialSessionId;
    } catch (error) {
      console.error('Error loading session from localStorage:', error);
      return initialSessionId;
    }
  });

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  // Persist messages to localStorage whenever they change (USER-SCOPED)
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEYS.MESSAGES, JSON.stringify(messages));
    } catch (error) {
      console.error('Error saving messages to localStorage:', error);
    }
  }, [messages, STORAGE_KEYS]);

  // Persist session ID to localStorage whenever it changes (USER-SCOPED)
  useEffect(() => {
    if (sessionId) {
      try {
        localStorage.setItem(STORAGE_KEYS.SESSION_ID, sessionId);
      } catch (error) {
        console.error('Error saving session to localStorage:', error);
      }
    }
  }, [sessionId, STORAGE_KEYS]);

  const addMessage = useCallback((message) => {
    setMessages((prev) => [...prev, message]);
  }, []);

  const sendMessage = useCallback(async (messageText, userType = 'patient') => {
    if (!messageText.trim()) return;

    const userMessage = {
      role: 'user',
      content: messageText,
      timestamp: new Date().toISOString()
    };

    addMessage(userMessage);
    setIsLoading(true);
    setError(null);

    try {
      const response = await axios.post(`${API_BASE_URL}/chat`, {
        session_id: sessionId,
        message: messageText,
        user_type: userType,
        user_email: userEmail  // ← CRITICAL: User isolation
      }, {
        timeout: 60000 // Increase timeout to 60 seconds
      });

      if (!sessionId) {
        setSessionId(response.data.session_id);
      }

      const assistantMessage = {
        role: 'assistant',
        content: response.data.response,
        timestamp: new Date().toISOString(),
        toolCallsMade: response.data.tool_calls_made
      };

      addMessage(assistantMessage);
      return response.data;
    } catch (err) {
      const errorMessage = {
        role: 'assistant',
        content: err.code === 'ECONNABORTED'
          ? 'Request timed out. The AI is taking longer than usual. Please try again or use the direct booking option.'
          : 'Sorry, I encountered an error. Please try again or use the direct booking button.',
        timestamp: new Date().toISOString(),
        isError: true
      };
      addMessage(errorMessage);
      setError(err.message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [sessionId, userEmail, addMessage]);  // ← Added userEmail dependency

  const clearMessages = useCallback(() => {
    setMessages([]);
    setSessionId(null);
    setError(null);
    // Clear from localStorage (USER-SCOPED)
    try {
      localStorage.removeItem(STORAGE_KEYS.MESSAGES);
      localStorage.removeItem(STORAGE_KEYS.SESSION_ID);
    } catch (error) {
      console.error('Error clearing localStorage:', error);
    }
  }, [STORAGE_KEYS]);

  return {
    messages,
    sessionId,
    isLoading,
    error,
    sendMessage,
    addMessage,
    clearMessages
  };
};

/**
 * Custom hook for doctor dashboard
 */
export const useDoctorDashboard = (doctorId) => {
  const [stats, setStats] = useState(null);
  const [appointments, setAppointments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchStats = useCallback(async (startDate, endDate) => {
    if (!doctorId) return;

    setLoading(true);
    setError(null);

    try {
      const response = await axios.post(`${API_BASE_URL}/doctor/stats`, {
        doctor_id: doctorId,
        start_date: startDate,
        end_date: endDate
      });
      setStats(response.data);
      return response.data;
    } catch (err) {
      setError(err.message);
      console.error('Error fetching stats:', err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [doctorId]);

  const fetchAppointments = useCallback(async (startDate, endDate) => {
    if (!doctorId) return;

    setLoading(true);
    setError(null);

    try {
      const response = await axios.get(`${API_BASE_URL}/appointments`, {
        params: {
          doctor_id: doctorId,
          start_date: startDate,
          end_date: endDate
        }
      });
      setAppointments(response.data.appointments);
      return response.data.appointments;
    } catch (err) {
      setError(err.message);
      console.error('Error fetching appointments:', err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [doctorId]);

  const generateReport = useCallback(async (query) => {
    if (!doctorId || !query.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const response = await axios.post(
        `${API_BASE_URL}/doctor/generate-report`,
        null,
        {
          params: {
            doctor_id: doctorId,
            query: query
          }
        }
      );
      return response.data;
    } catch (err) {
      setError(err.message);
      console.error('Error generating report:', err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [doctorId]);

  return {
    stats,
    appointments,
    loading,
    error,
    fetchStats,
    fetchAppointments,
    generateReport
  };
};

/**
 * Custom hook for API data fetching
 */
export const useAPI = (url, options = {}) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await axios.get(`${API_BASE_URL}${url}`, options);
      setData(response.data);
      return response.data;
    } catch (err) {
      setError(err.message);
      console.error(`Error fetching ${url}:`, err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [url, options]);

  return { data, loading, error, fetchData, refetch: fetchData };
};
