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
    
    Uses agent to process natural language queries like:
    - "How many patients yesterday?"
    - "What are the common symptoms this week?"
    """
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    
    # Create a session for this doctor
    session_id = f"doctor_{doctor_id}_{datetime.now().timestamp()}"
    
    # Process through agent
    result = await agent.process_message(
        session_id=session_id,
        user_message=query,
        db=db
    )
    
    # Send notification to doctor
    if result["success"]:
        mcp_server.invoke_tool(
            "send_doctor_notification",
            {
                "doctor_email": doctor.email,
                "notification_type": "report",
                "title": "Daily Report",
                "message": result["response"]
            },
            db
        )
    
    return result

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
