# 🏗️ Architecture Deep Dive

## System Overview

The Smart Doctor Assistant is built on a **truly agentic architecture** where the LLM dynamically discovers and orchestrates tools through the Model Context Protocol (MCP).

## Component Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                           USER INTERFACE                             │
│                                                                       │
│  ┌──────────────────────┐              ┌───────────────────────┐   │
│  │   Patient Portal      │              │  Doctor Dashboard     │   │
│  │   • Chat Interface    │              │  • Statistics View    │   │
│  │   • Quick Actions     │              │  • Report Generator   │   │
│  │   • Doctor List       │              │  • Appointment List   │   │
│  └──────────────────────┘              └───────────────────────┘   │
│              ▲                                      ▲                │
│              │                                      │                │
│              └──────────────┬───────────────────────┘                │
│                             │                                        │
└─────────────────────────────┼────────────────────────────────────────┘
                              │ HTTP/REST
                              │
┌─────────────────────────────▼────────────────────────────────────────┐
│                        FASTAPI BACKEND                                │
│                                                                        │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                  API ENDPOINTS                                │   │
│  │  • /api/chat        → Agent interactions                      │   │
│  │  • /api/mcp/tools   → Tool discovery                          │   │
│  │  • /api/mcp/resources → Resource access                       │   │
│  │  • /api/doctors     → Doctor management                       │   │
│  │  • /api/appointments → Appointment CRUD                       │   │
│  └────────────────────────┬─────────────────────────────────────┘   │
│                           │                                           │
│  ┌────────────────────────▼─────────────────────────────────────┐   │
│  │              AGENT ORCHESTRATOR                               │   │
│  │                                                                │   │
│  │  Core Responsibilities:                                       │   │
│  │  1. Manage conversation context (session-based)               │   │
│  │  2. Format MCP tools for LLM                                  │   │
│  │  3. Call LLM with tool-calling capabilities                   │   │
│  │  4. Execute tool calls through MCP server                     │   │
│  │  5. Handle multi-turn interactions                            │   │
│  │  6. Synthesize final responses                                │   │
│  │                                                                │   │
│  │  Key Components:                                              │   │
│  │  • ConversationContext: Maintains history                     │   │
│  │  • Tool Formatter: Converts MCP → LLM format                  │   │
│  │  • Execution Loop: Agent reasoning cycle                      │   │
│  │  • Response Synthesizer: Formats final output                 │   │
│  └────────────────────────┬─────────────────────────────────────┘   │
│                           │                                           │
│  ┌────────────────────────▼─────────────────────────────────────┐   │
│  │                   MCP SERVER                                  │   │
│  │                                                                │   │
│  │  ┌──────────────────────────────────────────────────────┐    │   │
│  │  │              MCP TOOLS (Actions)                      │    │   │
│  │  │                                                        │    │   │
│  │  │  get_doctor_availability(doctor_name, date)           │    │   │
│  │  │    → Queries database for free slots                  │    │   │
│  │  │    → Returns available time slots                     │    │   │
│  │  │                                                        │    │   │
│  │  │  book_appointment(patient, doctor, date, time, ...)   │    │   │
│  │  │    → Creates database record                          │    │   │
│  │  │    → Generates Google Calendar event                  │    │   │
│  │  │    → Returns confirmation                             │    │   │
│  │  │                                                        │    │   │
│  │  │  send_patient_email(email, appointment_id, ...)       │    │   │
│  │  │    → Sends confirmation via Gmail/SendGrid           │    │   │
│  │  │    → Logs email activity                              │    │   │
│  │  │                                                        │    │   │
│  │  │  get_doctor_stats(doctor_name, start, end)            │    │   │
│  │  │    → Aggregates appointment data                      │    │   │
│  │  │    → Analyzes symptoms and patterns                   │    │   │
│  │  │    → Returns statistical summary                      │    │   │
│  │  │                                                        │    │   │
│  │  │  send_doctor_notification(email, type, message)       │    │   │
│  │  │    → Sends to Slack or in-app system                  │    │   │
│  │  │    → Logs notification                                │    │   │
│  │  │                                                        │    │   │
│  │  │  list_doctors(specialization?)                        │    │   │
│  │  │    → Queries all doctors                              │    │   │
│  │  │    → Filters by specialization if provided            │    │   │
│  │  └──────────────────────────────────────────────────────┘    │   │
│  │                                                                │   │
│  │  ┌──────────────────────────────────────────────────────┐    │   │
│  │  │          MCP RESOURCES (Read-only Data)               │    │   │
│  │  │                                                        │    │   │
│  │  │  resource://doctors                                   │    │   │
│  │  │    → Complete doctors list with details               │    │   │
│  │  │                                                        │    │   │
│  │  │  resource://appointments                              │    │   │
│  │  │    → Current and future appointments                  │    │   │
│  │  │                                                        │    │   │
│  │  │  resource://schedules                                 │    │   │
│  │  │    → Weekly schedules for all doctors                 │    │   │
│  │  └──────────────────────────────────────────────────────┘    │   │
│  │                                                                │   │
│  │  ┌──────────────────────────────────────────────────────┐    │   │
│  │  │         MCP PROMPTS (Reasoning Templates)             │    │   │
│  │  │                                                        │    │   │
│  │  │  appointment_booking                                  │    │   │
│  │  │    → Guides booking logic and error handling          │    │   │
│  │  │    → Instructs on availability checking               │    │   │
│  │  │                                                        │    │   │
│  │  │  doctor_summary                                       │    │   │
│  │  │    → Guides report generation                         │    │   │
│  │  │    → Instructs on data analysis                       │    │   │
│  │  └──────────────────────────────────────────────────────┘    │   │
│  └────────────────────────┬─────────────────────────────────────┘   │
│                           │                                           │
└───────────────────────────┼───────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  PostgreSQL  │    │   Google     │    │ Gmail/Slack  │
│   Database   │    │   Calendar   │    │ Notifications│
│              │    │     API      │    │     API      │
└──────────────┘    └──────────────┘    └──────────────┘
```

## Data Flow: Patient Booking Appointment

```
1. User Input
   │
   ├─ "I want to book an appointment with Dr. Ahuja tomorrow at 10 AM"
   │
   ▼

