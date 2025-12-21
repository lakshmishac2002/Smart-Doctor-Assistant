"""
Agent Orchestration Engine

This module implements the agentic AI system that:
1. Discovers MCP tools dynamically
2. Calls LLM with tool-calling capabilities
3. Manages conversation context across multiple turns
4. Executes tool calls and synthesizes responses
"""

from typing import List, Dict, Any, Optional
import json
import os
from datetime import datetime
from sqlalchemy.orm import Session
from mcp.server import mcp_server
from agents.free_llm import get_llm_client
from db.models import Doctor


class ConversationContext:
    """Manages conversation history and context for multi-turn interactions"""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.messages: List[Dict[str, Any]] = []
        self.metadata: Dict[str, Any] = {}
    
    def add_message(self, role: str, content: str, tool_calls: Optional[List[Dict]] = None):
        """Add a message to conversation history"""
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        if tool_calls:
            message["tool_calls"] = tool_calls
        
        self.messages.append(message)
    
    def add_tool_result(self, tool_call_id: str, tool_name: str, result: Any):
        """Add tool execution result"""
        self.messages.append({
            "role": "tool",
            "tool_call_id": tool_call_id,
            "name": tool_name,
            "content": json.dumps(result),
            "timestamp": datetime.now().isoformat()
        })
    
    def get_recent_context(self, max_messages: int = 10) -> List[Dict[str, Any]]:
        """Get recent conversation history"""
        return self.messages[-max_messages:]
    
    def extract_context_summary(self) -> str:
        """Extract relevant context for prompt injection"""
        summary = []
        for msg in self.messages[-5:]:  # Last 5 messages
            role = msg.get("role", "")
            content = msg.get("content", "")
            if role in ["user", "assistant"]:
                summary.append(f"{role.title()}: {content[:200]}")
        
        return "\n".join(summary)


