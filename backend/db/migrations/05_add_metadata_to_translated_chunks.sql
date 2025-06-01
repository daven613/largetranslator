-- Add metadata column to translated_chunks table for error tracking and retry information
-- This migration adds support for storing error details, retry attempts, and other metadata

-- Add metadata column if it doesn't exist
ALTER TABLE translated_chunks 
ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}'::jsonb;

-- Add index for metadata queries
CREATE INDEX IF NOT EXISTS idx_translated_chunks_metadata ON translated_chunks USING gin (metadata);

-- Add comment for documentation
COMMENT ON COLUMN translated_chunks.metadata IS 'Stores error information, retry attempts, and other chunk-specific metadata'; 