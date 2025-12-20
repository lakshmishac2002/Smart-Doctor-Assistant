"""
Unit tests for MCP Server Tools

Run with: pytest backend/tests/test_mcp_tools.py
"""

import pytest
from datetime import date, datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.models import Base, Doctor, Patient, Appointment
from mcp.server import MCPServer

# Test database setup
TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="function")
def db_session():
    """Create a test database session"""
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    # Add test data
    doctor = Doctor(
        name="Dr. Test Doctor",
        specialization="General Physician",
        email="test.doctor@hospital.com",
        available_days=["Monday", "Tuesday", "Wednesday"],
        available_start_time=datetime.strptime("09:00", "%H:%M").time(),
        available_end_time=datetime.strptime("17:00", "%H:%M").time(),
        slot_duration_minutes=30
    )
    session.add(doctor)
    session.commit()
    
    yield session
    
    session.close()
    Base.metadata.drop_all(engine)


@pytest.fixture
def mcp_server():
    """Create MCP server instance"""
    return MCPServer()


class TestMCPTools:
    """Test MCP tool implementations"""
    
    def test_list_tools(self, mcp_server):
        """Test that all required tools are registered"""
        tools = mcp_server.list_tools()
        tool_names = [tool["name"] for tool in tools]
        
        required_tools = [
            "get_doctor_availability",
            "book_appointment",
            "send_patient_email",
            "get_doctor_stats",
            "send_doctor_notification",
            "list_doctors"
        ]
        
        for tool in required_tools:
            assert tool in tool_names, f"Required tool {tool} not found"
    
    def test_get_doctor_availability(self, mcp_server, db_session):
        """Test doctor availability checking"""
        result = mcp_server.invoke_tool(
            "get_doctor_availability",
            {
                "doctor_name": "Dr. Test Doctor",
                "date": "2025-12-22"  # Monday
            },
            db_session
        )
        
        assert result["success"] is True
        assert "available_slots" in result
        assert len(result["available_slots"]) > 0
    
    def test_get_doctor_availability_unavailable_day(self, mcp_server, db_session):
        """Test availability on unavailable day"""
        result = mcp_server.invoke_tool(
            "get_doctor_availability",
            {
                "doctor_name": "Dr. Test Doctor",
                "date": "2025-12-21"  # Sunday - not available
            },
            db_session
        )
        
        assert result["success"] is False
        assert "not available" in result["error"].lower()
    
    def test_book_appointment(self, mcp_server, db_session):
        """Test appointment booking"""
        result = mcp_server.invoke_tool(
            "book_appointment",
            {
                "patient_name": "Test Patient",
                "patient_email": "test.patient@email.com",
                "doctor_name": "Dr. Test Doctor",
                "appointment_date": "2025-12-22",
                "appointment_time": "10:00",
                "symptoms": "Test symptoms"
            },
            db_session
        )
        
        assert result["success"] is True
        assert result["appointment_id"] is not None
        assert "google_calendar_event_id" in result
    
    def test_book_appointment_duplicate_slot(self, mcp_server, db_session):
        """Test booking already occupied slot"""
        # Book first appointment
        mcp_server.invoke_tool(
            "book_appointment",
            {
                "patient_name": "Patient 1",
                "patient_email": "patient1@email.com",
                "doctor_name": "Dr. Test Doctor",
                "appointment_date": "2025-12-22",
                "appointment_time": "10:00"
            },
            db_session
        )
        
        # Try to book same slot
        result = mcp_server.invoke_tool(
            "book_appointment",
            {
                "patient_name": "Patient 2",
                "patient_email": "patient2@email.com",
                "doctor_name": "Dr. Test Doctor",
                "appointment_date": "2025-12-22",
                "appointment_time": "10:00"
            },
            db_session
        )
        
        assert result["success"] is False
        assert "already booked" in result["error"].lower()
    
    def test_get_doctor_stats(self, mcp_server, db_session):
        """Test doctor statistics retrieval"""
        # Create test appointments
        doctor = db_session.query(Doctor).first()
        patient = Patient(
            name="Test Patient",
            email="test@email.com"
        )
        db_session.add(patient)
        db_session.commit()
        
        appointment = Appointment(
            patient_id=patient.id,
            doctor_id=doctor.id,
            appointment_date=date.today(),
            appointment_time=datetime.strptime("10:00", "%H:%M").time(),
            status="scheduled",
            symptoms="fever, cough"
        )
        db_session.add(appointment)
        db_session.commit()
        
        # Get stats
        result = mcp_server.invoke_tool(
            "get_doctor_stats",
            {
                "doctor_name": "Dr. Test Doctor",
                "start_date": str(date.today()),
                "end_date": str(date.today())
            },
            db_session
        )
        
        assert result["success"] is True
        assert result["total_appointments"] == 1
        assert "fever" in result["symptom_analysis"]
    
    def test_list_doctors(self, mcp_server, db_session):
        """Test listing all doctors"""
        result = mcp_server.invoke_tool(
            "list_doctors",
            {},
            db_session
        )
        
        assert result["success"] is True
        assert result["count"] > 0
        assert len(result["doctors"]) > 0


class TestMCPResources:
    """Test MCP resource implementations"""
    
    def test_get_doctors_list_resource(self, mcp_server, db_session):
        """Test doctors list resource"""
        result = mcp_server.get_resource("doctors_list", db_session)
        
        assert "uri" in result
        assert result["uri"] == "resource://doctors"
        assert "data" in result
        assert len(result["data"]) > 0


class TestAgentOrchestrator:
    """Test agent orchestration logic"""
    
    def test_session_creation(self):
        """Test conversation session creation"""
        from agents.orchestrator import AgentOrchestrator
        
        agent = AgentOrchestrator()
        session = agent.get_or_create_session("test_session_1")
        
        assert session.session_id == "test_session_1"
        assert len(session.messages) == 0
    
    def test_context_preservation(self):
        """Test multi-turn context preservation"""
        from agents.orchestrator import AgentOrchestrator
        
        agent = AgentOrchestrator()
        session = agent.get_or_create_session("test_session_2")
        
        # Add messages
        session.add_message("user", "Hello")
        session.add_message("assistant", "Hi there!")
        
        # Verify context
        context = session.get_recent_context()
        assert len(context) == 2
        assert context[0]["role"] == "user"
        assert context[1]["role"] == "assistant"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
