"""
Free LLM Integration Module

Supports multiple FREE LLM providers:
- Ollama (100% free, local)
- Groq (free tier, cloud)
- Together AI (free tier)
- Hugging Face (free tier)
"""

import os
import json
import requests
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class FreeLLMClient:
    """Unified client for free LLM providers"""
    
    def __init__(self, provider: str = None):
        """
        Initialize LLM client
        
        Args:
            provider: 'ollama', 'groq', 'together', or 'huggingface'
        """
        self.provider = provider or os.getenv("LLM_PROVIDER", "ollama")
        self.setup_provider()
    
    def setup_provider(self):
        """Setup provider-specific configuration"""
        if self.provider == "ollama":
            self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            self.model = os.getenv("OLLAMA_MODEL", "llama2")
            
        elif self.provider == "groq":
            self.api_key = os.getenv("GROQ_API_KEY")
            self.base_url = "https://api.groq.com/openai/v1"
            self.model = "mixtral-8x7b-32768"  # Free on Groq
            
        elif self.provider == "together":
            self.api_key = os.getenv("TOGETHER_API_KEY")
            self.base_url = "https://api.together.xyz/v1"
            self.model = "mistralai/Mixtral-8x7B-Instruct-v0.1"  # Free tier
            
        elif self.provider == "huggingface":
            self.api_key = os.getenv("HUGGINGFACE_API_KEY")
            self.base_url = "https://api-inference.huggingface.co/models"
            self.model = "mistralai/Mistral-7B-Instruct-v0.2"
    
    def chat_completion(
        self, 
        messages: List[Dict[str, str]], 
        tools: Optional[List[Dict]] = None,
        tool_choice: str = "auto"
    ) -> Dict[str, Any]:
        """
        Call LLM with optional tool calling
        
        Args:
            messages: Conversation messages
            tools: Available tools (optional)
            tool_choice: "auto", "none", or specific tool
            
        Returns:
            LLM response with potential tool calls
        """
        if self.provider == "ollama":
            return self._call_ollama(messages, tools, tool_choice)
        elif self.provider == "groq":
            return self._call_groq(messages, tools, tool_choice)
        elif self.provider == "together":
            return self._call_together(messages, tools, tool_choice)
        elif self.provider == "huggingface":
            return self._call_huggingface(messages, tools, tool_choice)
        else:
            raise ValueError(f"Unknown provider: {self.provider}")
    
    def _call_ollama(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict]] = None,
        tool_choice: str = "auto"
    ) -> Dict[str, Any]:
        """Call Ollama API (local, free)"""
        try:
            # Ollama uses a simpler format
            url = f"{self.base_url}/api/chat"

            # Convert messages to Ollama format - skip empty content
            ollama_messages = []
            for msg in messages:
                # Skip messages with no content (tool calls)
                if msg.get("role") == "tool":
                    continue
                if not msg.get("content"):
                    continue

                ollama_messages.append({
                    "role": msg["role"],
                    "content": str(msg["content"])
                })

            # Don't use tool calling with Ollama - it's unreliable
            # Just let it answer directly from the enhanced system prompt

            payload = {
                "model": self.model,
                "messages": ollama_messages,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "num_predict": 256  # Limit response length for speed
                }
            }

            response = requests.post(url, json=payload, timeout=60)  # Increased to 60 seconds
            response.raise_for_status()
            result = response.json()

            # Get response content
            content = result.get("message", {}).get("content", "")

            # Return direct response - no tool calling
            return {
                "role": "assistant",
                "content": content
            }

        except requests.exceptions.Timeout:
            print(f"Ollama API timeout - model may need warm-up")
            return {
                "role": "assistant",
                "content": "The AI is taking longer than expected. For faster responses, try:\n1. Use the 'Book Appointment' button for instant booking\n2. Or ask a simpler question\n3. Consider switching to Groq (faster, still free)"
            }
        except requests.exceptions.ConnectionError:
            print(f"Ollama connection error - check if Ollama is running")
            return {
                "role": "assistant",
                "content": "Cannot connect to Ollama. Please ensure Ollama is running:\n1. Open terminal\n2. Run: ollama serve\n3. Or use the 'Book Appointment' button for direct booking"
            }
        except Exception as e:
            print(f"Ollama API error: {e}")
            return {
                "role": "assistant",
                "content": f"Error connecting to AI service. Please use the 'Book Appointment' button for direct booking. Error: {str(e)}"
            }
    
    def _call_groq(
        self, 
        messages: List[Dict[str, str]], 
        tools: Optional[List[Dict]] = None,
        tool_choice: str = "auto"
    ) -> Dict[str, Any]:
        """Call Groq API (free tier, fast)"""
        try:
            url = f"{self.base_url}/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": messages
            }
            
            # Groq supports function calling
            if tools and tool_choice != "none":
                payload["tools"] = tools
                payload["tool_choice"] = tool_choice
            
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            result = response.json()
            
            message = result["choices"][0]["message"]
            return {
                "role": message["role"],
                "content": message.get("content"),
                "tool_calls": message.get("tool_calls")
            }
            
        except Exception as e:
            print(f"Groq API error: {e}")
            return self._fallback_response(messages, tools)
    
    def _call_together(
        self, 
        messages: List[Dict[str, str]], 
        tools: Optional[List[Dict]] = None,
        tool_choice: str = "auto"
    ) -> Dict[str, Any]:
        """Call Together AI API (free tier)"""
        try:
            url = f"{self.base_url}/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": messages
            }
            
            # Together AI supports function calling
            if tools and tool_choice != "none":
                payload["tools"] = tools
                payload["tool_choice"] = tool_choice
            
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            result = response.json()
            
            message = result["choices"][0]["message"]
            return {
                "role": message["role"],
                "content": message.get("content"),
                "tool_calls": message.get("tool_calls")
            }
            
        except Exception as e:
            print(f"Together AI error: {e}")
            return self._fallback_response(messages, tools)
    
    def _call_huggingface(
        self, 
        messages: List[Dict[str, str]], 
        tools: Optional[List[Dict]] = None,
        tool_choice: str = "auto"
    ) -> Dict[str, Any]:
        """Call Hugging Face Inference API (free)"""
        try:
            url = f"{self.base_url}/{self.model}"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # HF uses a different format - convert messages to prompt
            prompt = self._messages_to_prompt(messages, tools)
            
            payload = {
                "inputs": prompt,
                "parameters": {
                    "max_new_tokens": 500,
                    "temperature": 0.7,
                    "return_full_text": False
                }
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=60)
            response.raise_for_status()
            result = response.json()
            
            # Extract generated text
            if isinstance(result, list) and len(result) > 0:
                content = result[0].get("generated_text", "")
            else:
                content = str(result)
            
            # Try to extract tool calls from response
            tool_calls = self._extract_tool_calls_from_text(content)
            
            if tool_calls:
                return {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": tool_calls
                }
            else:
                return {
                    "role": "assistant",
                    "content": content
                }
            
        except Exception as e:
            print(f"Hugging Face API error: {e}")
            return self._fallback_response(messages, tools)
    
    def _format_tools_for_prompt(self, tools: List[Dict]) -> str:
        """Format tools as text for prompt injection"""
        formatted = []
        for tool in tools:
            func = tool["function"]
            formatted.append(
                f"- {func['name']}: {func['description']}\n"
                f"  Parameters: {json.dumps(func['parameters']['properties'], indent=2)}"
            )
        return "\n".join(formatted)
    
    def _messages_to_prompt(self, messages: List[Dict], tools: Optional[List[Dict]] = None) -> str:
        """Convert messages to a single prompt string"""
        prompt_parts = []
        
        if tools:
            prompt_parts.append("You have access to these tools:")
            prompt_parts.append(self._format_tools_for_prompt(tools))
            prompt_parts.append("\nTo use a tool, respond with JSON: {\"tool\": \"tool_name\", \"parameters\": {...}}\n")
        
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            if role == "system":
                prompt_parts.append(f"System: {content}")
            elif role == "user":
                prompt_parts.append(f"User: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")
        
        prompt_parts.append("Assistant:")
        return "\n".join(prompt_parts)
    
    def _extract_tool_calls_from_text(self, text: str) -> Optional[List[Dict]]:
        """Extract tool calls from LLM text response"""
        # Look for JSON blocks in the response
        try:
            # Try to find JSON object in the text
            start_idx = text.find('{')
            end_idx = text.rfind('}')
            
            if start_idx != -1 and end_idx != -1:
                json_str = text[start_idx:end_idx+1]
                data = json.loads(json_str)
                
                # Check if it's a tool call
                if "tool" in data and "parameters" in data:
                    import time
                    return [{
                        "id": f"call_{int(time.time() * 1000)}",
                        "type": "function",
                        "function": {
                            "name": data["tool"],
                            "arguments": json.dumps(data["parameters"])
                        }
                    }]
        except:
            pass
        
        return None
    
    def _fallback_response(self, messages: List[Dict], tools: Optional[List[Dict]]) -> Dict[str, Any]:
        """Fallback response when API fails"""
        last_user_message = ""
        for msg in reversed(messages):
            if msg["role"] == "user":
                last_user_message = msg["content"].lower()
                break
        
        # Simple rule-based fallback for demo purposes
        if "availability" in last_user_message or "available" in last_user_message:
            return {
                "role": "assistant",
                "content": None,
                "tool_calls": [{
                    "id": "fallback_1",
                    "type": "function",
                    "function": {
                        "name": "get_doctor_availability",
                        "arguments": json.dumps({
                            "doctor_name": "Dr. Rajesh Ahuja",
                            "date": "2025-12-20"
                        })
                    }
                }]
            }
        elif "book" in last_user_message:
            return {
                "role": "assistant",
                "content": "I can help you book an appointment. Please provide the doctor's name, preferred date, and time."
            }
        else:
            return {
                "role": "assistant",
                "content": "I can help you with booking appointments, checking doctor availability, or generating reports. What would you like to do?"
            }


# Global client instance
llm_client = None

def get_llm_client() -> FreeLLMClient:
    """Get or create LLM client"""
    global llm_client
    if llm_client is None:
        llm_client = FreeLLMClient()
    return llm_client
