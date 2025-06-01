-- Drop legacy functions related to processing_id
DROP FUNCTION IF EXISTS get_processing_ids() CASCADE;
DROP FUNCTION IF EXISTS has_processing_id(text) CASCADE;
DROP FUNCTION IF EXISTS get_chunks_by_processing_id(text) CASCADE;

-- Create function to get all chunks by chunk_set_id
CREATE OR REPLACE FUNCTION get_chunks_by_chunk_set_id(chunk_set_id UUID)
RETURNS SETOF chunks
LANGUAGE sql
AS $$
    SELECT * FROM chunks
    WHERE chunk_set_id = chunk_set_id
    ORDER BY sequence_number;
$$; 