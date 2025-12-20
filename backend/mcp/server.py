"""
MCP Server Implementation for Smart Doctor Assistant

This module implements the Model Context Protocol (MCP) server that exposes:
- Tools: Actions the LLM agent can invoke
- Resources: Read-only data sources
- Prompts: Reasoning templates

The LLM agent discovers and invokes these tools dynamically without
hardcoded flows.

✅ 100% FREE - Uses free APIs only!
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, date, time, timedelta
from sqlalchemy.orm import Session
from db.models import Doctor, Patient, Appointment, ConversationContext
from db.database import get_db
import json

# Import FREE integrations
from tools.free_email import get_email_client
from tools.free_notifications import get_notification_client

# Import conversation memory
from utils.conversation_memory import ConversationMemoryManager


class MCPServer:
    """
    Model Context Protocol Server
    
    Exposes tools, resources, and prompts that an LLM agent can discover
    and use to accomplish tasks autonomously.
    """
    
    def __init__(self):
        self.tools = self._register_tools()
        self.resources = self._register_resources()
        self.prompts = self._register_prompts()
    
    def _register_tools(self) -> Dict[str, Dict[str, Any]]:
        """
        Register MCP tools (actions) that the LLM can invoke.
        
        Each tool has:
        - name: Unique identifier
        - description: What the tool does
        - parameters: JSON schema for input validation
        - handler: Function that executes the tool
        """
        return {
            "get_doctor_availability": {
                "name": "get_doctor_availability",
                "description": "Get available appointment slots for a specific doctor on a given date. Returns list of available time slots.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "doctor_name": {
                            "type": "string",
                            "description": "Full name of the doctor (e.g., 'Dr. Rajesh Ahuja')"
                        },
                        "date": {
                            "type": "string",
                            "description": "Date in YYYY-MM-DD format"
                        }
                    },
                    "required": ["doctor_name", "date"]
                },
                "handler": self._get_doctor_availability
            },
            
            "book_appointment": {
                "name": "book_appointment",
                "description": "Book an appointment for a patient with a doctor at a specific date and time. Creates database entry and Google Calendar event.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "patient_name": {
                            "type": "string",
                            "description": "Full name of the patient"
                        },
                        "patient_email": {
                            "type": "string",
                            "description": "Email address of the patient"
                        },
                        "doctor_name": {
                            "type": "string",
                            "description": "Full name of the doctor"
                        },
                        "appointment_date": {
                            "type": "string",
                            "description": "Date in YYYY-MM-DD format"
                        },
                        "appointment_time": {
                            "type": "string",
                            "description": "Time in HH:MM format (24-hour)"
                        },
                        "symptoms": {
                            "type": "string",
                            "description": "Patient's symptoms or reason for visit"
                        }
                    },
                    "required": ["patient_name", "patient_email", "doctor_name", "appointment_date", "appointment_time"]
                },
                "handler": self._book_appointment
            },
            
            "send_patient_email": {
                "name": "send_patient_email",
                "description": "Send appointment confirmation email to patient with appointment details.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "patient_email": {
                            "type": "string",
                            "description": "Email address of the patient"
                        },
                        "appointment_id": {
                            "type": "integer",
                            "description": "ID of the appointment"
                        },
                        "subject": {
                            "type": "string",
                            "description": "Email subject line"
                        },
                        "message": {
                            "type": "string",
                            "description": "Email body content"
                        }
                    },
                    "required": ["patient_email", "appointment_id", "subject", "message"]
                },
                "handler": self._send_patient_email
            },
            
            "get_doctor_stats": {
                "name": "get_doctor_stats",
                "description": "Get statistics and summary data for a doctor including appointment counts, patient visits, and symptom analysis.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "doctor_name": {
                            "type": "string",
                            "description": "Full name of the doctor"
                        },
                        "start_date": {
                            "type": "string",
                            "description": "Start date for stats in YYYY-MM-DD format"
                        },
                        "end_date": {
                            "type": "string",
                            "description": "End date for stats in YYYY-MM-DD format"
                        }
                    },
                    "required": ["doctor_name", "start_date", "end_date"]
                },
                "handler": self._get_doctor_stats
            },
            
            "send_doctor_notification": {
                "name": "send_doctor_notification",
                "description": "Send notification to doctor (via Slack or in-app) with summary report or alert.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "doctor_email": {
                            "type": "string",
                            "description": "Email address of the doctor"
                        },
                        "notification_type": {
                            "type": "string",
                            "enum": ["report", "alert", "reminder"],
                            "description": "Type of notification"
                        },
                        "title": {
                            "type": "string",
                            "description": "Notification title"
                        },
                        "message": {
                            "type": "string",
                            "description": "Notification content"
                        }
                    },
                    "required": ["doctor_email", "notification_type", "title", "message"]
                },
                "handler": self._send_doctor_notification
            },
            
            "list_doctors": {
                "name": "list_doctors",
                "description": "List all available doctors with their specializations and availability.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "specialization": {
                            "type": "string",
                            "description": "Optional: Filter by specialization"
                        }
                    }
                },
                "handler": self._list_doctors
            }
        }
    
    def _register_resources(self) -> Dict[str, Dict[str, Any]]:
        """
        Register MCP resources (read-only data sources).
        
        Resources provide context to the LLM without side effects.
        """
        return {
            "doctors_list": {
                "uri": "resource://doctors",
                "name": "Doctors List",
                "description": "List of all doctors with specializations and availability",
                "handler": self._resource_doctors_list
            },
            "appointments_data": {
                "uri": "resource://appointments",
                "name": "Appointments Data",
                "description": "Current and upcoming appointments",
                "handler": self._resource_appointments_data
            },
            "doctor_schedules": {
                "uri": "resource://schedules",
                "name": "Doctor Schedules",
                "description": "Weekly schedules for all doctors",
                "handler": self._resource_doctor_schedules
            }
        }
    
    def _register_prompts(self) -> Dict[str, Dict[str, Any]]:
        """
        Register MCP prompts (reasoning templates).
        
        Prompts guide the LLM's reasoning process for specific tasks.
        """
        return {
            "appointment_booking": {
                "name": "appointment_booking",
                "description": "Reasoning prompt for booking patient appointments",
                "template": """You are an intelligent appointment booking assistant.

