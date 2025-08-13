from openai import OpenAI
from typing import List, Dict, Any, Optional, Tuple
import os
import json
from dotenv import load_dotenv
from models import Message

load_dotenv()


class OpenAIService:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        # Fix for httpx/proxy issue
        import httpx
        http_client = httpx.Client()
        self.client = OpenAI(api_key=api_key, http_client=http_client)
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    
    async def get_completion(self, messages: List[Message], use_tools: bool = False, include_system_prompt: bool = True) -> Tuple[str, Optional[List[Dict]]]:
        """
        Get completion from OpenAI with optional tool/function calling support
        Returns: (response_content, tool_calls)
        """
        try:
            from services.prompts import get_system_prompt
            
            formatted_messages = []
            
            # Add system prompt if not already present and enabled
            if include_system_prompt and (not messages or messages[0].role != "system"):
                formatted_messages.append({
                    "role": "system",
                    "content": get_system_prompt("default")
                })
            
            # Add conversation messages
            formatted_messages.extend([
                {"role": msg.role, "content": msg.content}
                for msg in messages
            ])
            
            # Import tools if enabled
            if use_tools:
                from services.tools import AVAILABLE_TOOLS
                
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=formatted_messages,
                    tools=AVAILABLE_TOOLS,
                    tool_choice="auto",  # Let model decide when to use tools
                    temperature=0.7,
                    max_tokens=1000
                )
            else:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=formatted_messages,
                    temperature=0.7,
                    max_tokens=1000
                )
            
            message = response.choices[0].message
            
            # Check if the model wants to use tools
            if hasattr(message, 'tool_calls') and message.tool_calls:
                tool_calls = []
                for tool_call in message.tool_calls:
                    tool_calls.append({
                        "id": tool_call.id,
                        "name": tool_call.function.name,
                        "arguments": json.loads(tool_call.function.arguments)
                    })
                return message.content or "", tool_calls
            
            return message.content, None
            
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")
    
    async def get_completion_with_tools(self, messages: List[Message], use_rag: bool = False) -> str:
        """
        Enhanced completion that automatically handles tool calls and RAG
        """
        from services.tools import ToolExecutor, format_tool_response
        from services.prompts import get_system_prompt
        from services.pinecone_service import get_pinecone_service
        
        # Get RAG context if enabled and available
        rag_context = ""
        if use_rag and messages:
            pinecone = get_pinecone_service()
            if pinecone:
                # Get the latest user message for context retrieval
                user_messages = [msg for msg in messages if msg.role == "user"]
                if user_messages:
                    latest_query = user_messages[-1].content
                    rag_context = pinecone.get_context_for_prompt(latest_query)
        
        # If we have RAG context, add it to the messages
        enhanced_messages = messages.copy()
        if rag_context:
            # Add RAG context to the last user message for better context
            if enhanced_messages and enhanced_messages[-1].role == "user":
                original_content = enhanced_messages[-1].content
                enhanced_messages[-1].content = f"{rag_context}\n\nUser Question: {original_content}"
        
        # Get initial response with tools enabled (system prompt included)
        content, tool_calls = await self.get_completion(enhanced_messages, use_tools=True, include_system_prompt=True)
        
        if not tool_calls:
            return content
        
        # Process tool calls
        full_response = content if content else ""
        tool_results = []
        
        for tool_call in tool_calls:
            # Execute the tool
            result = ToolExecutor.execute_tool(
                tool_call["name"], 
                tool_call["arguments"]
            )
            
            # Format the result for display
            formatted_result = format_tool_response(tool_call["name"], result)
            tool_results.append(formatted_result)
        
        # Combine original response with tool results
        if full_response:
            full_response += "\n\n"
        full_response += "\n".join(tool_results)
        
        # Add tool results to conversation and get final response
        formatted_messages = []
        
        # Add system prompt
        formatted_messages.append({
            "role": "system",
            "content": get_system_prompt("default")
        })
        
        # Add conversation history
        formatted_messages.extend([
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ])
        
        # Add assistant's tool calls
        formatted_messages.append({
            "role": "assistant",
            "content": content,
            "tool_calls": [
                {
                    "id": tc["id"],
                    "type": "function",
                    "function": {
                        "name": tc["name"],
                        "arguments": json.dumps(tc["arguments"])
                    }
                }
                for tc in tool_calls
            ]
        })
        
        # Add tool results
        for i, (tool_call, result) in enumerate(zip(tool_calls, tool_results)):
            formatted_messages.append({
                "role": "tool",
                "content": json.dumps(ToolExecutor.execute_tool(
                    tool_call["name"], 
                    tool_call["arguments"]
                )),
                "tool_call_id": tool_call["id"]
            })
        
        # Get final response from model
        final_response = self.client.chat.completions.create(
            model=self.model,
            messages=formatted_messages,
            temperature=0.7,
            max_tokens=1000
        )
        
        return final_response.choices[0].message.content


openai_service = None

def get_openai_service():
    global openai_service
    if openai_service is None:
        openai_service = OpenAIService()
    return openai_service