2. Frontend (PatientChat.jsx)
   │
   ├─ POST /api/chat { message, session_id }
   │
   ▼

3. FastAPI Endpoint
   │
   ├─ Route to agent.process_message()
   │
   ▼

4. Agent Orchestrator
   │
   ├─ Step 1: Load conversation context (session-based)
   │   └─ Check if session_id exists
   │       └─ Load previous messages if exists
   │
   ├─ Step 2: Discover available tools
   │   └─ tools = mcp_server.list_tools()
   │   └─ Format for LLM: convert to OpenAI/Claude format
   │
   ├─ Step 3: Prepare LLM messages
   │   └─ System prompt: "You are an appointment assistant..."
   │   └─ Conversation history: [previous messages]
   │   └─ Current message: [user input]
   │
   ├─ Step 4: Call LLM with tools
   │   └─ llm_response = call_llm(messages, tools)
   │   └─ LLM analyzes: "Need to check availability first"
   │   └─ Returns: tool_call = get_doctor_availability(...)
   │
   ├─ Step 5: Execute tool call
   │   └─ result = mcp_server.invoke_tool("get_doctor_availability", {...})
   │       │
   │       ├─ Tool handler queries database
   │       ├─ Finds Dr. Ahuja's schedule
   │       ├─ Checks existing appointments
   │       ├─ Generates available slots
   │       └─ Returns: {available_slots: ["10:00", "10:30", ...]}
   │
   ├─ Step 6: LLM processes tool result
   │   └─ "10 AM is available. Should I book it?"
   │   └─ User confirms: "Yes"
   │
   ├─ Step 7: Second tool call
   │   └─ tool_call = book_appointment(...)
   │       │
   │       ├─ Create/find patient record
   │       ├─ Verify doctor exists
   │       ├─ Check slot still available
   │       ├─ Create appointment record
   │       ├─ Generate Google Calendar event
   │       └─ Returns: {success: true, appointment_id: 123, ...}
   │
   ├─ Step 8: Third tool call (automatic)
   │   └─ tool_call = send_patient_email(...)
   │       │
   │       ├─ Format confirmation email
   │       ├─ Send via Gmail/SendGrid
   │       └─ Returns: {success: true}
   │
   ├─ Step 9: Synthesize final response
   │   └─ LLM combines all results
   │   └─ Creates human-readable message
   │   └─ "✅ Appointment booked! Dr. Ahuja on [date] at 10:00 AM.
   │       Confirmation email sent to [email]"
   │
   ▼