Your task: Help the patient book an appointment with the appropriate doctor.

Guidelines:
1. Parse the patient's request to extract: doctor preference, date, time, and symptoms
2. If information is missing, use context from previous conversation
3. Check doctor availability using get_doctor_availability tool
4. If requested slot is unavailable, suggest nearest available slots
5. Once confirmed, use book_appointment tool to create the appointment
6. Send confirmation email using send_patient_email tool
7. Provide clear, friendly confirmation to the patient

Remember:
- Always verify availability before booking
- Be helpful in suggesting alternatives if preferred slot is unavailable
- Maintain conversation context across multiple turns
- Only book when you have all required information

Current context: {context}
Patient message: {message}
"""
            },
            
            "doctor_summary": {
                "name": "doctor_summary",
                "description": "Reasoning prompt for generating doctor reports",
                "template": """You are an intelligent medical analytics assistant for doctors.

Your task: Generate insights and summaries from appointment data.

Guidelines:
1. Use get_doctor_stats tool to fetch relevant data
2. Analyze patterns in patient visits and symptoms
3. Present data in a clear, actionable format
4. Highlight important trends or anomalies
5. Send the report via send_doctor_notification tool

Focus areas:
- Patient volume trends
- Common symptoms and diagnoses
- Appointment status distribution
- Day-over-day or week-over-week changes

