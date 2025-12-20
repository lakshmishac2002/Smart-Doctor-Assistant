import React, { useState, useMemo, useCallback, useEffect } from "react";
import { useApp } from "../context/AppContext";
import { useChat } from "../hooks/useAPI";
import Navbar from "./Navbar";
import AppointmentModal from "./AppointmentModal";
import "../styles/PatientDashboard.css";

function PatientDashboard() {
  const { doctors, loading: doctorsLoading, error: doctorsError, userEmail } = useApp();

  // **USER ISOLATION: Pass userEmail to useChat**
  const { messages, isLoading, sendMessage, clearMessages, error: chatError } = useChat(userEmail);
  const [inputMessage, setInputMessage] = useState("");
  const [selectedDoctor, setSelectedDoctor] = useState(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [filterSpec, setFilterSpec] = useState("all");
  const [showBookingModal, setShowBookingModal] = useState(false);
  const [bookingDoctor, setBookingDoctor] = useState(null);
  const [bookingSuccess, setBookingSuccess] = useState(null);
  const [error, setError] = useState(null);
  const [retryCount, setRetryCount] = useState(0);

  // Filter doctors
  const filteredDoctors = useMemo(() => {
    let filtered = doctors;

    if (searchTerm) {
      filtered = filtered.filter(
        (doc) =>
          doc.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
          doc.specialization.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    if (filterSpec !== "all") {
      filtered = filtered.filter((doc) => doc.specialization === filterSpec);
    }

    return filtered;
  }, [doctors, searchTerm, filterSpec]);

  // Get unique specializations
  const specializations = useMemo(() => {
    return [...new Set(doctors.map((doc) => doc.specialization))];
  }, [doctors]);

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const messageText = inputMessage;
    setInputMessage("");

    try {
      await sendMessage(messageText, "patient");
    } catch (error) {
      console.error("Failed to send message:", error);
    }
  };

  const handleBookAppointment = (doctor) => {
    setBookingDoctor(doctor);
    setShowBookingModal(true);
  };

  const handleBookingSuccess = (result) => {
    setShowBookingModal(false);
    setBookingSuccess(result);
    // Auto-hide success message after 5 seconds
    setTimeout(() => setBookingSuccess(null), 5000);
  };

  return (
    <>
      <Navbar userType="patient" />

      {/* Success Message */}
      {bookingSuccess && (
        <div className="success-banner">
          <div className="success-content">
            <span className="success-icon">✓</span>
            <div>
              <strong>Appointment Booked Successfully!</strong>
              <p>
                Confirmation email has been sent to{" "}
                {bookingSuccess.patient_email}
              </p>
            </div>
            <button
              className="close-success"
              onClick={() => setBookingSuccess(null)}
            >
              ×
            </button>
          </div>
        </div>
      )}

      {/* Appointment Booking Modal */}
      {showBookingModal && bookingDoctor && (
        <AppointmentModal
          doctor={bookingDoctor}
          onClose={() => setShowBookingModal(false)}
          onSuccess={handleBookingSuccess}
        />
      )}

      <div className="patient-dashboard">
        {/* Sidebar - Doctors List */}
        <aside className="doctors-sidebar">
          <div className="sidebar-header">
            <h2>Available Doctors</h2>
            <span className="count">
              {filteredDoctors.length}{" "}
              {filteredDoctors.length === 1 ? "doctor" : "doctors"}
            </span>
          </div>

          <div className="search-filters">
            <input
              type="text"
              placeholder="Search doctors..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="search-input"
            />

            <select
              value={filterSpec}
              onChange={(e) => setFilterSpec(e.target.value)}
              className="filter-select"
            >
              <option value="all">All Specializations</option>
              {specializations.map((spec) => (
                <option key={spec} value={spec}>
                  {spec}
                </option>
              ))}
            </select>
          </div>

          {doctorsLoading ? (
            <div className="loading-state">
              <div className="spinner"></div>
              <p>Loading doctors...</p>
            </div>
          ) : filteredDoctors.length === 0 ? (
            <div className="empty-state">
              <p>No doctors found</p>
            </div>
          ) : (
            <div className="doctors-grid">
              {filteredDoctors.map((doctor) => (
                <div
                  key={doctor.id}
                  className={`doctor-card ${
                    selectedDoctor?.id === doctor.id ? "selected" : ""
                  }`}
                  onClick={() => setSelectedDoctor(doctor)}
                >
                  <div className="doctor-avatar">{doctor.name.charAt(0)}</div>
                  <div className="doctor-info">
                    <h3>{doctor.name}</h3>
                    <p className="specialization">{doctor.specialization}</p>
                    <div className="availability">
                      <span className="label">Available:</span>
                      <span className="days">
                        {doctor.available_days?.slice(0, 3).join(", ") || "N/A"}
                        {doctor.available_days?.length > 3 && "..."}
                      </span>
                    </div>
                    <button
                      className="book-btn"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleBookAppointment(doctor);
                      }}
                    >
                      Book Appointment
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </aside>

        {/* Main Chat Area */}
        <main className="chat-area">
          <div className="chat-header">
            <div>
              <h2>AI Assistant</h2>
              <p>Ask me anything about appointments and doctors</p>
            </div>
            {messages.length > 0 && (
              <button
                className="clear-chat-btn"
                onClick={clearMessages}
                title="Clear chat history"
              >
                Clear Chat
              </button>
            )}
          </div>

          <div className="messages-container">
            {messages.length === 0 && (
              <div className="welcome-card">
                <h3>Welcome to Smart Doctor Assistant</h3>
                <p>I can help you with:</p>
                <ul>
                  <li>Checking doctor availability</li>
                  <li>Booking appointments</li>
                  <li>Finding specialists</li>
                  <li>Rescheduling appointments</li>
                </ul>
                <p className="tip">
                  Try: "Show me available cardiologists" or "Book appointment
                  with Dr. Ahuja"
                </p>
              </div>
            )}

            {messages.map((message, index) => (
              <div key={index} className={`message ${message.role}`}>
                <div className="message-avatar">
                  {message.role === "user" ? "You" : "AI"}
                </div>
                <div className="message-bubble">
                  <div className="message-content">{message.content}</div>
                  {message.toolCallsMade > 0 && (
                    <div className="tool-badge">
                      Used {message.toolCallsMade} tool
                      {message.toolCallsMade > 1 ? "s" : ""}
                    </div>
                  )}
                  <div className="message-time">
                    {new Date(message.timestamp).toLocaleTimeString("en-US", {
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </div>
                </div>
              </div>
            ))}

            {isLoading && (
              <div className="message assistant">
                <div className="message-avatar">AI</div>
                <div className="message-bubble loading">
                  <div className="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                </div>
              </div>
            )}
          </div>

          <div className="input-area">
            <textarea
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSendMessage();
                }
              }}
              placeholder="Type your message here... (e.g., 'I need to see a cardiologist tomorrow')"
              disabled={isLoading}
              rows={2}
            />
            <button
              onClick={handleSendMessage}
              disabled={isLoading || !inputMessage.trim()}
              className="send-btn"
            >
              {isLoading ? "Sending..." : "Send"}
            </button>
          </div>
        </main>

        {/* Selected Doctor Info Panel */}
        {selectedDoctor && (
          <aside className="doctor-details-panel">
            <div className="panel-header">
              <h3>Doctor Details</h3>
              <button
                className="close-btn"
                onClick={() => setSelectedDoctor(null)}
              >
                ×
              </button>
            </div>

            <div className="doctor-profile">
              <div className="profile-avatar">
                {selectedDoctor.name.charAt(0)}
              </div>
              <h2>{selectedDoctor.name}</h2>
              <p className="spec-badge">{selectedDoctor.specialization}</p>
            </div>

            <div className="detail-section">
              <h4>Contact Information</h4>
              <p>Email: {selectedDoctor.email || "Not available"}</p>
              <p>Phone: {selectedDoctor.phone || "Not available"}</p>
            </div>

            <div className="detail-section">
              <h4>Availability</h4>
              <div className="days-list">
                {selectedDoctor.available_days?.map((day, idx) => (
                  <span key={idx} className="day-badge">
                    {day}
                  </span>
                )) || <p>No availability info</p>}
              </div>
            </div>

            <div className="detail-section">
              <h4>Working Hours</h4>
              <p>{selectedDoctor.working_hours || "9:00 AM - 5:00 PM"}</p>
            </div>

            <button
              className="primary-btn"
              onClick={() => handleBookAppointment(selectedDoctor)}
            >
              Book Appointment
            </button>
          </aside>
        )}
      </div>
    </>
  );
}

export default PatientDashboard;
