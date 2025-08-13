from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime
from uuid import UUID, uuid4


class Message(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    role: Literal["user", "assistant", "system"]
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class MessageCreate(BaseModel):
    content: str
    use_tools: bool = True  # Enable/disable tool usage
    use_rag: bool = False  # Enable/disable RAG from Pinecone (default: False)


class Conversation(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    title: Optional[str] = None
    messages: List[Message] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ConversationCreate(BaseModel):
    title: Optional[str] = None
    initial_message: Optional[str] = None
    session_id: Optional[str] = None


class ConversationResponse(BaseModel):
    id: UUID
    title: Optional[str]
    message_count: int
    created_at: datetime
    updated_at: datetime
    initial_message: Optional[str] = None
    ai_response: Optional[str] = None


class MessageResponse(BaseModel):
    user_message: Message
    assistant_message: Message
    conversation_id: UUID