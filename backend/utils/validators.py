"""
Production-grade input validation utilities
"""
import re
from typing import Optional
from datetime import datetime, date, timedelta

class ValidationError(Exception):
    """Custom validation error"""
    pass

class InputValidator:
    """Production-grade input validation"""

    @staticmethod
    def validate_email(email: str) -> str:
        """Validate and normalize email"""
        if not email or not isinstance(email, str):
            raise ValidationError("Email is required")

        email = email.strip().lower()

        if len(email) > 254:
            raise ValidationError("Email is too long")

        # Basic email regex
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            raise ValidationError("Invalid email format")

        return email

    @staticmethod
    def validate_name(name: str, field_name: str = "Name") -> str:
        """Validate person name"""
        if not name or not isinstance(name, str):
            raise ValidationError(f"{field_name} is required")

        name = name.strip()

        if len(name) < 2:
            raise ValidationError(f"{field_name} must be at least 2 characters")

        if len(name) > 100:
            raise ValidationError(f"{field_name} must be less than 100 characters")

        # Allow letters, spaces, hyphens, apostrophes, dots
        if not re.match(r"^[a-zA-Z\s\-'.]+$", name):
            raise ValidationError(f"{field_name} contains invalid characters")

        return name

    @staticmethod
    def validate_phone(phone: str) -> str:
        """Validate phone number"""
        if not phone or not isinstance(phone, str):
            raise ValidationError("Phone number is required")

        # Remove common formatting
        cleaned = re.sub(r'[\s\-\(\)\+]', '', phone)

        # Should be 10-15 digits
        if not re.match(r'^\d{10,15}$', cleaned):
            raise ValidationError("Phone number must be 10-15 digits")

        return phone.strip()

    @staticmethod
    def validate_date(date_str: str) -> date:
        """Validate appointment date"""
        if not date_str or not isinstance(date_str, str):
            raise ValidationError("Date is required")

        try:
            appt_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            raise ValidationError("Invalid date format. Use YYYY-MM-DD")

        if appt_date < date.today():
            raise ValidationError("Appointment date cannot be in the past")

        # Max 6 months in advance
        max_date = date.today() + timedelta(days=180)
        if appt_date > max_date:
            raise ValidationError("Cannot book more than 6 months in advance")

        return appt_date

    @staticmethod
    def validate_time(time_str: str) -> str:
        """Validate appointment time"""
        if not time_str or not isinstance(time_str, str):
            raise ValidationError("Time is required")

        try:
            time_obj = datetime.strptime(time_str, "%H:%M").time()
        except ValueError:
            raise ValidationError("Invalid time format. Use HH:MM (24-hour)")

        # Business hours: 8 AM to 6 PM
        if time_obj.hour < 8 or time_obj.hour >= 18:
            raise ValidationError("Appointments only available 8:00 AM - 6:00 PM")

        return time_str

    @staticmethod
    def sanitize_text(text: str, max_length: int = 500) -> str:
        """Sanitize text input (symptoms, notes, etc.)"""
        if not text:
            return ""

        if not isinstance(text, str):
            text = str(text)

        text = text.strip()

        if len(text) > max_length:
            raise ValidationError(f"Text exceeds maximum length of {max_length}")

        # Remove control characters except newlines and tabs
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)

        # Escape potential HTML/script tags
        text = text.replace('<', '&lt;').replace('>', '&gt;')

        return text

    @staticmethod
    def validate_id(id_value: any, field_name: str = "ID") -> int:
        """Validate database ID"""
        try:
            id_int = int(id_value)
            if id_int < 1:
                raise ValidationError(f"{field_name} must be positive")
            return id_int
        except (ValueError, TypeError):
            raise ValidationError(f"Invalid {field_name}")

    @staticmethod
    def validate_specialization(spec: str) -> str:
        """Validate doctor specialization"""
        if not spec or not isinstance(spec, str):
            raise ValidationError("Specialization is required")

        spec = spec.strip()

        valid_specializations = [
            "Cardiology", "General Medicine", "Orthopedics", "Pediatrics",
            "Dermatology", "Neurology", "Gynecology", "Psychiatry",
            "ENT", "Ophthalmology", "Dentistry", "Surgery"
        ]

        if spec not in valid_specializations:
            raise ValidationError(f"Invalid specialization. Must be one of: {', '.join(valid_specializations)}")

        return spec