class AgentOrchestrator:
    """
    Orchestrates the agentic AI system using MCP tools and LLM.
    
    This class:
    - Discovers available MCP tools
    - Formats tool definitions for LLM
    - Manages multi-turn conversations with context
    - Executes tool calls through MCP server
    - Synthesizes final responses
    """
    
    def __init__(self):
        """
        Initialize the agent orchestrator with FREE LLM support
        
        Supports: Ollama (local), Groq, Together AI, Hugging Face
        No paid API keys required!
        """
        self.llm_client = get_llm_client()
        self.mcp_server = mcp_server
        self.sessions: Dict[str, ConversationContext] = {}
    
    def get_or_create_session(self, session_id: str) -> ConversationContext:
        """Get or create conversation context for a session"""
        if session_id not in self.sessions:
            self.sessions[session_id] = ConversationContext(session_id)
        return self.sessions[session_id]
    
    def _format_tools_for_llm(self) -> List[Dict[str, Any]]:
        """
        Format MCP tools for LLM tool-calling API.
        
        Converts MCP tool definitions to OpenAI/Anthropic function calling format.
        """
        tools = self.mcp_server.list_tools()
        formatted_tools = []
        
        for tool in tools:
            formatted_tools.append({
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["parameters"]
                }
            })
        
        return formatted_tools
    
    def _call_llm(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        tool_choice: str = "auto"
    ) -> Dict[str, Any]:
        """
        Call FREE LLM with tool-calling capabilities.
        
        Supports: Ollama, Groq, Together AI, Hugging Face
        
        Args:
            messages: Conversation history
            tools: Available tools
            tool_choice: "auto", "none", or specific tool name
        
        Returns:
            LLM response with potential tool calls
        """
        try:
            # Use the free LLM client
            response = self.llm_client.chat_completion(
                messages=messages,
                tools=tools,
                tool_choice=tool_choice
            )
            return response
            
        except Exception as e:
            print(f"LLM call error: {e}")
            # Return a helpful error message
            return {
                "role": "assistant",
                "content": "I'm having trouble processing your request. Please make sure the LLM service is running. "
                          "If using Ollama, run: ollama serve"
            }
    
    def _execute_tool_calls(
        self,
        tool_calls: List[Dict[str, Any]],
        db: Session
    ) -> List[Dict[str, Any]]:
        """
        Execute tool calls through MCP server.
        
        Args:
            tool_calls: List of tool calls from LLM
            db: Database session
        
        Returns:
            List of tool execution results
        """
        results = []
        
        for tool_call in tool_calls:
            tool_call_id = tool_call["id"]
            function_name = tool_call["function"]["name"]
            arguments = json.loads(tool_call["function"]["arguments"])
            
            # Execute tool through MCP server
            result = self.mcp_server.invoke_tool(function_name, arguments, db)
            
            results.append({
                "tool_call_id": tool_call_id,
                "tool_name": function_name,
                "result": result
            })
        
        return results
    
    def _synthesize_final_response(
        self,
        messages: List[Dict[str, Any]],
        tool_results: List[Dict[str, Any]]
    ) -> str:
        """
        Create a synthesized response from tool results.

        Args:
            messages: Conversation history (not modified)
            tool_results: Results from tool executions

        Returns:
            Final synthesized response
        """
        # NOTE: Tool results are already added to messages in the main loop
        # We just format them into a human-readable response here

        final_response = ""

        for tool_result in tool_results:
            result_data = tool_result["result"]
            tool_name = tool_result["tool_name"]

            if tool_name == "get_doctor_availability":
                if result_data.get("success"):
                    slots = result_data.get("available_slots", [])
                    final_response += f"Dr. {result_data['doctor_name']} has {len(slots)} available slots on {result_data['date']}.\n"
                    if slots:
                        final_response += f"Available times: {', '.join(slots[:5])}\n"

            elif tool_name == "book_appointment":
                if result_data.get("success"):
                    final_response += f"SUCCESS: Appointment booked!\n"
                    final_response += f"Doctor: {result_data['doctor_name']}\n"
                    final_response += f"Date: {result_data['appointment_date']} at {result_data['appointment_time']}\n"
                    final_response += f"A confirmation email has been sent to {result_data.get('patient_email', 'your email')}.\n"
                else:
                    final_response += f"BOOKING FAILED: {result_data.get('error')}\n"

            elif tool_name == "get_doctor_stats":
                if result_data.get("success"):
                    final_response += f"Statistics for {result_data['doctor_name']}:\n"
                    final_response += f"Total appointments: {result_data['total_appointments']}\n"
                    final_response += f"Status breakdown: {json.dumps(result_data['status_distribution'])}\n"
                    if result_data.get('symptom_analysis'):
                        final_response += f"Common symptoms: {', '.join(list(result_data['symptom_analysis'].keys())[:3])}\n"

            elif tool_name == "list_doctors":
                if result_data.get("success"):
                    doctors = result_data.get("doctors", [])
                    # Fix grammar: "1 doctor" vs "2 doctors"
                    doctor_count = len(doctors)
                    doctor_word = "doctor" if doctor_count == 1 else "doctors"
                    final_response += f"We have {doctor_count} {doctor_word} available:\n\n"
                    for doc in doctors:
                        final_response += f"• {doc['name']} - {doc['specialization']}\n"
                        if doc.get('available_days'):
                            final_response += f"  Available: {', '.join(doc['available_days'][:3])}\n"

        return final_response.strip()
    
    async def process_message(
        self,
        session_id: str,
        user_email: str,  # ← CRITICAL: User identifier for isolation
        user_message: str,
        db: Session,
        max_iterations: int = 5
    ) -> Dict[str, Any]:
        """
        Process user message with agentic reasoning and tool execution.

        This is the main entry point for the agent system.

        Args:
            session_id: Unique session identifier for conversation continuity
            user_email: User identifier for conversation isolation (REQUIRED)
            user_message: User's natural language input
            db: Database session
            max_iterations: Maximum tool-calling iterations to prevent loops

        Returns:
            Response dict with final answer and metadata
        """
        # **USER ISOLATION: Validate user_email**
        if not user_email:
            raise ValueError("user_email is required for conversation isolation")

        # Get or create conversation context
        context = self.get_or_create_session(session_id)

        # Add user message to context
        context.add_message("user", user_message)

        # **GET CONVERSATION MEMORY CONTEXT WITH USER ISOLATION**
        from utils.conversation_memory import ConversationMemoryManager
        memory_context = ConversationMemoryManager.get_context_for_prompt(
            session_id, user_email, db  # ← USER ISOLATED
        )

        # Get available tools
        tools = self._format_tools_for_llm()

        # Get list of available doctors from database
        available_doctors = db.query(Doctor).all()
        doctors_info = "\n".join([
            f"- {doc.name} ({doc.specialization}) - Available: {', '.join(doc.available_days if doc.available_days else [])}"
            for doc in available_doctors
        ])

        # Check if this is a doctor query (session_id starts with "doctor_")
        is_doctor_query = session_id.startswith("doctor_")

        if is_doctor_query:
            # System prompt for doctor analytics/reporting
            system_prompt = f"""You are an intelligent medical analytics assistant for doctors.

{memory_context}

YOUR CAPABILITIES:
1. Get doctor statistics and appointment data using the get_doctor_stats tool
2. Analyze patient visit patterns and symptom trends
3. Answer questions about appointments, patient counts, and common symptoms

AVAILABLE TOOLS:
- get_doctor_stats: Fetches appointment data for a doctor within a date range
  Parameters: doctor_name (string), start_date (YYYY-MM-DD), end_date (YYYY-MM-DD)

IMPORTANT GUIDELINES:
- ALWAYS use get_doctor_stats tool to answer questions about appointments
- For "today": use today's date for both start_date and end_date
- For "yesterday": use yesterday's date for both start_date and end_date
- For "this week": use 7 days ago to today
- For "this month": use first day of month to today
- Provide specific numbers from the tool results, not generic responses
- Extract the doctor's name from the user message (usually starts with "I am [Doctor Name]")

CURRENT DATE: {datetime.now().strftime("%Y-%m-%d")}

When the user asks about their appointments, IMMEDIATELY call get_doctor_stats with:
1. The doctor's name mentioned in their message
2. Appropriate date range based on their query
3. Then present the specific data from the results"""
        else:
            # System prompt for patient booking
            system_prompt = f"""You are an intelligent medical appointment assistant with access to real doctor data and booking tools.

AVAILABLE DOCTORS:
{doctors_info}

{memory_context}

YOUR CAPABILITIES:
1. Answer questions about available doctors and their specializations
2. Check specific doctor availability for dates
3. Book appointments (requires: patient name, email, doctor name, date, time)"""

            # Continue system prompt
            system_prompt += """
4. Send email confirmations
5. Provide doctor statistics

IMPORTANT GUIDELINES:
- When asked about cardiologists, recommend Dr. Rajesh Ahuja (Cardiology)
- When asked about general physicians, recommend Dr. Priya Sharma or Dr. Rahul Mehta
- Always use the list_doctors tool to get current information if needed
- For bookings, collect: patient name, email, preferred doctor, date, and time
- Use book_appointment tool only when you have ALL required information
- After successful booking, confirm details and mention email was sent
- USE CONVERSATION CONTEXT: If the user says "book the same doctor" or "try next week", reference their previous selections
- If a booking failed before, suggest alternative dates/times proactively

Be helpful, professional, and proactive in suggesting doctors based on patient needs."""

        llm_messages = [
            {
                "role": "system",
                "content": system_prompt
            }
        ]
        
        # Add conversation history
        for msg in context.get_recent_context():
            if msg["role"] in ["user", "assistant"]:
                llm_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        
        # Agent loop: Call LLM, execute tools, repeat if needed
        iteration = 0
        all_tool_results = []

        while iteration < max_iterations:
            iteration += 1

            # Call LLM with tools
            llm_response = self._call_llm(
                messages=llm_messages,
                tools=tools,
                tool_choice="auto"
            )

            # Check if LLM wants to call tools
            tool_calls = llm_response.get("tool_calls")

            if not tool_calls:
                # No more tool calls, return final response
                final_content = llm_response.get("content", "")

                # If content is empty but we have tool results, synthesize response
                if not final_content and all_tool_results:
                    final_content = self._synthesize_final_response(llm_messages, all_tool_results)

                context.add_message("assistant", final_content)

                # **UPDATE MESSAGE COUNT IN MEMORY - USER ISOLATED**
                from utils.conversation_memory import ConversationMemoryManager
                ConversationMemoryManager.update_message_count(
                    session_id, user_email, user_message, final_content, db  # ← USER ISOLATED
                )

                return {
                    "success": True,
                    "response": final_content,
                    "tool_calls_made": len(all_tool_results),
                    "iterations": iteration
                }

            # Execute tool calls
            tool_results = self._execute_tool_calls(tool_calls, db)
            all_tool_results.extend(tool_results)

            # Add tool calls and results to messages for next LLM call
            llm_messages.append(llm_response)
            for tool_result in tool_results:
                llm_messages.append({
                    "role": "tool",
                    "tool_call_id": tool_result["tool_call_id"],
                    "name": tool_result["tool_name"],
                    "content": json.dumps(tool_result["result"])
                })

                context.add_tool_result(
                    tool_result["tool_call_id"],
                    tool_result["tool_name"],
                    tool_result["result"]
                )

            # After adding tool results, loop continues to let LLM generate final response

        # If we hit max iterations, synthesize response from available results
        if all_tool_results:
            final_response = self._synthesize_final_response(llm_messages, all_tool_results)
            context.add_message("assistant", final_response)

            # **UPDATE MESSAGE COUNT IN MEMORY - USER ISOLATED**
            from utils.conversation_memory import ConversationMemoryManager
            ConversationMemoryManager.update_message_count(
                session_id, user_email, user_message, final_response, db  # ← USER ISOLATED
            )

            return {
                "success": True,
                "response": final_response,
                "tool_calls_made": len(all_tool_results),
                "iterations": iteration,
                "warning": "Max iterations reached - LLM may not be responding properly"
            }

        # No tool results and hit max iterations
        return {
            "success": False,
            "response": "I apologize, but I'm having trouble processing your request. Please try again.",
            "tool_calls_made": 0,
            "iterations": iteration,
            "error": "Max iterations reached without results"
        }


# Global agent instance
agent = AgentOrchestrator()