Current context: {context}
Doctor query: {message}
"""
            }
        }
    
    # ==================== TOOL HANDLERS ====================
    
    def _get_doctor_availability(self, doctor_name: str, date: str, db: Session) -> Dict[str, Any]:
        """Get available time slots for a doctor on a specific date"""
        try:
            target_date = datetime.strptime(date, "%Y-%m-%d").date()
            day_name = target_date.strftime("%A")
            
            # Find doctor
            doctor = db.query(Doctor).filter(Doctor.name.ilike(f"%{doctor_name}%")).first()
            if not doctor:
                return {"success": False, "error": f"Doctor '{doctor_name}' not found"}
            
            # Check if doctor works on this day
            if day_name not in doctor.available_days:
                return {
                    "success": False,
                    "error": f"Dr. {doctor.name} is not available on {day_name}s",
                    "available_days": doctor.available_days
                }
            
            # Get existing appointments for this doctor on this date
            existing_appointments = db.query(Appointment).filter(
                Appointment.doctor_id == doctor.id,
                Appointment.appointment_date == target_date,
                Appointment.status != 'cancelled'
            ).all()
            
            booked_times = {appt.appointment_time for appt in existing_appointments}
            
            # Generate available slots
            available_slots = []
            current_time = datetime.combine(target_date, doctor.available_start_time)
            end_time = datetime.combine(target_date, doctor.available_end_time)
            
            while current_time < end_time:
                slot_time = current_time.time()
                if slot_time not in booked_times:
                    available_slots.append(slot_time.strftime("%H:%M"))
                current_time += timedelta(minutes=doctor.slot_duration_minutes)
            
            return {
                "success": True,
                "doctor_name": doctor.name,
                "date": date,
                "day": day_name,
                "available_slots": available_slots,
                "slot_duration_minutes": doctor.slot_duration_minutes
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _book_appointment(
        self,
        patient_name: str,
        patient_email: str,
        doctor_name: str,
        appointment_date: str,
        appointment_time: str,
        symptoms: Optional[str] = None,
        session_id: Optional[str] = None,
        db: Session = None
    ) -> Dict[str, Any]:
        """Book an appointment with comprehensive validation and context tracking"""
        try:
            # Find or create patient
            patient = db.query(Patient).filter(Patient.email == patient_email).first()
            if not patient:
                patient = Patient(name=patient_name, email=patient_email)
                db.add(patient)
                db.flush()
            
            # Find doctor
            doctor = db.query(Doctor).filter(Doctor.name.ilike(f"%{doctor_name}%")).first()
            if not doctor:
                return {
                    "success": False,
                    "error": f"Doctor '{doctor_name}' not found in our system. Please check the name and try again."
                }

            # Parse date and time
            try:
                appt_date = datetime.strptime(appointment_date, "%Y-%m-%d").date()
                appt_time = datetime.strptime(appointment_time, "%H:%M").time()
            except ValueError as ve:
                return {
                    "success": False,
                    "error": f"Invalid date or time format. Please use YYYY-MM-DD for date and HH:MM for time."
                }

            # **COMPREHENSIVE VALIDATION**
            from utils.appointment_validator import AppointmentValidator

            validation_result = AppointmentValidator.validate_complete_appointment(
                doctor=doctor,
                appt_date=appt_date,
                appt_time=appt_time,
                db=db
            )

            if not validation_result["valid"]:
                # **SAVE REJECTION CONTEXT - USER ISOLATED**
                if session_id and patient_email:
                    ConversationMemoryManager.save_doctor_selection(
                        session_id, patient_email, doctor.id, doctor.name, doctor.specialization, db
                    )
                    ConversationMemoryManager.save_attempted_date(
                        session_id, patient_email, appointment_date, validation_result["error"], db
                    )

                response = {
                    "success": False,
                    "error": validation_result["error"],
                    "error_type": validation_result["error_type"]
                }

                # Add suggestions if available
                if validation_result["suggestions"]:
                    response["suggested_slots"] = validation_result["suggestions"]
                    response["doctor_name"] = doctor.name
                    response["requested_date"] = appointment_date

                return response
            
            # Create appointment
            appointment = Appointment(
                patient_id=patient.id,
                doctor_id=doctor.id,
                appointment_date=appt_date,
                appointment_time=appt_time,
                duration_minutes=doctor.slot_duration_minutes,
                symptoms=symptoms,
                status='scheduled'
            )
            
            db.add(appointment)
            db.commit()
            db.refresh(appointment)
            
            # In production, create Google Calendar event here
            # For now, simulate with a mock event ID
            appointment.google_calendar_event_id = f"gcal_{appointment.id}_{datetime.now().timestamp()}"
            db.commit()

            # Send confirmation email automatically
            try:
                from tools.free_email import get_email_client
                email_client = get_email_client()
                email_client.send_appointment_confirmation(
                    patient_email=patient_email,
                    patient_name=patient.name,
                    doctor_name=doctor.name,
                    appointment_date=appointment_date,
                    appointment_time=appointment_time
                )
            except Exception as email_error:
                print(f"[WARNING] Failed to send email: {email_error}")
                # Don't fail the appointment if email fails

            # Calculate end time for the appointment
            appt_datetime = datetime.combine(appt_date, appt_time)
            end_datetime = appt_datetime + timedelta(minutes=appointment.duration_minutes)
            end_time_str = end_datetime.strftime('%H:%M')

            # Format date for display
            date_formatted = appt_date.strftime('%A, %B %d, %Y')
            time_formatted = appt_time.strftime('%I:%M %p')

            # Build comprehensive confirmation message
            confirmation_message = (
                f"✅ Appointment Confirmed!\n\n"
                f"Patient: {patient.name}\n"
                f"Doctor: {doctor.name} ({doctor.specialization})\n"
                f"Date: {date_formatted}\n"
                f"Time: {time_formatted} - {end_datetime.strftime('%I:%M %p')} "
                f"({appointment.duration_minutes} minutes)\n"
                f"Location: Main Clinic\n\n"
                f"Confirmation email has been sent to {patient_email}.\n"
                f"Appointment ID: #{appointment.id}"
            )

            # **SAVE SUCCESSFUL BOOKING TO CONTEXT - USER ISOLATED**
            if session_id and patient_email:
                ConversationMemoryManager.save_successful_booking(
                    session_id=session_id,
                    patient_email=patient_email,
                    appointment_id=appointment.id,
                    doctor_name=doctor.name,
                    date=appointment_date,
                    time=appointment_time,
                    db=db
                )

            return {
                "success": True,
                "appointment_id": appointment.id,
                "patient_name": patient.name,
                "patient_email": patient_email,
                "doctor_name": doctor.name,
                "doctor_specialization": doctor.specialization,
                "appointment_date": appointment_date,
                "appointment_date_formatted": date_formatted,
                "appointment_time": appointment_time,
                "appointment_time_formatted": time_formatted,
                "end_time": end_time_str,
                "duration_minutes": appointment.duration_minutes,
                "google_calendar_event_id": appointment.google_calendar_event_id,
                "location": "Main Clinic",
                "message": confirmation_message
            }
            
        except Exception as e:
            db.rollback()
            return {"success": False, "error": str(e)}
    
    def _send_patient_email(
        self,
        patient_email: str,
        appointment_id: int,
        subject: str,
        message: str,
        db: Session
    ) -> Dict[str, Any]:
        """Send confirmation email to patient using FREE Gmail SMTP"""
        try:
            # Get appointment details
            appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
            if not appointment:
                return {"success": False, "error": "Appointment not found"}
            
            # Get free email client
            email_client = get_email_client()
            
            # Send formatted appointment confirmation
            result = email_client.send_appointment_confirmation(
                patient_email=patient_email,
                patient_name=appointment.patient.name,
                doctor_name=appointment.doctor.name,
                appointment_date=str(appointment.appointment_date),
                appointment_time=str(appointment.appointment_time)
            )
            
            return result
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _get_doctor_stats(
        self,
        doctor_name: str,
        start_date: str,
        end_date: str,
        db: Session
    ) -> Dict[str, Any]:
        """Get statistics for a doctor within date range"""
        try:
            # Find doctor
            doctor = db.query(Doctor).filter(Doctor.name.ilike(f"%{doctor_name}%")).first()
            if not doctor:
                return {"success": False, "error": f"Doctor '{doctor_name}' not found"}
            
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
            end = datetime.strptime(end_date, "%Y-%m-%d").date()
            
            # Get appointments in date range
            appointments = db.query(Appointment).filter(
                Appointment.doctor_id == doctor.id,
                Appointment.appointment_date >= start,
                Appointment.appointment_date <= end
            ).all()
            
            # Analyze data
            total_appointments = len(appointments)
            status_counts = {}
            symptom_counts = {}
            daily_counts = {}
            
            for appt in appointments:
                # Status distribution
                status_counts[appt.status] = status_counts.get(appt.status, 0) + 1
                
                # Symptom analysis
                if appt.symptoms:
                    symptoms_list = [s.strip().lower() for s in appt.symptoms.split(',')]
                    for symptom in symptoms_list:
                        symptom_counts[symptom] = symptom_counts.get(symptom, 0) + 1
                
                # Daily distribution
                day_key = str(appt.appointment_date)
                daily_counts[day_key] = daily_counts.get(day_key, 0) + 1
            
            return {
                "success": True,
                "doctor_name": doctor.name,
                "date_range": {"start": start_date, "end": end_date},
                "total_appointments": total_appointments,
                "status_distribution": status_counts,
                "symptom_analysis": symptom_counts,
                "daily_distribution": daily_counts,
                "appointments": [appt.to_dict() for appt in appointments]
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _send_doctor_notification(
        self,
        doctor_email: str,
        notification_type: str,
        title: str,
        message: str,
        db: Session
    ) -> Dict[str, Any]:
        """Send notification to doctor via FREE Discord/Telegram"""
        try:
            # Get free notification client
            notification_client = get_notification_client()
            
            # Send notification
            result = notification_client.send_notification(
                title=title,
                message=message,
                notification_type=notification_type,
                recipient=doctor_email
            )
            
            return result
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _list_doctors(self, specialization: Optional[str] = None, db: Session = None) -> Dict[str, Any]:
        """List all doctors, optionally filtered by specialization"""
        try:
            query = db.query(Doctor)
            if specialization:
                query = query.filter(Doctor.specialization.ilike(f"%{specialization}%"))
            
            doctors = query.all()
            
            return {
                "success": True,
                "count": len(doctors),
                "doctors": [doctor.to_dict() for doctor in doctors]
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ==================== RESOURCE HANDLERS ====================
    
    def _resource_doctors_list(self, db: Session) -> Dict[str, Any]:
        """Resource: List of all doctors"""
        doctors = db.query(Doctor).all()
        return {
            "uri": "resource://doctors",
            "data": [doctor.to_dict() for doctor in doctors]
        }
    
    def _resource_appointments_data(self, db: Session) -> Dict[str, Any]:
        """Resource: Current and upcoming appointments"""
        today = date.today()
        appointments = db.query(Appointment).filter(
            Appointment.appointment_date >= today
        ).all()
        
        return {
            "uri": "resource://appointments",
            "data": [appt.to_dict() for appt in appointments]
        }
    
    def _resource_doctor_schedules(self, db: Session) -> Dict[str, Any]:
        """Resource: Weekly schedules for all doctors"""
        doctors = db.query(Doctor).all()
        schedules = []
        
        for doctor in doctors:
            schedules.append({
                "doctor_name": doctor.name,
                "specialization": doctor.specialization,
                "available_days": doctor.available_days,
                "hours": f"{doctor.available_start_time} - {doctor.available_end_time}",
                "slot_duration": f"{doctor.slot_duration_minutes} minutes"
            })
        
        return {
            "uri": "resource://schedules",
            "data": schedules
        }
    
    # ==================== PUBLIC API ====================
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """List all available tools for LLM discovery"""
        return [
            {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": tool["parameters"]
            }
            for tool in self.tools.values()
        ]
    
    def invoke_tool(self, tool_name: str, parameters: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """Invoke a tool by name with given parameters"""
        if tool_name not in self.tools:
            return {"success": False, "error": f"Tool '{tool_name}' not found"}
        
        tool = self.tools[tool_name]
        handler = tool["handler"]
        
        try:
            result = handler(**parameters, db=db)
            return result
        except Exception as e:
            return {"success": False, "error": f"Tool execution failed: {str(e)}"}
    
    def get_resource(self, resource_name: str, db: Session) -> Dict[str, Any]:
        """Get resource data by name"""
        if resource_name not in self.resources:
            return {"success": False, "error": f"Resource '{resource_name}' not found"}
        
        resource = self.resources[resource_name]
        handler = resource["handler"]
        
        try:
            result = handler(db=db)
            return result
        except Exception as e:
            return {"success": False, "error": f"Resource access failed: {str(e)}"}
    
    def get_prompt_template(self, prompt_name: str, context: str, message: str) -> str:
        """Get formatted prompt template"""
        if prompt_name not in self.prompts:
            return f"Prompt '{prompt_name}' not found"
        
        template = self.prompts[prompt_name]["template"]
        return template.format(context=context, message=message)


# Global MCP server instance
mcp_server = MCPServer()
