# Database Schema Changes Summary

## Overview of Changes

Based on the requirements in the to-fix.md file, I've made the following changes to simplify and improve the database schema:

1. **Added `file_path` column to documents table:**
   - Created a dedicated column for storing file paths instead of storing them in metadata JSON
   - Updated the file upload/retrieval/deletion operations to use this field
   - Added migration to populate the field from existing metadata.storage_path values

2. **Simplified `chunk_sets` table:**
   - Removed unnecessary fields (chunk_strategy, overlap, processing_id)
   - Removed the unique constraint on (document_id, processing_id)
   - Updated models and schemas to reflect these changes

3. **Added `chunk_set_id` to chunks table:**
   - Added a direct UUID reference to chunk_sets(id)
   - Created an index for better query performance
   - Added cascade delete constraint
   - Updated all chunk-related operations to use this field

4. **Removed the trigger function:**
   - Removed the `update_chunks_with_chunk_set_id` trigger function
   - Updated the chunking process to directly assign chunks to chunk sets at creation time

5. **Removed processing_id-based functionality:**
   - Removed the processing_history tracking in document metadata
   - Replaced the `get_by_processing_id` method with `get_by_chunk_set_id`
   - Updated API endpoints to work with chunk sets instead of processing IDs

## File Changes

1. **SQL Migrations:**
   - Created `01_add_file_path_and_update_chunk_sets.sql` to modify the schema
   - Created `02_remove_legacy_functions.sql` to drop outdated functions

2. **Models and Schemas:**
   - Updated `models.py` to include file_path and chunk_set_id
   - Added ChunkSet model and removed ProcessingSession model
   - Updated `schemas.py` to reflect these changes in the API

3. **CRUD Operations:**
   - Added `ChunkSetCRUD` for managing chunk sets
   - Replaced `get_by_processing_id` with `get_by_chunk_set_id`
   - Removed `append_processing_history` method
   - Added `update_metadata` method

4. **API Endpoints:**
   - Updated `chunk_file` to create a chunk set and assign chunks to it
   - Replaced `list_chunks_by_processing_id` with `list_chunks_by_chunk_set_id`
   - Added `list_chunk_sets_by_document` endpoint

5. **Helper Functions:**
   - Updated `text_chunker.py` to remove overlap parameter
   - Simplified the chunking process

6. **File Handling:**
   - Updated file upload to set the file_path field
   - Improved file retrieval and deletion to use file_path

## Migration Strategy

The migration consists of two SQL scripts:

1. **First Migration:** Adds new columns, updates existing data, and removes unnecessary columns
2. **Second Migration:** Removes deprecated database functions

When deploying these changes, you should:

1. Apply both migrations in order
2. Deploy the updated codebase
3. Test the new functionality thoroughly

No data will be lost during the migration, as existing processing_id references in metadata are maintained (though no longer used for new operations).

## Benefits of These Changes

1. **Simpler Schema:** Removed unnecessary columns and JSON nesting
2. **Better Performance:** Direct foreign key relationships are more efficient than JSON searches
3. **Cleaner Code:** Simpler programming model with explicit relationships
4. **Improved File Management:** Dedicated file_path column for better file tracking 