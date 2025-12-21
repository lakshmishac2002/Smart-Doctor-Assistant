"""
FastAPI Application for Smart Doctor Assistant

Main backend server that exposes:
- Chat API for patient interactions
- MCP tools and resources endpoints
- Doctor dashboard APIs
"""

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from datetime import date, datetime
import uuid

from db.database import get_db, init_db
from db.models import Doctor, Patient, Appointment
from agents.orchestrator import agent
from mcp.server import mcp_server
from auth.utils import hash_password, verify_password

# Initialize FastAPI app
app = FastAPI(
    title="Smart Doctor Assistant API",
    description="Agentic AI system for medical appointment management",
    version="1.0.0"
)

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",  # Added for Vite port conflict
        "http://localhost:5173"
    ],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== Pydantic Models ====================

class ChatMessage(BaseModel):
    session_id: Optional[str] = None
    message: str
    user_type: str = "patient"  # "patient" or "doctor"
    user_email: str  # REQUIRED: User identifier for conversation isolation

class ChatResponse(BaseModel):
    session_id: str
    response: str
    tool_calls_made: int
    success: bool

class AppointmentCreate(BaseModel):
    patient_name: str
    patient_email: EmailStr
    doctor_id: int
    appointment_date: str
    appointment_time: str
    symptoms: Optional[str] = None

class DoctorStatsRequest(BaseModel):
    doctor_id: int
    start_date: str
    end_date: str

class SignupRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    phone: str
    user_type: str  # "patient" or "doctor"
    specialization: Optional[str] = None  # Only for doctors

class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    user_type: str  # "patient" or "doctor"

class AuthResponse(BaseModel):
    success: bool
    message: str
    user_type: Optional[str] = None
    user_data: Optional[Dict] = None

# ==================== Startup Events ====================

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    init_db()
    print("[SUCCESS] Database initialized")
    print("[INFO] Smart Doctor Assistant API is running")

# ==================== Health Check ====================

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Smart Doctor Assistant",
        "version": "1.0.0",
        "mcp_enabled": True
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "database": "connected",
        "mcp_server": "active",
        "agent": "ready"
    }

# ==================== Authentication APIs ====================

@app.post("/api/auth/signup", response_model=AuthResponse)
async def signup(request: SignupRequest, db: Session = Depends(get_db)):
    """
    Register a new patient or doctor account
    """
    try:
        # Check if user already exists
        if request.user_type == "patient":
            existing_user = db.query(Patient).filter(Patient.email == request.email).first()
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )

            # Hash password
            hashed_pwd = hash_password(request.password)

            # Create new patient
            new_patient = Patient(
                name=request.name,
                email=request.email,
                password=hashed_pwd,
                phone=request.phone
            )
            db.add(new_patient)
            db.commit()
            db.refresh(new_patient)

            return AuthResponse(
                success=True,
                message="Patient account created successfully",
                user_type="patient",
                user_data={
                    "id": new_patient.id,
                    "name": new_patient.name,
                    "email": new_patient.email
                }
            )

        elif request.user_type == "doctor":
            existing_user = db.query(Doctor).filter(Doctor.email == request.email).first()
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )

            if not request.specialization:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Specialization is required for doctors"
                )

            # Hash password
            hashed_pwd = hash_password(request.password)

            # Create new doctor with default availability
            from datetime import time
            new_doctor = Doctor(
                name=request.name,
                email=request.email,
                password=hashed_pwd,
                phone=request.phone,
                specialization=request.specialization,
                available_days=['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'],
                available_start_time=time(9, 0),
                available_end_time=time(17, 0),
                slot_duration_minutes=30
            )
            db.add(new_doctor)
            db.commit()
            db.refresh(new_doctor)

            return AuthResponse(
                success=True,
                message="Doctor account created successfully",
                user_type="doctor",
                user_data={
                    "id": new_doctor.id,
                    "name": new_doctor.name,
                    "email": new_doctor.email,
                    "specialization": new_doctor.specialization
                }
            )

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user type. Must be 'patient' or 'doctor'"
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Signup failed: {str(e)}"
        )

