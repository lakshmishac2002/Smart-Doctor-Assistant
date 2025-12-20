# 🏥 Smart Doctor Assistant

An intelligent, agentic AI system for medical appointment booking and management, built with **Model Context Protocol (MCP)** and tool-calling LLMs.

## 🎯 Project Overview

This is a production-quality full-stack application demonstrating **true agentic behavior** using MCP. The system enables:

- **Patients**: Book appointments using natural language conversations
- **Doctors**: Receive AI-generated summary reports and statistics
- **AI Agent**: Dynamically discovers and invokes MCP tools without hardcoded workflows

> **🆓 100% FREE SETUP AVAILABLE!**  
> This project works with completely FREE APIs - no credit card required:
> - **LLM**: Ollama (local), Groq, Together AI, or Hugging Face
> - **Email**: Gmail SMTP
> - **Notifications**: Discord Webhooks or Telegram Bot
> 
> See [FREE_APIS_SETUP.md](FREE_APIS_SETUP.md) for complete setup guide.

### Key Features

✅ **True Agentic AI**: LLM dynamically decides which tools to use  
✅ **MCP Integration**: Tools, resources, and prompts exposed via Model Context Protocol  
✅ **Multi-turn Conversations**: Context preservation across interactions  
✅ **No Direct Database Access**: All actions through MCP tools  
✅ **External API Integration**: Google Calendar, Gmail/SendGrid, Slack  

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend (React)                      │
│                                                               │
│  ┌──────────────────┐          ┌──────────────────┐        │
│  │  Patient Chat    │          │ Doctor Dashboard │        │
│  │  Interface       │          │                  │        │
│  └──────────────────┘          └──────────────────┘        │
└───────────────────────────┬─────────────────────────────────┘
                            │
                    HTTP/REST API
                            │
┌───────────────────────────▼─────────────────────────────────┐
│                    FastAPI Backend                           │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Agent Orchestrator                       │  │
│  │  • Manages conversation context                       │  │
│  │  • Calls LLM with tool definitions                    │  │
│  │  • Executes tool calls through MCP                    │  │
│  │  • Synthesizes final responses                        │  │
│  └────────────────────┬─────────────────────────────────┘  │
│                       │                                      │
│  ┌────────────────────▼─────────────────────────────────┐  │
│  │              MCP Server                               │  │
│  │                                                        │  │
│  │  MCP TOOLS (Actions):                                 │  │
│  │  • get_doctor_availability                            │  │
│  │  • book_appointment                                   │  │
│  │  • send_patient_email                                 │  │
│  │  • get_doctor_stats                                   │  │
│  │  • send_doctor_notification                           │  │
│  │  • list_doctors                                       │  │
│  │                                                        │  │
│  │  MCP RESOURCES (Read-only):                           │  │
│  │  • doctors_list                                       │  │
│  │  • appointments_data                                  │  │
│  │  • doctor_schedules                                   │  │
│  │                                                        │  │
│  │  MCP PROMPTS (Reasoning):                             │  │
│  │  • appointment_booking                                │  │
│  │  • doctor_summary                                     │  │
│  └────────────────────┬─────────────────────────────────┘  │
│                       │                                      │
└───────────────────────┼──────────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
        ▼               ▼               ▼
   PostgreSQL    Google Calendar   Gmail/Slack
   Database      API               API
```

## 🧠 How MCP Enables True Agentic Behavior

### Traditional Approach (Hardcoded)
```python
if "book appointment" in message:
    check_availability()
    create_appointment()
    send_email()
```

### Agentic Approach (MCP)
```python
# Agent discovers tools dynamically
tools = mcp_server.list_tools()

# LLM decides which tools to use based on user intent
llm_response = call_llm(message, tools)

# Execute whatever tools the LLM chose
for tool_call in llm_response.tool_calls:
    result = mcp_server.invoke_tool(tool_call.name, tool_call.args)
