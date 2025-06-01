-- Add indexes for better performance on translated_chunks table

-- Index for finding translated chunks by translation_id (already used frequently)
CREATE INDEX IF NOT EXISTS idx_translated_chunks_translation_id ON translated_chunks(translation_id);

-- Index for finding translated chunks by chunk_id
CREATE INDEX IF NOT EXISTS idx_translated_chunks_chunk_id ON translated_chunks(chunk_id);

-- Index for ordering by sequence_number within a translation
CREATE INDEX IF NOT EXISTS idx_translated_chunks_translation_sequence ON translated_chunks(translation_id, sequence_number);

-- Add a comment to document the unique constraint
COMMENT ON CONSTRAINT translated_chunks_translation_id_chunk_id_key ON translated_chunks 
IS 'Ensures each chunk can only be translated once per translation job to prevent duplicates'; 