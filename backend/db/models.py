from sqlalchemy import Column, Integer, String, Date, Time, Text, ARRAY, ForeignKey, TIMESTAMP, CheckConstraint, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()

class Doctor(Base):
    __tablename__ = "doctors"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    specialization = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone = Column(String(20))
    available_days = Column(ARRAY(String))  # ['Monday', 'Tuesday', ...]
    available_start_time = Column(Time, nullable=False)
    available_end_time = Column(Time, nullable=False)
    slot_duration_minutes = Column(Integer, default=30)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    appointments = relationship("Appointment", back_populates="doctor")
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "specialization": self.specialization,
            "email": self.email,
            "phone": self.phone,
            "available_days": self.available_days,
            "available_start_time": str(self.available_start_time),
            "available_end_time": str(self.available_end_time),
            "slot_duration_minutes": self.slot_duration_minutes
        }


class Patient(Base):
    __tablename__ = "patients"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone = Column(String(20))
    date_of_birth = Column(Date)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    appointments = relationship("Appointment", back_populates="patient")
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "date_of_birth": str(self.date_of_birth) if self.date_of_birth else None
        }


class Appointment(Base):
    __tablename__ = "appointments"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("doctors.id", ondelete="CASCADE"), nullable=False)
    appointment_date = Column(Date, nullable=False, index=True)
    appointment_time = Column(Time, nullable=False)
    duration_minutes = Column(Integer, default=30)
    status = Column(String(50), default="scheduled", index=True)
    symptoms = Column(Text)
    diagnosis = Column(Text)
    notes = Column(Text)
    google_calendar_event_id = Column(String(255))
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    patient = relationship("Patient", back_populates="appointments")
    doctor = relationship("Doctor", back_populates="appointments")
    
    def to_dict(self):
        return {
            "id": self.id,
            "patient_id": self.patient_id,
            "doctor_id": self.doctor_id,
            "patient_name": self.patient.name if self.patient else None,
            "doctor_name": self.doctor.name if self.doctor else None,
            "appointment_date": str(self.appointment_date),
            "appointment_time": str(self.appointment_time),
            "duration_minutes": self.duration_minutes,
            "status": self.status,
            "symptoms": self.symptoms,
            "diagnosis": self.diagnosis,
            "notes": self.notes,
            "google_calendar_event_id": self.google_calendar_event_id
        }


class ConversationContext(Base):
    """
    Stores conversation context for AI assistant
    Enables memory across sessions for personalized interactions
    """
    __tablename__ = "conversation_contexts"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), unique=True, nullable=False, index=True)
    patient_email = Column(String(255), index=True)  # Optional patient identifier

    # Context data stored as JSON
    context_data = Column(JSON, default={})
    # Example structure:
    # {
    #   "selected_doctor": {"id": 1, "name": "Dr. Smith", "specialization": "Cardiology"},
    #   "attempted_dates": ["2025-12-21", "2025-12-22"],
    #   "last_rejection_reason": "Doctor not available on Saturdays",
    #   "booking_preferences": {"preferred_time": "morning", "recurring": false},
    #   "last_successful_booking": {"appointment_id": 123, "date": "2025-12-25"},
    #   "conversation_summary": "User wants to book cardiologist for chest pain"
    # }

    last_message = Column(Text)  # Last user message
    last_response = Column(Text)  # Last AI response
    message_count = Column(Integer, default=0)

    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    expires_at = Column(TIMESTAMP)  # Session expiry (e.g., 24 hours)

    def to_dict(self):
        return {
            "id": self.id,
            "session_id": self.session_id,
            "patient_email": self.patient_email,
            "context_data": self.context_data,
            "last_message": self.last_message,
            "last_response": self.last_response,
            "message_count": self.message_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None
        }

    def get_context_summary(self) -> str:
        """Generate a human-readable summary of the conversation context"""
        if not self.context_data:
            return "New conversation"

        summary_parts = []

        if "selected_doctor" in self.context_data:
            doctor = self.context_data["selected_doctor"]
            summary_parts.append(f"Interested in {doctor.get('name', 'a doctor')}")

        if "attempted_dates" in self.context_data and self.context_data["attempted_dates"]:
            dates = ", ".join(self.context_data["attempted_dates"][-3:])  # Last 3 dates
            summary_parts.append(f"Tried dates: {dates}")

        if "last_rejection_reason" in self.context_data:
            summary_parts.append(f"Issue: {self.context_data['last_rejection_reason']}")

        if "last_successful_booking" in self.context_data:
            booking = self.context_data["last_successful_booking"]
            summary_parts.append(f"Last booked: Appt #{booking.get('appointment_id')}")

        return " | ".join(summary_parts) if summary_parts else "Ongoing conversation"