```

The LLM agent:
1. **Discovers** available MCP tools at runtime
2. **Reasons** about which tools are needed for the user's request
3. **Executes** tools in the optimal sequence
4. **Adapts** to multi-turn conversations without reprogramming

## 📁 Project Structure

```
smart-doctor-assistant/
├── backend/
│   ├── main.py                    # FastAPI application
│   ├── requirements.txt           # Python dependencies
│   ├── .env.example              # Environment variables template
│   │
│   ├── mcp/
│   │   └── server.py             # MCP server with tools/resources/prompts
│   │
│   ├── agents/
│   │   └── orchestrator.py       # Agent orchestration engine
│   │
│   ├── db/
│   │   ├── database.py           # Database connection
│   │   ├── models.py             # SQLAlchemy models
│   │   └── schema.sql            # Database schema + seed data
│   │
│   └── tools/                    # External API integrations (future)
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx               # Main application component
│   │   ├── App.css               # Global styles
│   │   ├── main.jsx              # React entry point
│   │   │
│   │   └── components/
│   │       ├── PatientChat.jsx   # Patient chat interface
│   │       └── DoctorDashboard.jsx # Doctor dashboard
│   │
│   ├── index.html                # HTML template
│   ├── package.json              # Node dependencies
│   └── vite.config.js            # Vite configuration
│
└── README.md                     # This file
```

## 🚀 Setup Instructions

### Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL 14+
- **FREE LLM** (choose one):
  - **Ollama** (local, recommended) - Download from https://ollama.ai
  - **Groq** (cloud, free tier) - Sign up at https://console.groq.com
  - **Together AI** (cloud, free tier) - Sign up at https://api.together.xyz
  - **Hugging Face** (cloud, free) - Sign up at https://huggingface.co

💡 **No paid API keys required!** See [FREE_APIS_SETUP.md](FREE_APIS_SETUP.md) for detailed setup.

### 1. Database Setup

```bash
# Create PostgreSQL database
createdb smart_doctor_db

# Or using psql
psql -U postgres
CREATE DATABASE smart_doctor_db;
\q

# Initialize schema and seed data
psql -U postgres -d smart_doctor_db -f backend/db/schema.sql
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env and add your API keys

# Run the FastAPI server
python main.py

# Server will start at http://localhost:8000
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Frontend will start at http://localhost:3000
```

### 4. Verify Installation

Open http://localhost:3000 in your browser. You should see the Smart Doctor Assistant interface.

## 🎭 Sample Prompts & Scenarios

### Scenario 1: Patient Appointment Booking

**User Prompt 1:**
```
"I want to book an appointment with Dr. Ahuja tomorrow morning."
```

**Agent Flow:**
1. Parses intent (doctor: Ahuja, date: tomorrow, time: morning)
2. Calls `get_doctor_availability` tool
3. Presents available slots
4. Waits for user confirmation

**User Prompt 2:**
```
"Book the 10 AM slot."
```

**Agent Flow:**
1. Recalls context from previous conversation
2. Calls `book_appointment` tool
3. Creates Google Calendar event
4. Calls `send_patient_email` tool
5. Returns confirmation

### Scenario 2: Multi-turn Conversation

**Turn 1:**
```
User: "Check Dr. Ahuja's availability for Friday afternoon."
Agent: [Calls get_doctor_availability]
      "Dr. Ahuja has these slots available on Friday afternoon:
       • 2:00 PM
       • 2:30 PM
       • 3:00 PM
       • 3:30 PM"
```

**Turn 2:**
```
User: "Book the 3 PM slot."
Agent: [Remembers: Dr. Ahuja, Friday, 3 PM from context]
       [Calls book_appointment]
       "Great! I've booked your appointment with Dr. Ahuja 
        for Friday at 3:00 PM. Confirmation email sent."
```

### Scenario 3: Doctor Summary Report

**User Prompt:**
```
Doctor: "How many patients visited yesterday?"
```

**Agent Flow:**
1. Identifies doctor from context
2. Calls `get_doctor_stats` with yesterday's date range
3. Analyzes appointment data
4. Calls `send_doctor_notification` with summary
5. Returns formatted report

**Sample Queries for Doctors:**
- "How many fever cases this week?"
- "Show me appointments for today and tomorrow."
- "What are the most common symptoms this month?"
- "Give me a summary of completed vs scheduled appointments."

## 🔧 MCP Tool Definitions

### Tools (Actions)

#### 1. get_doctor_availability
```json
{
  "name": "get_doctor_availability",
  "description": "Get available appointment slots for a doctor",
  "parameters": {
    "doctor_name": "string",
    "date": "YYYY-MM-DD"
  }
}
```

#### 2. book_appointment
```json
{
  "name": "book_appointment",
  "description": "Book an appointment for a patient",
  "parameters": {
    "patient_name": "string",
    "patient_email": "string",
    "doctor_name": "string",
    "appointment_date": "YYYY-MM-DD",
    "appointment_time": "HH:MM",
    "symptoms": "string (optional)"
  }
}
```

#### 3. send_patient_email
```json
{
  "name": "send_patient_email",
  "description": "Send confirmation email to patient",
  "parameters": {
    "patient_email": "string",
    "appointment_id": "integer",
    "subject": "string",
    "message": "string"
  }
}
```

#### 4. get_doctor_stats
```json
{
  "name": "get_doctor_stats",
  "description": "Get appointment statistics for a doctor",
  "parameters": {
    "doctor_name": "string",
    "start_date": "YYYY-MM-DD",
    "end_date": "YYYY-MM-DD"
  }
}
```

#### 5. send_doctor_notification
```json
{
  "name": "send_doctor_notification",
  "description": "Send notification to doctor (Slack/in-app)",
  "parameters": {
    "doctor_email": "string",
    "notification_type": "report|alert|reminder",
    "title": "string",
    "message": "string"
  }
}
```

### Resources (Read-only Data)

- **doctors_list**: `resource://doctors`
- **appointments_data**: `resource://appointments`
- **doctor_schedules**: `resource://schedules`