5. Return to Frontend
   │
   ├─ Display assistant message
   ├─ Show "🔧 Used 3 tools" indicator
   └─ Update conversation history
```

## Agent Decision Flow

```
┌─────────────────────────────────────────────┐
│         User Message Received                │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│     Extract Intent & Context                 │
│  • Parse natural language                    │
│  • Identify entities (doctor, date, time)    │
│  • Recall previous conversation              │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│     Discover Available Tools                 │
│  • List all MCP tools                        │
│  • Read tool descriptions                    │
│  • Understand parameters                     │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│       LLM Reasoning (Tool Selection)         │
│  • Analyze user intent                       │
│  • Determine required tools                  │
│  • Decide tool calling sequence              │
│  • Consider edge cases                       │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
           ┌───────┴────────┐
           │                │
           ▼                ▼
    ┌───────────┐    ┌───────────┐
    │  Direct   │    │   Need    │
    │  Answer   │    │   Tool    │
    │           │    │   Call    │
    └─────┬─────┘    └─────┬─────┘
          │                │
          │                ▼
          │    ┌───────────────────────┐
          │    │  Execute Tool Call(s)  │
          │    │  • Validate parameters │
          │    │  • Call MCP tool       │
          │    │  • Get result          │
          │    └───────┬───────────────┘
          │            │
          │            ▼
          │    ┌───────────────────────┐
          │    │  Evaluate Tool Result  │
          │    │  • Success?            │
          │    │  • Need more tools?    │
          │    │  • Ready to respond?   │
          │    └───────┬───────────────┘
          │            │
          │            ▼
          │         ┌──┴──┐
          │         │     │
          │    ┌────▼─┐ ┌─▼────┐
          │    │ More │ │ Done │
          │    │Tools │ │      │
          │    └──┬───┘ └───┬──┘
          │       │         │
          │       └────┐    │
          └────────────┼────┘
                       │
                       ▼
            ┌─────────────────────┐
            │ Synthesize Response  │
            │ • Format results     │
            │ • Add context        │
            │ • Create message     │
            └──────────┬───────────┘
                       │
                       ▼
            ┌─────────────────────┐
            │   Return to User     │
            └─────────────────────┘
