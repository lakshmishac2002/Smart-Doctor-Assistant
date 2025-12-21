import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { useApp } from '../context/AppContext';
import { useDoctorDashboard } from '../hooks/useAPI';

function DoctorDashboard() {
  const { doctors } = useApp();
  const [selectedDoctorId, setSelectedDoctorId] = useState(null);
  const [query, setQuery] = useState('');
  const [report, setReport] = useState(null);
  const [dateRange, setDateRange] = useState({
    start: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    end: new Date().toISOString().split('T')[0]
  });

  const {
    stats,
    appointments,
    loading,
    error,
    fetchStats,
    fetchAppointments,
    generateReport
  } = useDoctorDashboard(selectedDoctorId);

  // Set first doctor as selected when doctors load
  useEffect(() => {
    if (doctors.length > 0 && !selectedDoctorId) {
      setSelectedDoctorId(doctors[0].id);
    }
  }, [doctors, selectedDoctorId]);

  // Fetch data when doctor or date range changes
  useEffect(() => {
    if (selectedDoctorId) {
      fetchStats(dateRange.start, dateRange.end);
      fetchAppointments(dateRange.start, dateRange.end);
    }
  }, [selectedDoctorId, dateRange, fetchStats, fetchAppointments]);

  const handleGenerateReport = useCallback(async () => {
    if (!query.trim()) return;

    try {
      const result = await generateReport(query);
      setReport(result);
    } catch (error) {
      console.error('Failed to generate report:', error);
    }
  }, [query, generateReport]);

  const selectedDoctor = useMemo(() => {
    return doctors.find(d => d.id === selectedDoctorId);
  }, [doctors, selectedDoctorId]);

  const quickQueries = useMemo(() => [
    "How many patients visited yesterday?",
    "What are the most common symptoms this week?",
    "Show me today's appointments",
    "Give me a summary of fever cases"
  ], []);

  const handleDateChange = useCallback((field, value) => {
    setDateRange(prev => ({ ...prev, [field]: value }));
  }, []);

  if (doctors.length === 0) {
    return (
      <div className="doctor-dashboard-container">
        <div className="loading-placeholder">Loading doctors...</div>
      </div>
    );
  }

  return (
    <div className="doctor-dashboard-container">
      <div className="dashboard-header">
        <div>
          <h2>Doctor Dashboard</h2>
          <p className="dashboard-subtitle">AI-Powered Analytics & Reports</p>
        </div>
        <div className="doctor-selector">
          <label>Select Doctor:</label>
          <select 
            value={selectedDoctorId || ''} 
            onChange={(e) => setSelectedDoctorId(Number(e.target.value))}
          >
            {doctors.map(doctor => (
              <option key={doctor.id} value={doctor.id}>
                {doctor.name} - {doctor.specialization}
              </option>
            ))}
          </select>
        </div>
      </div>

      {selectedDoctor && (
        <>
          <div className="dashboard-grid">
            {/* Stats Overview */}
            <div className="dashboard-card stats-card">
              <h3>Statistics Overview</h3>
              <div className="date-range-selector">
                <input 
                  type="date" 
                  value={dateRange.start} 
                  onChange={(e) => handleDateChange('start', e.target.value)}
                  max={dateRange.end}
                />
                <span>to</span>
                <input 
                  type="date" 
                  value={dateRange.end} 
                  onChange={(e) => handleDateChange('end', e.target.value)}
                  min={dateRange.start}
                  max={new Date().toISOString().split('T')[0]}
                />
              </div>
              
              {loading && <div className="loading-indicator">Loading stats...</div>}
              
              {error && <div className="error-message">Error: {error}</div>}
              
              {stats && stats.success && (
                <div className="stats-content">
                  <div className="stat-item">
                    <div className="stat-value">{stats.total_appointments}</div>
                    <div className="stat-label">Total Appointments</div>
                  </div>
                  
                  {stats.status_distribution && Object.keys(stats.status_distribution).length > 0 && (
                    <div className="stat-group">
                      <h4>Status Distribution</h4>
                      {Object.entries(stats.status_distribution).map(([status, count]) => (
                        <div key={status} className="stat-row">
                          <span className={`status-badge ${status}`}>{status}</span>
                          <span className="count">{count}</span>
                        </div>
                      ))}
                    </div>
                  )}
                  
                  {stats.symptom_analysis && Object.keys(stats.symptom_analysis).length > 0 && (
                    <div className="stat-group">
                      <h4>Common Symptoms</h4>
                      {Object.entries(stats.symptom_analysis)
                        .sort(([,a], [,b]) => b - a)
                        .slice(0, 5)
                        .map(([symptom, count]) => (
                          <div key={symptom} className="stat-row">
                            <span>{symptom}</span>
                            <span className="count">{count}</span>
                          </div>
                        ))}
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Appointments List */}
            <div className="dashboard-card appointments-card">
              <h3>Recent Appointments</h3>
              
              {loading && <div className="loading-indicator">Loading appointments...</div>}
              
              <div className="appointments-list">
                {appointments && appointments.length > 0 ? (
                  appointments.map(appointment => (
                    <div key={appointment.id} className="appointment-item">
                      <div className="appointment-header">
                        <strong>{appointment.patient_name}</strong>
                        <span className={`status-badge ${appointment.status}`}>
                          {appointment.status}
                        </span>
                      </div>
                      <div className="appointment-details">
                        <div>{appointment.appointment_date}</div>
                        <div>{appointment.appointment_time}</div>
                      </div>
                      {appointment.symptoms && (
                        <div className="appointment-symptoms">
                          {appointment.symptoms}
                        </div>
                      )}
                    </div>
                  ))
                ) : (
                  <p className="no-data">No appointments in selected date range</p>
                )}
              </div>
            </div>
          </div>

          {/* AI Report Generator */}
          <div className="dashboard-card report-generator-card">
            <h3>AI Report Generator</h3>
            <p className="description">
              Ask questions about your appointments and get AI-generated insights using MCP tools
            </p>
            
            <div className="quick-queries">
              <span className="label">Quick queries:</span>
              {quickQueries.map((q, index) => (
                <button
                  key={index}
                  className="quick-query-btn"
                  onClick={() => setQuery(q)}
                  disabled={loading}
                >
                  {q}
                </button>
              ))}
            </div>

            <div className="query-input-section">
              <textarea
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="e.g., 'How many patients with fever did I see this week?'"
                rows={3}
                disabled={loading}
              />
              <button
                onClick={handleGenerateReport}
                disabled={loading || !query.trim()}
                className="generate-btn"
              >
                {loading ? 'Generating...' : 'Generate Report'}
              </button>
            </div>

            {report && (
              <div className="report-result">
                <h4>Report Result</h4>
                <div className="report-content">
                  {report.response}
                </div>
                {report.tool_calls_made > 0 && (
                  <div className="report-meta">
                    Used {report.tool_calls_made} MCP tool{report.tool_calls_made > 1 ? 's' : ''}
                    in {report.iterations} iteration{report.iterations > 1 ? 's' : ''}
                  </div>
                )}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}

export default DoctorDashboard;