### Prompts (Reasoning Templates)

- **appointment_booking**: Guides appointment booking reasoning
- **doctor_summary**: Guides report generation reasoning

## 🔌 API Endpoints

### Chat API
- `POST /api/chat` - Main agent interaction endpoint

### MCP Endpoints
- `GET /api/mcp/tools` - List all available tools
- `POST /api/mcp/tools/{tool_name}` - Invoke a specific tool
- `GET /api/mcp/resources` - List all resources
- `GET /api/mcp/resources/{resource_name}` - Get resource data

### Doctor Endpoints
- `GET /api/doctors` - List all doctors
- `POST /api/doctor/stats` - Get doctor statistics
- `POST /api/doctor/generate-report` - Generate AI report

### Appointment Endpoints
- `GET /api/appointments` - List appointments
- `POST /api/appointments` - Create appointment
- `GET /api/availability/{doctor_id}` - Check availability

## 🧪 Testing the Agent

### Test 1: Dynamic Tool Discovery
```bash
curl http://localhost:8000/api/mcp/tools
```

### Test 2: Direct Tool Invocation
```bash
curl -X POST http://localhost:8000/api/mcp/tools/get_doctor_availability \
  -H "Content-Type: application/json" \
  -d '{
    "doctor_name": "Dr. Rajesh Ahuja",
    "date": "2025-12-20"
  }'
```

### Test 3: Agentic Chat
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I want to book an appointment with Dr. Ahuja tomorrow at 10 AM",
    "user_type": "patient"
  }'
```

## 📊 Database Schema

### Doctors Table
- `id`, `name`, `specialization`, `email`
- `available_days[]`, `available_start_time`, `available_end_time`
- `slot_duration_minutes`

### Patients Table
- `id`, `name`, `email`, `phone`, `date_of_birth`

### Appointments Table
- `id`, `patient_id`, `doctor_id`
- `appointment_date`, `appointment_time`, `duration_minutes`
- `status`, `symptoms`, `diagnosis`, `notes`
- `google_calendar_event_id`

## 🎯 Why This Architecture is Interview-Ready

### 1. **True Agentic Behavior**
- No hardcoded if-else logic
- LLM dynamically discovers and uses tools
- Adapts to new tools without code changes

### 2. **Production-Quality MCP Implementation**
- Clean separation: Tools, Resources, Prompts
- Each tool has single responsibility
- Proper error handling and validation

### 3. **Scalable Design**
- Adding new tools is trivial (just register in MCP server)
- Agent automatically discovers new capabilities
- Frontend agnostic to backend changes

### 4. **Context Management**
- Session-based conversation tracking
- Multi-turn context preservation
- No information loss across interactions

### 5. **External API Integration**
- Google Calendar for scheduling
- Gmail/SendGrid for notifications
- Slack for doctor alerts
- All through MCP abstraction

## 🚀 Future Enhancements

- [ ] JWT-based role authentication (patient/doctor)
- [ ] Auto-rescheduling when doctor unavailable
- [ ] Prompt history and analytics
- [ ] Voice interface integration
- [ ] Symptom-based doctor recommendation
- [ ] Appointment reminders via SMS
- [ ] Insurance verification integration

## 🔒 Security Considerations

- API keys in environment variables
- Database credentials secured
- Input validation on all tools
- Rate limiting on endpoints
- CORS properly configured

## 📝 License

MIT License - Feel free to use for learning and interviews.

## 🤝 Contributing

This is a demonstration project for interviews. Feel free to fork and enhance!

## 📧 Contact

For questions about this implementation, please refer to the code comments and architecture diagrams.

---

**Built with ❤️ to demonstrate the power of Agentic AI and Model Context Protocol**
