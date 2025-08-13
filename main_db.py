from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
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
from services.supabase_service import supabase_service

app = FastAPI(title="Conversation API with Supabase", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "Conversation API with Supabase is running"}


@app.get("/system-prompt")
async def get_system_prompt(prompt_type: str = "default"):
    """Get the current system prompt"""
    from services.prompts import get_system_prompt as get_prompt
    return {
        "prompt_type": prompt_type,
        "prompt": get_prompt(prompt_type),
        "available_types": ["default", "minimal", "detailed"]
    }


@app.post("/conversations", response_model=ConversationResponse)
async def create_conversation(conversation_data: ConversationCreate):
    try:
        # Create conversation in database with session_id
        db_conversation = await supabase_service.create_conversation(
            title=conversation_data.title,
            session_id=conversation_data.session_id
        )
        
        if not db_conversation:
            raise HTTPException(status_code=500, detail="Failed to create conversation")
        
        conversation_id = UUID(db_conversation["id"])
        message_count = 0
        ai_response_text = None
        
        # If initial message provided, create it and get AI response
        if conversation_data.initial_message:
            # Create user message
            await supabase_service.create_message(
                conversation_id=conversation_id,
                role="user",
                content=conversation_data.initial_message
            )
            message_count += 1
            
            # Get all messages for AI context
            messages = await supabase_service.get_messages(conversation_id)
            conversation_messages = [
                Message(
                    id=UUID(msg["id"]),
                    role=msg["role"],
                    content=msg["content"],
                    created_at=msg["created_at"]
                )
                for msg in messages
            ]
            
            # Get AI response with tools support
            try:
                # Use the enhanced completion with tools
                ai_response_text = await get_openai_service().get_completion_with_tools(conversation_messages)
                
                # Save assistant message
                await supabase_service.create_message(
                    conversation_id=conversation_id,
                    role="assistant",
                    content=ai_response_text
                )
                message_count += 1
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"OpenAI error: {str(e)}")
        
        return ConversationResponse(
            id=conversation_id,
            title=db_conversation["title"],
            message_count=message_count,
            created_at=db_conversation["created_at"],
            updated_at=db_conversation["updated_at"],
            initial_message=conversation_data.initial_message,
            ai_response=ai_response_text
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/conversations", response_model=List[ConversationResponse])
async def list_conversations(session_id: Optional[str] = None):
    try:
        conversations = await supabase_service.list_conversations(session_id=session_id)
        
        result = []
        for conv in conversations:
            # Get message count for each conversation
            messages = await supabase_service.get_messages(UUID(conv["id"]))
            
            result.append(ConversationResponse(
                id=UUID(conv["id"]),
                title=conv["title"],
                message_count=len(messages),
                created_at=conv["created_at"],
                updated_at=conv["updated_at"]
            ))
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/conversations/{conversation_id}", response_model=Conversation)
async def get_conversation(conversation_id: UUID):
    try:
        # Get conversation
        conversation = await supabase_service.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Get messages
        messages = await supabase_service.get_messages(conversation_id)
        
        return Conversation(
            id=UUID(conversation["id"]),
            title=conversation["title"],
            messages=[
                Message(
                    id=UUID(msg["id"]),
                    role=msg["role"],
                    content=msg["content"],
                    created_at=msg["created_at"]
                )
                for msg in messages
            ],
            created_at=conversation["created_at"],
            updated_at=conversation["updated_at"]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/conversations/{conversation_id}/messages", response_model=MessageResponse)
async def send_message(conversation_id: UUID, message_data: MessageCreate):
    try:
        # Check if conversation exists
        conversation = await supabase_service.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Create user message
        user_msg_data = await supabase_service.create_message(
            conversation_id=conversation_id,
            role="user",
            content=message_data.content
        )
        
        user_message = Message(
            id=UUID(user_msg_data["id"]),
            role="user",
            content=user_msg_data["content"],
            created_at=user_msg_data["created_at"]
        )
        
        # Get all messages for context
        messages = await supabase_service.get_messages(conversation_id)
        conversation_messages = [
            Message(
                id=UUID(msg["id"]),
                role=msg["role"],
                content=msg["content"],
                created_at=msg["created_at"]
            )
            for msg in messages
        ]
        
        # Get AI response with tools and RAG support
        try:
            # Use tools if enabled (default is True)
            if message_data.use_tools:
                ai_response = await get_openai_service().get_completion_with_tools(
                    conversation_messages, 
                    use_rag=message_data.use_rag
                )
            else:
                ai_response, _ = await get_openai_service().get_completion(
                    conversation_messages, 
                    use_tools=False
                )
            
            # Save assistant message
            assistant_msg_data = await supabase_service.create_message(
                conversation_id=conversation_id,
                role="assistant",
                content=ai_response
            )
            
            assistant_message = Message(
                id=UUID(assistant_msg_data["id"]),
                role="assistant",
                content=assistant_msg_data["content"],
                created_at=assistant_msg_data["created_at"]
            )
            
            return MessageResponse(
                user_message=user_message,
                assistant_message=assistant_message,
                conversation_id=conversation_id
            )
        except Exception as e:
            # Delete the user message if AI fails
            # Note: You might want to keep it and handle errors differently
            raise HTTPException(status_code=500, detail=f"OpenAI error: {str(e)}")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: UUID):
    try:
        success = await supabase_service.delete_conversation(conversation_id)
        if not success:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        return {"message": "Conversation deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run("main_db:app", host="0.0.0.0", port=8000, reload=True)