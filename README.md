# GymNation Chat API

FastAPI-based conversational AI system with OpenAI integration, Pinecone RAG, and booking tools.

## Features

- Conversational AI with OpenAI GPT-4
- RAG (Retrieval-Augmented Generation) using Pinecone vector database
- Function calling for booking management (create, update, view bookings)
- Persistent storage with Supabase
- Session-based conversation management

## Architecture

```
/api
  ├── main_db.py          # Main FastAPI application
  ├── models.py           # Pydantic data models
  ├── services/
  │   ├── openai_service.py    # OpenAI integration with tools
  │   ├── supabase_service.py  # Database operations
  │   ├── pinecone_service.py  # Vector search RAG
  │   ├── tools.py             # Booking function definitions
  │   └── prompts.py           # System prompts
  └── database/
      └── migration.sql   # Supabase schema
```

## Installation

### Prerequisites

- Python 3.8+
- Supabase account and project
- OpenAI API key
- Pinecone account and index (512 dimensions)

### Setup

1. Clone repository and create virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables in `.env`:
```
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o-mini
SUPABASE_PROJECT_URL=your_supabase_url
SUPABASE_ANON=your_supabase_anon_key
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_INDEX_NAME=your_index_name
PINECONE_DIMENSION=512
```

4. Run database migrations in Supabase SQL editor:
```sql
-- Execute contents of database/migration.sql
-- Execute contents of database/add_session.sql
```

5. Upload documents to Pinecone (optional):
```bash
python upload_pdf.py
```

6. Start server:
```bash
python main_db.py
```

Server runs at http://localhost:8000

## API Endpoints

### Conversations

**Create conversation**
```bash
POST /conversations
{
  "title": "string",
  "initial_message": "string",
  "session_id": "string"
}
```

**Send message**
```bash
POST /conversations/{conversation_id}/messages
{
  "content": "string",
  "use_tools": true,
  "use_rag": false
}
```

**Get conversation**
```bash
GET /conversations/{conversation_id}
```

**List conversations**
```bash
GET /conversations?session_id=optional
```

**Delete conversation**
```bash
DELETE /conversations/{conversation_id}
```

## Testing

### Basic conversation
```bash
curl -X POST http://localhost:8000/conversations \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test",
    "initial_message": "Hello"
  }'
```

### With RAG enabled
```bash
curl -X POST http://localhost:8000/conversations/{id}/messages \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Tell me about GymNation",
    "use_rag": true
  }'
```

### With booking tools
```bash
curl -X POST http://localhost:8000/conversations/{id}/messages \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Book a gym session for tomorrow at 3pm",
    "use_tools": true
  }'
```

## Configuration

### Tools
Three booking functions available:
- create_booking: Create new appointments
- update_booking: Modify existing bookings  
- get_booking: Retrieve booking information

### RAG
- Documents must be uploaded to Pinecone with 512-dimension embeddings
- Use text-embedding-3-small model for compatibility
- RAG disabled by default, enable with use_rag=true

### System Prompts
Three prompt types available:
- default: Full booking assistant
- minimal: Basic tool-aware assistant
- detailed: Premium concierge mode

View current prompt:
```bash
GET /system-prompt?prompt_type=default
```

## Project Structure

```
gymnation-task/
├── main_db.py              # API server
├── models.py               # Data models
├── requirements.txt        # Dependencies
├── upload_pdf.py          # Document uploader
├── services/
│   ├── openai_service.py
│   ├── supabase_service.py
│   ├── pinecone_service.py
│   ├── tools.py
│   └── prompts.py
├── database/
│   ├── migration.sql
│   └── add_session.sql
└── .env                   # Configuration
```

## Dependencies

- FastAPI 0.115.0
- OpenAI 1.55.0
- Supabase 2.18.1
- Pinecone 7.3.0
- Pydantic 2.10.0
- Uvicorn 0.32.0

## Notes

- In-memory booking storage (production should use database)
- Session IDs for conversation grouping
- CORS enabled for all origins (restrict in production)
- Default timeout 120 seconds for API calls