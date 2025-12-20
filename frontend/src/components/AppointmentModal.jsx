import React, { useState } from 'react';
import axios from 'axios';
import '../styles/AppointmentModal.css';

function AppointmentModal({ doctor, onClose, onSuccess }) {
  const [formData, setFormData] = useState({
    patientName: '',
    patientEmail: '',
    appointmentDate: '',
    appointmentTime: '',
    symptoms: ''
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');

  const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setIsSubmitting(true);

    try {
      const response = await axios.post(`${API_BASE_URL}/appointments`, {
        patient_name: formData.patientName,
        patient_email: formData.patientEmail,
        doctor_id: doctor.id,
        appointment_date: formData.appointmentDate,
        appointment_time: formData.appointmentTime,
        symptoms: formData.symptoms || 'General checkup'
      });

      if (response.data.success) {
        onSuccess(response.data);
      } else {
        setError(response.data.error || 'Failed to book appointment');
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to book appointment. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  // Get min date (today)
  const today = new Date().toISOString().split('T')[0];

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Book Appointment</h2>
          <button className="close-modal-btn" onClick={onClose}>×</button>
        </div>

        <div className="doctor-info-bar">
          <div className="doctor-avatar-small">
            {doctor.name.charAt(0)}
          </div>
          <div>
            <h3>{doctor.name}</h3>
            <p>{doctor.specialization}</p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="appointment-form">
          <div className="form-row">
            <div className="form-field">
              <label htmlFor="patientName">Your Name *</label>
              <input
                type="text"
                id="patientName"
                name="patientName"
                value={formData.patientName}
                onChange={handleChange}
                required
                placeholder="John Doe"
              />
            </div>

            <div className="form-field">
              <label htmlFor="patientEmail">Your Email *</label>
              <input
                type="email"
                id="patientEmail"
                name="patientEmail"
                value={formData.patientEmail}
                onChange={handleChange}
                required
                placeholder="john@example.com"
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-field">
              <label htmlFor="appointmentDate">Preferred Date *</label>
              <input
                type="date"
                id="appointmentDate"
                name="appointmentDate"
                value={formData.appointmentDate}
                onChange={handleChange}
                min={today}
                required
              />
              <small>Available: {doctor.available_days?.join(', ')}</small>
            </div>

            <div className="form-field">
              <label htmlFor="appointmentTime">Preferred Time *</label>
              <input
                type="time"
                id="appointmentTime"
                name="appointmentTime"
                value={formData.appointmentTime}
                onChange={handleChange}
                required
              />
              <small>Hours: {doctor.available_start_time} - {doctor.available_end_time}</small>
            </div>
          </div>

          <div className="form-field">
            <label htmlFor="symptoms">Reason for Visit (Optional)</label>
            <textarea
              id="symptoms"
              name="symptoms"
              value={formData.symptoms}
              onChange={handleChange}
              rows={3}
              placeholder="Describe your symptoms or reason for visit..."
            />
          </div>

          {error && (
            <div className="error-box">
              {error}
            </div>
          )}

          <div className="modal-actions">
            <button
              type="button"
              className="btn-secondary"
              onClick={onClose}
              disabled={isSubmitting}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn-primary"
              disabled={isSubmitting}
            >
              {isSubmitting ? 'Booking...' : 'Confirm Booking'}
            </button>
          </div>
        </form>

        <div className="booking-note">
          <p>Note: You will receive a confirmation email once the appointment is booked.</p>
        </div>
      </div>
    </div>
  );
}

export default AppointmentModal;
