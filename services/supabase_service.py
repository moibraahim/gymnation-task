from supabase import create_client, Client
from typing import List, Optional, Dict, Any
from uuid import UUID
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()


class SupabaseService:
    def __init__(self):
        url = os.getenv("SUPABASE_PROJECT_URL")
        key = os.getenv("SUPABASE_ANON")
        
        if not url or not key:
            raise ValueError("Supabase credentials not found in environment variables")
        
        try:
            self.client: Client = create_client(url, key)
        except Exception as e:
            raise ValueError(f"Failed to create Supabase client: {str(e)}")
    
    async def create_conversation(self, title: Optional[str] = None, session_id: Optional[str] = None) -> Dict[str, Any]:
        data = {
            "title": title or "New Conversation",
            "session_id": session_id
        }
        
        try:
            response = self.client.table("conversations").insert(data).execute()
            if not response.data:
                raise Exception("No data returned from insert")
            return response.data[0]
        except Exception as e:
            raise Exception(f"Failed to create conversation: {str(e)}")
    
    async def get_conversation(self, conversation_id: UUID) -> Optional[Dict[str, Any]]:
        response = self.client.table("conversations").select("*").eq("id", str(conversation_id)).execute()
        return response.data[0] if response.data else None
    
    async def list_conversations(self, session_id: Optional[str] = None) -> List[Dict[str, Any]]:
        query = self.client.table("conversations").select("*")
        
        if session_id:
            query = query.eq("session_id", session_id)
        
        response = query.order("created_at", desc=True).execute()
        return response.data or []
    
    async def delete_conversation(self, conversation_id: UUID) -> bool:
        response = self.client.table("conversations").delete().eq("id", str(conversation_id)).execute()
        return bool(response.data)
    
    async def create_message(self, conversation_id: UUID, role: str, content: str) -> Dict[str, Any]:
        data = {
            "conversation_id": str(conversation_id),
            "role": role,
            "content": content
        }
        
        response = self.client.table("messages").insert(data).execute()
        
        # Update conversation's updated_at
        self.client.table("conversations").update({
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", str(conversation_id)).execute()
        
        return response.data[0] if response.data else None
    
    async def get_messages(self, conversation_id: UUID) -> List[Dict[str, Any]]:
        response = self.client.table("messages").select("*").eq(
            "conversation_id", str(conversation_id)
        ).order("created_at").execute()
        
        return response.data or []
    
    async def update_conversation_title(self, conversation_id: UUID, title: str) -> Dict[str, Any]:
        response = self.client.table("conversations").update({
            "title": title,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", str(conversation_id)).execute()
        
        return response.data[0] if response.data else None


supabase_service = SupabaseService()