@app.post("/api/auth/login", response_model=AuthResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    Login for patients and doctors
    """
    try:
        if request.user_type == "patient":
            user = db.query(Patient).filter(Patient.email == request.email).first()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password"
                )

            # Verify password
            if not verify_password(request.password, user.password):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password"
                )

            return AuthResponse(
                success=True,
                message="Login successful",
                user_type="patient",
                user_data={
                    "id": user.id,
                    "name": user.name,
                    "email": user.email,
                    "phone": user.phone
                }
            )

        elif request.user_type == "doctor":
            user = db.query(Doctor).filter(Doctor.email == request.email).first()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password"
                )

            # Verify password
            if not verify_password(request.password, user.password):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password"
                )

            return AuthResponse(
                success=True,
                message="Login successful",
                user_type="doctor",
                user_data={
                    "id": user.id,
                    "name": user.name,
                    "email": user.email,
                    "phone": user.phone,
                    "specialization": user.specialization
                }
            )

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user type. Must be 'patient' or 'doctor'"
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )

# ==================== Chat API (Main Agent Interface) ====================

@app.post("/api/chat", response_model=ChatResponse)
async def chat(message: ChatMessage, db: Session = Depends(get_db)):
    """
    Main chat endpoint for patient and doctor interactions.
    
    This endpoint:
    1. Receives natural language messages
    2. Routes to agent orchestrator
    3. Agent discovers and invokes MCP tools
    4. Returns synthesized response
    """
    try:
        # **USER ISOLATION: Validate user_email is provided**
        if not message.user_email or not message.user_email.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="user_email is required for conversation isolation"
            )

        # Generate or use existing session ID
        session_id = message.session_id or str(uuid.uuid4())

        # Process message through agent with USER ISOLATION
        result = await agent.process_message(
            session_id=session_id,
            user_email=message.user_email,  # ← CRITICAL: User isolation
            user_message=message.message,
            db=db
        )
        
        return ChatResponse(
            session_id=session_id,
            response=result["response"],
            tool_calls_made=result["tool_calls_made"],
            success=result["success"]
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing message: {str(e)}"
        )

# ==================== MCP Endpoints ====================

@app.get("/api/mcp/tools")
async def list_mcp_tools():
    """
    List all available MCP tools.
    
    This allows the LLM (or developers) to discover available tools.
    """
    return {
        "tools": mcp_server.list_tools(),
        "count": len(mcp_server.tools)
    }

@app.post("/api/mcp/tools/{tool_name}")
async def invoke_mcp_tool(
    tool_name: str,
    parameters: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """
    Directly invoke an MCP tool.
    
    Useful for testing or direct integrations.
    """
    try:
        result = mcp_server.invoke_tool(tool_name, parameters, db)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Tool execution failed: {str(e)}"
        )

@app.get("/api/mcp/resources")
async def list_mcp_resources():
    """List all available MCP resources"""
    return {
        "resources": [
            {
                "name": resource["name"],
                "uri": resource["uri"],
                "description": resource["description"]
            }
            for resource in mcp_server.resources.values()
        ]
    }

@app.get("/api/mcp/resources/{resource_name}")
async def get_mcp_resource(resource_name: str, db: Session = Depends(get_db)):
    """Get data from an MCP resource"""
    try:
        result = mcp_server.get_resource(resource_name, db)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Resource access failed: {str(e)}"
        )

# ==================== Doctor Management ====================

@app.get("/api/doctors")
async def get_doctors(
    specialization: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get list of all doctors"""
    query = db.query(Doctor)
    if specialization:
        query = query.filter(Doctor.specialization.ilike(f"%{specialization}%"))
    
    doctors = query.all()
    return {
        "doctors": [doctor.to_dict() for doctor in doctors],
        "count": len(doctors)
    }

@app.get("/api/doctors/{doctor_id}")
async def get_doctor(doctor_id: int, db: Session = Depends(get_db)):
    """Get specific doctor details"""
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    
    return doctor.to_dict()

# ==================== Appointment Management ====================

@app.post("/api/appointments")
async def create_appointment(
    appointment: AppointmentCreate,
    db: Session = Depends(get_db)
):
    """
    Create appointment directly (alternative to chat interface).

    This bypasses the agent and directly uses the MCP tool.

    Returns structured response with:
    - success: bool
    - error: str (if failed)
    - error_type: str (if failed - 'conflict', 'validation', etc.)
    - suggested_slots: list (if conflict)
    - appointment_id: int (if success)
    """
    result = mcp_server.invoke_tool(
        "book_appointment",
        {
            "patient_name": appointment.patient_name,
            "patient_email": appointment.patient_email,
            "doctor_name": db.query(Doctor).filter(Doctor.id == appointment.doctor_id).first().name,
            "appointment_date": appointment.appointment_date,
            "appointment_time": appointment.appointment_time,
            "symptoms": appointment.symptoms
        },
        db
    )

    # **CRITICAL: Return full structured response for conflict handling**
    # Do NOT raise HTTPException - return the result with all fields
    # This allows frontend to handle conflicts and show suggested slots
    return result

@app.get("/api/appointments")
async def get_appointments(
    patient_email: Optional[str] = None,
    doctor_id: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get appointments with optional filters"""
    query = db.query(Appointment)
    
    if patient_email:
        patient = db.query(Patient).filter(Patient.email == patient_email).first()
        if patient:
            query = query.filter(Appointment.patient_id == patient.id)
    
    if doctor_id:
        query = query.filter(Appointment.doctor_id == doctor_id)
    
    if start_date:
        query = query.filter(Appointment.appointment_date >= start_date)
    
    if end_date:
        query = query.filter(Appointment.appointment_date <= end_date)
    
    appointments = query.all()
    return {
        "appointments": [appt.to_dict() for appt in appointments],
        "count": len(appointments)
    }

@app.get("/api/appointments/{appointment_id}")
async def get_appointment(appointment_id: int, db: Session = Depends(get_db)):
    """Get specific appointment details"""
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    return appointment.to_dict()

# ==================== Doctor Dashboard ====================

@app.post("/api/doctor/stats")
async def get_doctor_stats(
    stats_request: DoctorStatsRequest,
    db: Session = Depends(get_db)
):
    """
    Get statistics for doctor dashboard.
    
    Uses MCP tool to fetch and analyze appointment data.
    """
    doctor = db.query(Doctor).filter(Doctor.id == stats_request.doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    
    result = mcp_server.invoke_tool(
        "get_doctor_stats",
        {
            "doctor_name": doctor.name,
            "start_date": stats_request.start_date,
            "end_date": stats_request.end_date
        },
        db
    )
    
    return result

@app.post("/api/doctor/generate-report")
async def generate_doctor_report(
    doctor_id: int,
    query: str,
    db: Session = Depends(get_db)
):
    """
    Generate AI summary report for doctor.

    Uses direct stats tool to answer queries like:
    - "How many patients yesterday?"
    - "What are the common symptoms this week?"
    - "Show me today's appointments"
    """
    from datetime import timedelta

    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    # Parse query to determine date range
    query_lower = query.lower()
    today = date.today()

    if "today" in query_lower:
        start_date = today
        end_date = today
        time_desc = "today"
    elif "yesterday" in query_lower:
        yesterday = today - timedelta(days=1)
        start_date = yesterday
        end_date = yesterday
        time_desc = "yesterday"
    elif "week" in query_lower or "7 days" in query_lower:
        start_date = today - timedelta(days=7)
        end_date = today
        time_desc = "this week"
    elif "month" in query_lower:
        start_date = today.replace(day=1)
        end_date = today
        time_desc = "this month"
    else:
        # Default to today
        start_date = today
        end_date = today
        time_desc = "today"

    # Call get_doctor_stats directly
    stats_result = mcp_server.invoke_tool(
        "get_doctor_stats",
        {
            "doctor_name": doctor.name,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        },
        db
    )

    if not stats_result.get("success"):
        return {
            "success": False,
            "response": f"Unable to fetch statistics: {stats_result.get('error')}",
            "tool_calls_made": 1,
            "iterations": 1
        }

    # Format the response
    total = stats_result.get("total_appointments", 0)
    status_dist = stats_result.get("status_distribution", {})
    symptoms = stats_result.get("symptom_analysis", {})

    response_text = f"Statistics for Dr. {doctor.name} ({time_desc})\n\n"
    response_text += f"Total Appointments: {total}\n\n"

    if status_dist:
        response_text += "Status Breakdown:\n"
        for status, count in status_dist.items():
            response_text += f"  - {status.title()}: {count}\n"
        response_text += "\n"

    if symptoms:
        top_symptoms = sorted(symptoms.items(), key=lambda x: x[1], reverse=True)[:5]
        if top_symptoms:
            response_text += "Common Symptoms:\n"
            for symptom, count in top_symptoms:
                response_text += f"  - {symptom}: {count} patients\n"

    return {
        "success": True,
        "response": response_text,
        "tool_calls_made": 1,
        "iterations": 1
    }

# ==================== Utility Endpoints ====================

@app.get("/api/availability/{doctor_id}")
async def check_availability(
    doctor_id: int,
    date: str,
    db: Session = Depends(get_db)
):
    """Check doctor availability for a specific date"""
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    
    result = mcp_server.invoke_tool(
        "get_doctor_availability",
        {
            "doctor_name": doctor.name,
            "date": date
        },
        db
    )
    
    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

