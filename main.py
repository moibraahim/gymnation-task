from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List
from uuid import UUID
import uvicorn

from models import (
    Conversation, 
    ConversationCreate, 
    ConversationResponse,
    Message,
    MessageCreate,
    MessageResponse
)
from services.openai_service import get_openai_service

app = FastAPI(title="Conversation API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

conversations_db: Dict[UUID, Conversation] = {}


@app.get("/")
async def root():
    return {"message": "Conversation API is running"}


@app.post("/conversations", response_model=ConversationResponse)
async def create_conversation(conversation_data: ConversationCreate):
    conversation = Conversation(
        title=conversation_data.title or "New Conversation"
    )
    
    if conversation_data.initial_message:
        user_message = Message(
            role="user",
            content=conversation_data.initial_message
        )
        conversation.messages.append(user_message)
        
        try:
            ai_response = await get_openai_service().get_completion(conversation.messages)
            assistant_message = Message(
                role="assistant",
                content=ai_response
            )
            conversation.messages.append(assistant_message)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    conversations_db[conversation.id] = conversation
    
    return ConversationResponse(
        id=conversation.id,
        title=conversation.title,
        message_count=len(conversation.messages),
        created_at=conversation.created_at,
        updated_at=conversation.updated_at
    )


@app.get("/conversations", response_model=List[ConversationResponse])
async def list_conversations():
    return [
        ConversationResponse(
            id=conv.id,
            title=conv.title,
            message_count=len(conv.messages),
            created_at=conv.created_at,
            updated_at=conv.updated_at
        )
        for conv in conversations_db.values()
    ]


@app.get("/conversations/{conversation_id}", response_model=Conversation)
async def get_conversation(conversation_id: UUID):
    if conversation_id not in conversations_db:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return conversations_db[conversation_id]


@app.post("/conversations/{conversation_id}/messages", response_model=MessageResponse)
async def send_message(conversation_id: UUID, message_data: MessageCreate):
    if conversation_id not in conversations_db:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    conversation = conversations_db[conversation_id]
    
    user_message = Message(
        role="user",
        content=message_data.content
    )
    conversation.messages.append(user_message)
    
    try:
        ai_response = await openai_service.get_completion(conversation.messages)
        assistant_message = Message(
            role="assistant",
            content=ai_response
        )
        conversation.messages.append(assistant_message)
    except Exception as e:
        conversation.messages.pop()
        raise HTTPException(status_code=500, detail=str(e))
    
    from datetime import datetime
    conversation.updated_at = datetime.utcnow()
    
    return MessageResponse(
        user_message=user_message,
        assistant_message=assistant_message
    )


@app.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: UUID):
    if conversation_id not in conversations_db:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    del conversations_db[conversation_id]
    return {"message": "Conversation deleted successfully"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)