```

## MCP Tool Lifecycle

```
┌──────────────────────────────────────────────────────────────┐
│                     TOOL REGISTRATION                         │
│                                                                │
│  1. Tool defined in mcp/server.py                            │
│     └─ Name, description, parameters, handler                │
│                                                                │
│  2. Added to MCP server registry                             │
│     └─ self.tools["tool_name"] = {...}                       │
│                                                                │
│  3. Exposed via API endpoint                                 │
│     └─ GET /api/mcp/tools                                    │
└──────────────────┬───────────────────────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────────────────────┐
│                     TOOL DISCOVERY                            │
│                                                                │
│  1. Agent requests tool list                                 │
│     └─ tools = mcp_server.list_tools()                       │
│                                                                │
│  2. Tools formatted for LLM                                  │
│     └─ Convert to OpenAI/Claude function format              │
│                                                                │
│  3. Sent to LLM alongside user message                       │
│     └─ LLM can now "see" available tools                     │
└──────────────────┬───────────────────────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────────────────────┐
│                      TOOL INVOCATION                          │
│                                                                │
│  1. LLM decides to use a tool                                │
│     └─ Returns tool_call object with name & args             │
│                                                                │
│  2. Agent validates tool exists                              │
│     └─ if tool_name not in mcp_server.tools: error           │
│                                                                │
│  3. Agent invokes tool through MCP                           │
│     └─ result = mcp_server.invoke_tool(name, params, db)     │
│                                                                │
│  4. Tool handler executes                                    │
│     └─ Accesses database via db parameter                    │
│     └─ Performs action (query, create, update, etc.)         │
│     └─ Returns structured result                             │
└──────────────────┬───────────────────────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────────────────────┐
│                     RESULT HANDLING                           │
│                                                                │
│  1. Tool result added to conversation                        │
│     └─ {role: "tool", content: result}                       │
│                                                                │
│  2. Sent back to LLM for processing                          │
│     └─ LLM can decide: use more tools or respond             │
│                                                                │
│  3. Process repeats until LLM has final answer               │
│     └─ Max iterations prevent infinite loops                 │
└──────────────────────────────────────────────────────────────┘
```

## Key Design Principles

### 1. Separation of Concerns
- **Frontend**: Pure UI, no business logic
- **Agent**: Orchestration and reasoning
- **MCP Server**: Tool execution and data access
- **Database**: Data persistence

### 2. Tool Independence
- Each tool has single responsibility
- Tools don't call other tools
- Tools don't know about the LLM
- Tools are stateless (except for db operations)

### 3. Agentic Autonomy
- No hardcoded workflows
- LLM decides tool usage dynamically
- Multi-tool sequences emerge from reasoning
- Adapts to new tools without code changes

### 4. Context Preservation
- Session-based conversation tracking
- Full message history maintained
- Context passed to LLM each iteration
- Supports multi-turn interactions

### 5. Scalability
- New tools: just add to MCP registry
- New resources: implement handler
- New prompts: add template
- Agent automatically discovers additions

## Security Considerations

### API Key Protection
- Never exposed to frontend
- Stored in environment variables
- Not in version control (.gitignore)

### Input Validation
- Pydantic models validate all inputs
- SQL injection prevented by SQLAlchemy
- Tool parameters validated against schemas

### Database Access
- Tools are only way to access database
- No direct database URLs exposed
- Connection pooling for efficiency

### Rate Limiting
- Tool execution rate limits (future)
- API endpoint throttling (future)
- Per-session limits (future)

## Performance Optimizations

### Caching Strategy (Future)
- Cache doctor availability for N minutes
- Cache resource data with TTL
- LLM response caching for common queries

### Database Optimization
- Indexed columns for common queries
- Efficient joins in tool handlers
- Connection pooling

### Async Operations
- Async API calls to external services
- Parallel tool execution (when independent)
- Non-blocking I/O throughout

## Extending the System

### Adding a New Tool

1. Define in `mcp/server.py`:
```python
"new_tool_name": {
    "name": "new_tool_name",
    "description": "What it does",
    "parameters": {...},
    "handler": self._new_tool_handler
}
```

2. Implement handler:
```python
def _new_tool_handler(self, param1, param2, db):
    # Tool logic here
    return {"success": True, "result": ...}
```

3. That's it! Agent discovers it automatically.

### Adding a New Resource

1. Define in `mcp/server.py`:
```python
"resource_name": {
    "uri": "resource://resource_name",
    "name": "Resource Name",
    "description": "What it provides",
    "handler": self._resource_handler
}
```

### Adding External API Integration

1. Create new file in `backend/tools/`
2. Implement API client
3. Call from MCP tool handler
4. Example: Google Calendar, Slack, etc.

---

This architecture demonstrates production-grade agentic AI system design suitable for:
- Technical interviews
- System design discussions
- Portfolio projects
- Production deployment (with additional hardening)
