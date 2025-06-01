-- Add file_path column to documents table
ALTER TABLE documents 
ADD COLUMN file_path TEXT;

-- Populate file_path from storage_path in metadata
UPDATE documents 
SET file_path = metadata->>'storage_path'
WHERE metadata->>'storage_path' IS NOT NULL;

-- Modify chunk_sets table to remove unnecessary columns
ALTER TABLE chunk_sets
DROP COLUMN IF EXISTS chunk_strategy,
DROP COLUMN IF EXISTS overlap,
DROP COLUMN IF EXISTS processing_id;

-- Add chunk_set_id to chunks table
ALTER TABLE chunks
ADD COLUMN chunk_set_id UUID REFERENCES chunk_sets(id) ON DELETE CASCADE;

-- Create index on chunk_set_id for better performance
CREATE INDEX idx_chunks_chunk_set_id ON chunks(chunk_set_id);

-- Drop the trigger function as it's no longer needed
DROP FUNCTION IF EXISTS update_chunks_with_chunk_set_id() CASCADE;

-- Remove the unique constraint on document_id and processing_id
ALTER TABLE chunk_sets
DROP CONSTRAINT IF EXISTS chunk_sets_document_id_processing_id_key; 