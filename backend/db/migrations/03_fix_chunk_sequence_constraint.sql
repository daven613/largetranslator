-- Fix chunk sequence constraint to use chunk_set_id instead of document_id
-- This allows multiple chunk sets per document with independent sequence numbering

-- Drop the old constraint that causes conflicts
ALTER TABLE chunks
DROP CONSTRAINT IF EXISTS chunks_document_sequence_unique;

-- Add new constraint based on chunk_set_id and sequence_number
ALTER TABLE chunks
ADD CONSTRAINT chunks_chunk_set_sequence_unique UNIQUE (chunk_set_id, sequence_number);

-- Create index for better performance on the new constraint
CREATE INDEX IF NOT EXISTS idx_chunks_chunk_set_sequence ON chunks(chunk_set_id, sequence_number); 