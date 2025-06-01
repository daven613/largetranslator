-- SETUP DATABASE FOR LARGE TRANSLATOR PROJECT
-- Run these commands in the Supabase SQL Editor or PostgreSQL client

-- Step 1: Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Step 2: Create the documents table
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    name TEXT NOT NULL,
    file_size INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Step 3: Create the chunks table
CREATE TABLE IF NOT EXISTS chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    sequence_number INTEGER NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Step 4: Create unique constraints
ALTER TABLE documents 
ADD CONSTRAINT documents_user_name_unique UNIQUE (user_id, name);

ALTER TABLE chunks
ADD CONSTRAINT chunks_document_sequence_unique UNIQUE (document_id, sequence_number);

-- Step 5: Create function for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Step 6: Create trigger for updating timestamps
CREATE TRIGGER update_documents_updated_at
BEFORE UPDATE ON documents
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- Step 7: Create useful indices
CREATE INDEX IF NOT EXISTS chunks_document_id_idx ON chunks(document_id);
CREATE INDEX IF NOT EXISTS documents_user_id_idx ON documents(user_id);
CREATE INDEX IF NOT EXISTS documents_metadata_idx ON documents USING gin (metadata);
CREATE INDEX IF NOT EXISTS chunks_metadata_idx ON chunks USING gin (metadata);

-- Step 8: Create helper functions for processing IDs
CREATE OR REPLACE FUNCTION get_processing_ids(doc_metadata JSONB) 
RETURNS TEXT[] AS $$
DECLARE
    processing_history JSONB;
    result TEXT[] := '{}';
    item JSONB;
BEGIN
    -- Get processing history array from metadata
    processing_history := doc_metadata->'processing_history';
    
    -- If processing history exists and is an array
    IF processing_history IS NOT NULL AND jsonb_typeof(processing_history) = 'array' THEN
        -- Iterate through each processing session
        FOR item IN SELECT * FROM jsonb_array_elements(processing_history)
        LOOP
            -- Add processing_id to result array
            IF item->>'processing_id' IS NOT NULL THEN
                result := array_append(result, item->>'processing_id');
            END IF;
        END LOOP;
    END IF;
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- Step 9: Create function to check for processing ID
CREATE OR REPLACE FUNCTION has_processing_id(doc_id UUID, proc_id TEXT) 
RETURNS BOOLEAN AS $$
DECLARE
    doc_metadata JSONB;
BEGIN
    -- Get document metadata
    SELECT metadata INTO doc_metadata FROM documents WHERE id = doc_id;
    
    -- Check if processing ID exists in processing history
    RETURN proc_id = ANY(get_processing_ids(doc_metadata));
END;
$$ LANGUAGE plpgsql;

-- Step 10: Create function to get chunks by processing ID
CREATE OR REPLACE FUNCTION get_chunks_by_processing_id(proc_id TEXT) 
RETURNS SETOF chunks AS $$
BEGIN
    RETURN QUERY 
    SELECT * FROM chunks 
    WHERE metadata->>'processing_id' = proc_id
    ORDER BY sequence_number;
END;
$$ LANGUAGE plpgsql;

-- Step 11: Create function to check if document has chunks
CREATE OR REPLACE FUNCTION has_chunks(document_id UUID) 
RETURNS BOOLEAN AS $$
BEGIN
  RETURN EXISTS (
    SELECT 1 FROM chunks 
    WHERE document_id = $1
    LIMIT 1
  );
END;
$$ LANGUAGE plpgsql; 