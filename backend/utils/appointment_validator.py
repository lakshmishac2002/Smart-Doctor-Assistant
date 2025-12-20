"""
Comprehensive appointment validation logic
Handles doctor availability, date validation, and conflict detection
"""
from datetime import datetime, date, time, timedelta
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session

from db.models import Doctor, Appointment


class AppointmentValidator:
    """Validates appointment bookings against doctor availability and conflicts"""

    # US Federal Holidays (basic list - can be extended)
    HOLIDAYS = [
        (1, 1),   # New Year's Day
        (7, 4),   # Independence Day
        (12, 25), # Christmas
    ]

    @staticmethod
    def validate_date_against_availability(
        appt_date: date,
        doctor: Doctor
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate if appointment date falls on doctor's working day

        Returns:
            (is_valid, error_message)
        """
        # Check if date is in the past
        if appt_date < date.today():
            return False, "Cannot book appointments in the past. Please select a future date."

        # Check if date is too far in the future (max 6 months)
        max_future_date = date.today() + timedelta(days=180)
        if appt_date > max_future_date:
            return False, "Cannot book appointments more than 6 months in advance. Please select an earlier date."

        # Check if it's a holiday
        if (appt_date.month, appt_date.day) in AppointmentValidator.HOLIDAYS:
            holiday_name = AppointmentValidator._get_holiday_name(appt_date)
            return False, f"The clinic is closed on {holiday_name} ({appt_date.strftime('%B %d, %Y')}). Please choose another date."

        # Check if date falls on doctor's working day
        day_name = appt_date.strftime("%A")  # e.g., "Monday"

        if not doctor.available_days or day_name not in doctor.available_days:
            available_days_str = ", ".join(doctor.available_days) if doctor.available_days else "none"
            return False, (
                f"Dr. {doctor.name} is not available on {day_name}s. "
                f"Available days: {available_days_str}. "
                f"Please select a different date."
            )

        return True, None

    @staticmethod
    def validate_time_against_availability(
        appt_time: time,
        doctor: Doctor
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate if appointment time falls within doctor's working hours

        Returns:
            (is_valid, error_message)
        """
        if not doctor.available_start_time or not doctor.available_end_time:
            return False, "Doctor's availability hours are not configured."

        # Convert to comparable format
        start_time = doctor.available_start_time
        end_time = doctor.available_end_time

        if appt_time < start_time or appt_time >= end_time:
            return False, (
                f"The requested time {appt_time.strftime('%I:%M %p')} is outside "
                f"Dr. {doctor.name}'s working hours "
                f"({start_time.strftime('%I:%M %p')} - {end_time.strftime('%I:%M %p')}). "
                f"Please select a time within these hours."
            )

        return True, None

    @staticmethod
    def check_appointment_conflicts(
        doctor_id: int,
        appt_date: date,
        appt_time: time,
        duration_minutes: int,
        db: Session
    ) -> Tuple[bool, Optional[str], Optional[List[Dict]]]:
        """
        Check for appointment conflicts and suggest alternatives

        Returns:
            (has_conflict, error_message, suggested_slots)
        """
        # Check exact time slot
        existing = db.query(Appointment).filter(
            Appointment.doctor_id == doctor_id,
            Appointment.appointment_date == appt_date,
            Appointment.appointment_time == appt_time,
            Appointment.status != 'cancelled'
        ).first()

        if existing:
            # Get patient name for the conflicting appointment
            patient_name = existing.patient.name if existing.patient else "another patient"

            # Find alternative slots
            suggested_slots = AppointmentValidator._find_alternative_slots(
                doctor_id, appt_date, appt_time, duration_minutes, db
            )

            error_msg = (
                f"This time slot ({appt_time.strftime('%I:%M %p')}) is already booked. "
            )

            if suggested_slots:
                slot_times = [slot['time'] for slot in suggested_slots[:3]]
                error_msg += f"Available slots on {appt_date.strftime('%B %d, %Y')}: {', '.join(slot_times)}."
            else:
                error_msg += "No available slots found on this date. Please try another day."

            return True, error_msg, suggested_slots

        # Check for overlapping appointments
        appt_datetime = datetime.combine(appt_date, appt_time)
        appt_end_datetime = appt_datetime + timedelta(minutes=duration_minutes)

        overlapping = db.query(Appointment).filter(
            Appointment.doctor_id == doctor_id,
            Appointment.appointment_date == appt_date,
            Appointment.status != 'cancelled'
        ).all()

        for existing_appt in overlapping:
            existing_datetime = datetime.combine(
                existing_appt.appointment_date,
                existing_appt.appointment_time
            )
            existing_end_datetime = existing_datetime + timedelta(
                minutes=existing_appt.duration_minutes
            )

            # Check if times overlap
            if (appt_datetime < existing_end_datetime and
                appt_end_datetime > existing_datetime):

                suggested_slots = AppointmentValidator._find_alternative_slots(
                    doctor_id, appt_date, appt_time, duration_minutes, db
                )

                error_msg = (
                    f"This time slot overlaps with another appointment "
                    f"({existing_appt.appointment_time.strftime('%I:%M %p')} - "
                    f"{existing_end_datetime.strftime('%I:%M %p')}). "
                )

                if suggested_slots:
                    slot_times = [slot['time'] for slot in suggested_slots[:3]]
                    error_msg += f"Try these times: {', '.join(slot_times)}."

                return True, error_msg, suggested_slots

        return False, None, None

    @staticmethod
    def _find_alternative_slots(
        doctor_id: int,
        appt_date: date,
        requested_time: time,
        duration_minutes: int,
        db: Session,
        num_suggestions: int = 5
    ) -> List[Dict[str, Any]]:
        """Find alternative available time slots"""
        doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
        if not doctor:
            return []

        # Get all appointments for this doctor on this date
        existing_appointments = db.query(Appointment).filter(
            Appointment.doctor_id == doctor_id,
            Appointment.appointment_date == appt_date,
            Appointment.status != 'cancelled'
        ).order_by(Appointment.appointment_time).all()

        # Generate all possible slots
        available_slots = []
        current_time = doctor.available_start_time
        end_time = doctor.available_end_time

        while current_time < end_time:
            slot_datetime = datetime.combine(appt_date, current_time)
            slot_end_datetime = slot_datetime + timedelta(minutes=duration_minutes)

            # Check if this slot conflicts with any existing appointment
            is_available = True
            for existing in existing_appointments:
                existing_datetime = datetime.combine(
                    existing.appointment_date,
                    existing.appointment_time
                )
                existing_end_datetime = existing_datetime + timedelta(
                    minutes=existing.duration_minutes
                )

                if (slot_datetime < existing_end_datetime and
                    slot_end_datetime > existing_datetime):
                    is_available = False
                    break

            if is_available and slot_end_datetime.time() <= end_time:
                available_slots.append({
                    "time": current_time.strftime('%I:%M %p'),
                    "time_24h": current_time.strftime('%H:%M'),
                    "datetime": slot_datetime.isoformat()
                })

            # Move to next slot
            current_time = (slot_datetime + timedelta(minutes=doctor.slot_duration_minutes)).time()

            if len(available_slots) >= num_suggestions:
                break

        return available_slots

    @staticmethod
    def _get_holiday_name(date_obj: date) -> str:
        """Get holiday name for a given date"""
        holiday_map = {
            (1, 1): "New Year's Day",
            (7, 4): "Independence Day",
            (12, 25): "Christmas Day"
        }
        return holiday_map.get((date_obj.month, date_obj.day), "Holiday")

    @staticmethod
    def validate_complete_appointment(
        doctor: Doctor,
        appt_date: date,
        appt_time: time,
        db: Session
    ) -> Dict[str, Any]:
        """
        Comprehensive validation of appointment

        Returns:
            {
                "valid": bool,
                "error": str or None,
                "error_type": str or None,  # 'date', 'time', 'conflict'
                "suggestions": list or None
            }
        """
        # Validate date against availability
        date_valid, date_error = AppointmentValidator.validate_date_against_availability(
            appt_date, doctor
        )

        if not date_valid:
            return {
                "valid": False,
                "error": date_error,
                "error_type": "date",
                "suggestions": None
            }

        # Validate time against availability
        time_valid, time_error = AppointmentValidator.validate_time_against_availability(
            appt_time, doctor
        )

        if not time_valid:
            return {
                "valid": False,
                "error": time_error,
                "error_type": "time",
                "suggestions": None
            }

        # Check for conflicts
        has_conflict, conflict_error, suggestions = AppointmentValidator.check_appointment_conflicts(
            doctor.id,
            appt_date,
            appt_time,
            doctor.slot_duration_minutes,
            db
        )

        if has_conflict:
            return {
                "valid": False,
                "error": conflict_error,
                "error_type": "conflict",
                "suggestions": suggestions
            }

        return {
            "valid": True,
            "error": None,
            "error_type": None,
            "suggestions": None
        }
