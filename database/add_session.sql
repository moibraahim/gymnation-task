-- Simple migration to add session_id column
ALTER TABLE conversations ADD COLUMN IF NOT EXISTS session_id TEXT;

-- Add index for better query performance
CREATE INDEX IF NOT EXISTS idx_conversations_session_id ON conversations(session_id);