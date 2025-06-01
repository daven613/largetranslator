"""
Translation API endpoints.
"""
import logging
import os
import asyncio
import random
import json  # Add this import for JSON serialization
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Path, BackgroundTasks

from backend.db import models
from backend.db.crud.translations import (
    create_translation as create_translation_db, get_translation_by_id, get_translations_by_user, 
    get_translated_chunks_by_translation, update_translation, delete_translation,
    create_translated_chunk, get_translation_with_chunks, delete_translated_chunk,
    get_translated_chunk_by_parent
)
from backend.db.crud.chunking import (
    get_chunk_by_id, get_chunks_by_chunk_set_id, get_chunk_set_by_id
)
from backend.db.crud.files import get_document_by_id
from backend.external_services.open_ai.translation import translate_text_with_prompt
from backend.external_services.supabase.storage_service import SupabaseStorageService
from backend.api import dependencies
from backend.api.translations import schemas
# Import direct PostgreSQL client for high-performance operations
from backend.db.postgres_client import get_postgres_client

logger = logging.getLogger(__name__)
router = APIRouter(tags=["translations"])

# Configuration for parallel processing
# With direct PostgreSQL connections, we need to be careful about connection pool usage
# Reduced batch size to prevent connection pool exhaustion and ensure API responsiveness
PARALLEL_TRANSLATION_BATCH_SIZE = int(os.environ.get("PARALLEL_TRANSLATION_BATCH_SIZE", "5"))
logger.info(f"Parallel translation batch size set to: {PARALLEL_TRANSLATION_BATCH_SIZE}")

# Import OpenAI for error handling
try:
    import openai
except ImportError:
    logger.warning("OpenAI library not found. Error handling may be limited.")
    openai = None

# Translation processing functions

async def test_database_connectivity():
    """
    Test database connectivity and basic operations before starting translation.
    This prevents wasting OpenAI API calls if there are fundamental database issues.
    
    Returns:
        True if database is working properly, False otherwise
    """
    try:
        pg_client = await get_postgres_client()
        
        # Test basic connectivity with a simple query
        async with pg_client.get_connection() as conn:
            # Test basic connectivity
            result = await conn.fetchval('SELECT 1')
            if result != 1:
                logger.error("Database connectivity test failed - basic query returned unexpected result")
                return False
            
            # Test that we can read from the translations table
            await conn.fetchval('SELECT COUNT(*) FROM translations')
            
            # Test that we can read from the chunks table  
            await conn.fetchval('SELECT COUNT(*) FROM chunks')
            
            # Test that we can read from the documents table
            await conn.fetchval('SELECT COUNT(*) FROM documents')
            
            # Test basic transaction capabilities without violating constraints
            async with conn.transaction():
                # Test a simple query in a transaction that will be rolled back
                await conn.fetchval('SELECT COUNT(*) FROM translations WHERE id IS NOT NULL')
                # Force rollback to test transaction handling
                raise Exception("Rollback test transaction")
        
    except Exception as e:
        if "Rollback test transaction" in str(e):
            # This is expected - it means our transaction test worked
            logger.info("Database pre-flight test passed - ready for translation")
            return True
        else:
            logger.error(f"Database pre-flight test failed: {e}")
            return False

class TranslationError(Exception):
    """Custom exception for translation-related errors."""
    pass

class DatabaseError(TranslationError):
    """Exception for database-related errors that should fail the entire job."""
    pass

class OpenAIError(TranslationError):
    """Exception for OpenAI-related errors that should be retried."""
    pass

async def translate_chunk_with_retry(chunk_id: UUID, translation_id: UUID, prompt: str, max_retries: int = 2) -> UUID:
    """
    Translate a single chunk with transactional safety and robust retry logic.
    
    This function implements:
    - Proper connection management: Never hold DB connections during external API calls
    - Transactional safety: OpenAI + DB operations succeed together or fail together
    - 2 immediate retries with exponential backoff for rate limits and transient errors
    - Error storage in metadata for policy violations and permanent failures
    
    Args:
        chunk_id: ID of the chunk to translate
        translation_id: ID of the translation job
        prompt: Translation prompt to use
        max_retries: Maximum number of retries for transient errors (default: 2)
        
    Returns:
        Translated chunk ID, or None if there was a permanent error
    """
    try:
        logger.info(f"Starting translation of chunk {chunk_id} for translation {translation_id}")
        
        # Use direct PostgreSQL client for high-performance operations
        pg_client = await get_postgres_client()
        
        # STEP 1: Fetch required data and immediately release connection
        async with pg_client.get_connection() as conn:
            # Get translation and chunk data
            translation = await conn.fetchrow("SELECT * FROM translations WHERE id = $1", str(translation_id))
            if not translation:
                logger.error(f"Translation with ID {translation_id} not found")
                return None
            
            chunk = await conn.fetchrow("SELECT * FROM chunks WHERE id = $1", str(chunk_id))
            if not chunk:
                logger.error(f"Chunk with ID {chunk_id} not found")
                return None
            
            # Check if a translated chunk already exists
            existing_chunk = await conn.fetchrow("""
                SELECT * FROM chunks 
                WHERE translation_id = $1 AND parent_chunk_id = $2 AND chunk_type = 'translated'
            """, str(translation_id), str(chunk_id))
            
            if existing_chunk:
                logger.info(f"Translated chunk already exists for chunk_id {chunk_id} and translation_id {translation_id}")
                return UUID(str(existing_chunk["id"]))
        
        # Connection is now released - safe to make external API calls
        
        # Create translation prompt
        translation_prompt = f"{prompt}\n\nText to translate:\n{chunk['content']}"
        
        # STEP 2: Attempt translation with retry logic (NO DATABASE CONNECTION HELD)
        translated_content = None
        final_error = None
        
        for attempt in range(max_retries + 1):
            try:
                logger.info(f"Calling OpenAI API to translate chunk {chunk_id} (attempt {attempt + 1}/{max_retries + 1})")
                
                # Call OpenAI API without holding any database connections
                translated_content = await translate_text_with_prompt(translation_prompt, translation["ai_model"])
                
                logger.info(f"Successfully translated chunk {chunk_id} on attempt {attempt + 1}")
                break  # Success - exit retry loop
                
            except Exception as e:
                error_type = type(e).__name__
                error_message = str(e)
                final_error = e
                
                logger.warning(f"Translation attempt {attempt + 1} failed for chunk {chunk_id}: {error_type}: {error_message}")
                
                # Check if this is a transient OpenAI error that should be retried
                is_transient_error = _is_transient_error(e)
                
                if is_transient_error and attempt < max_retries:
                    # Calculate exponential backoff delay with jitter
                    delay = min(60, (2 ** attempt) + random.uniform(0, 1))
                    logger.info(f"Transient error detected. Retrying chunk {chunk_id} in {delay:.2f} seconds...")
                    await asyncio.sleep(delay)
                    continue
                else:
                    # Permanent error or max retries exceeded
                    logger.error(f"Permanent error or max retries exceeded for chunk {chunk_id}: {error_type}: {error_message}")
                    break  # Exit retry loop
        
        # STEP 3: Save results to database (acquire fresh connection)
        async with pg_client.get_connection() as conn:
            if translated_content is not None:
                # Success case - save translated content
                try:
                    async with conn.transaction():
                        # Create successful translated chunk
                        result = await conn.fetchrow("""
                            INSERT INTO chunks (
                                document_id, chunk_set_id, parent_chunk_id, translation_id, 
                                sequence_number, content, chunk_type, target_language, 
                                metadata, created_at, updated_at
                            ) VALUES ($1, NULL, $2, $3, $4, $5, 'translated', $6, $7, NOW(), NOW())
                            RETURNING id
                        """, 
                        str(chunk["document_id"]), str(chunk_id), str(translation_id),
                        chunk["sequence_number"], translated_content, translation["target_language"],
                        json.dumps({"status": "success", "attempts": max_retries + 1})
                        )
                        
                        translated_chunk_id = result["id"]
                        
                        # Update translation progress in same transaction
                        await conn.execute("""
                            UPDATE translations 
                            SET completed_chunks = completed_chunks + 1,
                                status = CASE 
                                    WHEN completed_chunks + 1 >= total_chunks THEN 'completed'
                                    ELSE 'in_progress'
                                END,
                                updated_at = NOW()
                            WHERE id = $1
                        """, str(translation_id))
                        
                        logger.info(f"Created translated chunk {translated_chunk_id} and updated progress for translation {translation_id}")
                        return UUID(str(translated_chunk_id))
                        
                except Exception as db_error:
                    # Database error after successful OpenAI call - this is a critical failure
                    logger.error(f"DATABASE ERROR after successful OpenAI call for chunk {chunk_id}: {db_error}")
                    logger.error("This indicates a fundamental database/code issue - failing entire translation job")
                    raise DatabaseError(f"Failed to save successful translation to database: {db_error}")
                    
            else:
                # Failure case - save error information
                if final_error:
                    error_type = type(final_error).__name__
                    error_message = str(final_error)
                    is_transient = _is_transient_error(final_error)
                    
                    # Create failed translated chunk with error details in metadata
                    error_metadata = json.dumps({
                        "status": "failed",
                        "error_type": error_type,
                        "error_message": error_message,
                        "attempts": max_retries + 1,
                        "is_transient": is_transient,
                        "failed_at": str(asyncio.get_event_loop().time())
                    })
                    
                    try:
                        async with conn.transaction():
                            result = await conn.fetchrow("""
                                INSERT INTO chunks (
                                    document_id, chunk_set_id, parent_chunk_id, translation_id, 
                                    sequence_number, content, chunk_type, target_language, 
                                    metadata, created_at, updated_at
                                ) VALUES ($1, NULL, $2, $3, $4, $5, 'translated', $6, $7, NOW(), NOW())
                                RETURNING id
                            """, 
                            str(chunk["document_id"]), str(chunk_id), str(translation_id),
                            chunk["sequence_number"], "",  # Empty content for failed translation
                            translation["target_language"], error_metadata
                            )
                            
                            failed_chunk_id = result["id"]
                            
                            # Update translation progress (failed chunks still count as "processed")
                            await conn.execute("""
                                UPDATE translations 
                                SET completed_chunks = completed_chunks + 1,
                                    status = CASE 
                                        WHEN completed_chunks + 1 >= total_chunks THEN 'completed_with_errors'
                                        ELSE 'in_progress'
                                    END,
                                    updated_at = NOW()
                                WHERE id = $1
                            """, str(translation_id))
                            
                            logger.info(f"Created failed translated chunk {failed_chunk_id} for chunk {chunk_id}")
                            return UUID(str(failed_chunk_id))
                            
                    except Exception as create_error:
                        logger.error(f"Failed to create failed chunk record for chunk {chunk_id}: {create_error}")
                        return None
                        
                return None  # No final_error somehow
        
    except Exception as e:
        logger.error(f"Unexpected error in translate_chunk_with_retry for chunk {chunk_id}: {str(e)}", exc_info=True)
        return None

def _is_transient_error(error: Exception) -> bool:
    """
    Determine if an error is transient and should be retried.
    
    Args:
        error: The exception to check
        
    Returns:
        True if the error is transient (rate limits, timeouts, server errors)
        False if the error is permanent (policy violations, authentication, invalid input)
    """
    if not openai:
        # If OpenAI library isn't available, treat as permanent error
        return False
    
    error_message = str(error).lower()
    
    # Transient errors (should retry)
    if isinstance(error, (openai.RateLimitError, openai.APITimeoutError, openai.InternalServerError)):
        return True
    
    # Check for specific error messages that indicate transient issues
    transient_indicators = [
        "rate limit",
        "timeout",
        "server error",
        "service unavailable",
        "too many requests",
        "try again later",
        "temporary",
        "busy"
    ]
    
    if any(indicator in error_message for indicator in transient_indicators):
        return True
    
    # Permanent errors (should not retry)
    permanent_indicators = [
        "content policy",
        "policy violation",
        "inappropriate",
        "unsafe",
        "invalid api key",
        "authentication",
        "permission denied",
        "quota exceeded",
        "billing",
        "invalid request",
        "model not found"
    ]
    
    if any(indicator in error_message for indicator in permanent_indicators):
        return False
    
    # Default to permanent error for unknown error types
    return False

async def process_translation_job(job_id: UUID, user_id: UUID, prompt: str) -> None:
    """
    Process a translation job in the background with parallel chunk processing.
    
    Includes fail-fast mechanism: if database errors occur, the entire job is stopped
    immediately to prevent wasting OpenAI API calls.
    
    Processes chunks in parallel batches to improve throughput while avoiding
    overwhelming the OpenAI API. Each batch processes up to PARALLEL_TRANSLATION_BATCH_SIZE
    chunks concurrently, with proper error handling for individual chunk failures.
    
    Args:
        job_id: Translation job ID
        user_id: User ID
        prompt: Translation prompt
    """
    try:
        # CRITICAL: Test database connectivity before starting any OpenAI calls
        logger.info(f"Running database pre-flight test for translation {job_id}")
        if not await test_database_connectivity():
            logger.error(f"Database pre-flight test failed for translation {job_id} - aborting job")
            await update_translation(
                job_id,
                models.TranslationUpdate(status="failed")
            )
            return
        
        # Get translation
        translation = await get_translation_by_id(job_id)
        if not translation:
            raise ValueError(f"Translation with ID {job_id} not found")
        
        # Check user permission
        if str(translation.user_id) != str(user_id):
            raise ValueError("Permission denied")
        
        # Update status to in_progress immediately
        await update_translation(
            job_id,
            models.TranslationUpdate(status="in_progress")
        )
        logger.info(f"Translation {job_id} status updated to in_progress")
        
        # Get chunks from chunk set
        chunks = await get_chunks_by_chunk_set_id(translation.chunk_set_id)
        logger.info(f"Processing {len(chunks)} chunks for translation {job_id} in parallel batches of {PARALLEL_TRANSLATION_BATCH_SIZE}")
        
        # Track statistics
        successful_chunks = 0
        failed_chunks = 0
        
        # Process chunks in parallel batches
        for i in range(0, len(chunks), PARALLEL_TRANSLATION_BATCH_SIZE):
            batch = chunks[i:i + PARALLEL_TRANSLATION_BATCH_SIZE]
            batch_number = (i // PARALLEL_TRANSLATION_BATCH_SIZE) + 1
            total_batches = (len(chunks) + PARALLEL_TRANSLATION_BATCH_SIZE - 1) // PARALLEL_TRANSLATION_BATCH_SIZE
            
            logger.info(f"Processing batch {batch_number}/{total_batches} with {len(batch)} chunks for translation {job_id}")
            
            # Create tasks for this batch
            batch_tasks = [
                translate_chunk_with_retry(chunk.id, job_id, prompt)
                for chunk in batch
            ]
            
            # Execute batch in parallel with fail-fast error handling
            try:
                batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
                
                # Check for database errors in results - if found, fail immediately
                for j, (chunk, result) in enumerate(zip(batch, batch_results)):
                    if isinstance(result, DatabaseError):
                        chunk_number = i + j + 1
                        logger.error(f"DATABASE ERROR in chunk {chunk_number}/{len(chunks)} (ID: {chunk.id}): {result}")
                        logger.error("FAILING ENTIRE TRANSLATION JOB due to database error")
                        
                        # Update translation status to failed immediately
                        await update_translation(
                            job_id,
                            models.TranslationUpdate(status="failed")
                        )
                        return  # Stop processing immediately
                
                # Process results from this batch (only if no database errors)
                for j, (chunk, result) in enumerate(zip(batch, batch_results)):
                    chunk_number = i + j + 1
                    
                    if isinstance(result, Exception) and not isinstance(result, DatabaseError):
                        # Non-database exception occurred in task (OpenAI error, etc.)
                        failed_chunks += 1
                        logger.error(f"Chunk {chunk_number}/{len(chunks)} (ID: {chunk.id}) failed with exception: {result}")
                    elif result is not None:
                        # Check if the chunk was actually successful or failed by checking metadata
                        try:
                            translated_chunk = await get_translated_chunk_by_parent(job_id, chunk.id)
                            if translated_chunk and translated_chunk.metadata:
                                chunk_status = translated_chunk.metadata.get("status", "success")
                                if chunk_status == "success":
                                    successful_chunks += 1
                                    logger.debug(f"Chunk {chunk_number}/{len(chunks)} (ID: {chunk.id}) completed successfully")
                                elif chunk_status == "failed":
                                    failed_chunks += 1
                                    logger.warning(f"Chunk {chunk_number}/{len(chunks)} (ID: {chunk.id}) failed but translation continues. Error: {translated_chunk.metadata.get('error_message', 'Unknown error')}")
                            else:
                                successful_chunks += 1  # Assume success if no metadata or chunk not found
                        except Exception as e:
                            logger.warning(f"Could not determine status of chunk {chunk.id}: {e}")
                            successful_chunks += 1  # Assume success
                    else:
                        failed_chunks += 1
                        logger.error(f"Chunk {chunk_number}/{len(chunks)} (ID: {chunk.id}) failed to process")
                
                # Delay between batches to prevent connection pool exhaustion and ensure API responsiveness
                if i + PARALLEL_TRANSLATION_BATCH_SIZE < len(chunks):
                    await asyncio.sleep(1.0)  # 1 second delay between batches for better connection management
                    
            except Exception as batch_error:
                logger.error(f"Error processing batch {batch_number}: {batch_error}")
                failed_chunks += len(batch)
        
        # Re-fetch translation to get updated completed_chunks count
        updated_translation = await get_translation_by_id(job_id)
        if not updated_translation:
            raise ValueError(f"Translation with ID {job_id} not found after processing")
        
        # Determine final status based on results
        if updated_translation.completed_chunks == updated_translation.total_chunks:
            if failed_chunks == 0:
                final_status = "completed"
                logger.info(f"Translation {job_id} completed successfully - all {successful_chunks} chunks translated in parallel")
            else:
                final_status = "completed_with_errors" 
                logger.warning(f"Translation {job_id} completed with errors - {successful_chunks} successful, {failed_chunks} failed")
            
            await update_translation(
                job_id,
                models.TranslationUpdate(status=final_status)
            )
        else:
            logger.warning(f"Translation {job_id} finished but completed_chunks ({updated_translation.completed_chunks}) != total_chunks ({updated_translation.total_chunks})")
    
    except DatabaseError as db_error:
        logger.error(f"DATABASE ERROR in translation job {job_id}: {str(db_error)}")
        logger.error("This indicates a fundamental database/code issue")
        
        # Update translation status to failed
        try:
            await update_translation(
                job_id,
                models.TranslationUpdate(status="failed")
            )
            logger.info(f"Translation {job_id} status updated to failed due to database error")
        except Exception as update_error:
            logger.error(f"Failed to update translation {job_id} status to failed: {str(update_error)}")
    
    except Exception as e:
        logger.error(f"Failed to process translation job {job_id}: {str(e)}", exc_info=True)

# API Endpoints

@router.post("", response_model=schemas.TranslationResponse)
async def create_translation(
    background_tasks: BackgroundTasks, 
    translation_request: schemas.TranslationCreateRequest, 
    user = Depends(dependencies.get_current_user)
):
    """
    Create and start a new translation job.
    
    Args:
        background_tasks: Background tasks handler
        translation_request: Translation details (chunk_set_id, prompt)
        user: Current authenticated user
        
    Returns:
        Created translation job
    """
    logger.info(f"User {user['id']} creating translation for chunk_set {translation_request.chunk_set_id}")

    try:
        chunk_set = await get_chunk_set_by_id(translation_request.chunk_set_id)
        if not chunk_set:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Chunk set with ID {translation_request.chunk_set_id} not found"
            )
        
        document = await get_document_by_id(chunk_set.document_id)
        if not document or str(document.user_id) != str(user["id"]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this chunk set or its document"
            )
        
        total_chunks = chunk_set.total_chunks
        if total_chunks is None or total_chunks == 0:
            chunks_in_db = await get_chunks_by_chunk_set_id(translation_request.chunk_set_id)
            total_chunks = len(chunks_in_db)
        
        if total_chunks == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Chunk set has no chunks"
            )

        translation_data = models.TranslationCreate(
            chunk_set_id=translation_request.chunk_set_id,
            user_id=user["id"],
            target_language="auto", 
            name=f"Translation for {translation_request.chunk_set_id}", 
            ai_model="gpt-4o-mini", 
            total_chunks=total_chunks
        )
        
        job = await create_translation_db(UUID(user["id"]), translation_data)
        logger.info(f"Created translation job with ID: {job.id}")
        
        # Immediately set status to in_progress so frontend polling sees it
        updated_job = await update_translation(
            job.id,
            models.TranslationUpdate(status="in_progress")
        )
        logger.info(f"Set translation {job.id} status to in_progress")

        # Start processing in background
        background_tasks.add_task(process_translation_job, job_id=job.id, user_id=user["id"], prompt=translation_request.prompt)

        return schemas.TranslationResponse.model_validate(updated_job, from_attributes=True)
    
    except HTTPException: 
        raise
    except Exception as e:
        error_message = f"Failed to create translation: {str(e)}"
        logger.error(error_message, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_message
        )

# API to list all translations for a user
@router.get("", response_model=schemas.TranslationListResponse)
async def list_translations(
    user = Depends(dependencies.get_current_user)
):
    """
    List all translations for the current user.
    
    Args:
        user: Current authenticated user
        
    Returns:
        List of translations
    """
    try:
        translations = await get_translations_by_user(UUID(user["id"]))
        return {"translations": translations}
        
    except Exception as e:
        logger.error(f"Failed to list translations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list translations: {str(e)}"
        )

@router.get("/{translation_id}", response_model=schemas.TranslationResponse)
async def get_translation(
    translation_id: UUID = Path(..., description="Translation ID"),
    user = Depends(dependencies.get_current_user)
):
    """
    Get a specific translation job with status and progress.
    
    Args:
        translation_id: Translation ID
        user: Current authenticated user
        
    Returns:
        Translation details including status and progress
    """
    try:
        translation = await get_translation_by_id(translation_id)
        
        if not translation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Translation with ID {translation_id} not found"
            )
        
        if str(translation.user_id) != user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this translation"
            )
        
        # Convert to response model and add progress calculation
        response_data = schemas.TranslationResponse.model_validate(translation, from_attributes=True)
        
        # Add progress calculation (even though it's not in the schema, it's useful for clients)
        progress = 0.0
        if translation.total_chunks > 0:
            progress = translation.completed_chunks / translation.total_chunks
        
        # Add progress to the response (clients can calculate this themselves from completed_chunks/total_chunks)
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get translation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get translation: {str(e)}"
        )

@router.delete("/{translation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_translation_endpoint(
    translation_id: UUID = Path(..., description="Translation ID"),
    user = Depends(dependencies.get_current_user)
):
    """
    Delete a translation job.
    
    Args:
        translation_id: Translation ID
        user: Current authenticated user
        
    Returns:
        No content
    """
    try:
        translation = await get_translation_by_id(translation_id)
        
        if not translation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Translation with ID {translation_id} not found"
            )
        
        if str(translation.user_id) != user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to delete this translation"
            )
        
        # Delete translation
        deleted = await delete_translation(translation_id)
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Translation with ID {translation_id} not found"
            )
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete translation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete translation: {str(e)}"
        )

@router.get("/{translation_id}/download")
async def download_translated_document(
    translation_id: UUID = Path(..., description="Translation ID"),
    user = Depends(dependencies.get_current_user)
):
    """
    Download a completed translated document by assembling chunks on-demand.
    
    Args:
        translation_id: Translation ID
        user: Current authenticated user
        
    Returns:
        File download response
    """
    try:
        from fastapi.responses import FileResponse
        
        translation = await get_translation_by_id(translation_id)
        
        if not translation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Translation with ID {translation_id} not found"
            )
        
        if str(translation.user_id) != user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this translation"
            )
        
        # Check if there are any translated chunks to download
        if translation.completed_chunks == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No chunks have been translated yet"
            )
        
        # Assemble document on-demand
        try:
            # Get translation with chunks
            translation_with_chunks = await get_translation_with_chunks(translation_id)
            if not translation_with_chunks:
                raise ValueError(f"Translation with ID {translation_id} not found")
            
            # Get document through chunk set - fix dictionary access
            chunk_set = await get_chunk_set_by_id(translation_with_chunks["chunk_set_id"])
            if not chunk_set:
                raise ValueError(f"Chunk set with ID {translation_with_chunks['chunk_set_id']} not found")
            
            document = await get_document_by_id(chunk_set.document_id)
            if not document:
                raise ValueError(f"Document with ID {chunk_set.document_id} not found")
            
            # Sort chunks by sequence number
            sorted_chunks = sorted(
                translation_with_chunks["translated_chunks"],
                key=lambda x: x.sequence_number
            )
            
            # Combine chunks into a single text
            translated_content = "\n".join(chunk.content for chunk in sorted_chunks)
            
            # Create a file name for the translated document
            original_name = document.name
            name_parts = original_name.rsplit(".", 1)
            base_name = name_parts[0]
            extension = name_parts[1] if len(name_parts) > 1 else ""
            
            # Sanitize target language for filename (remove invalid characters)
            sanitized_target_language = translation_with_chunks["target_language"].replace("/", "_").replace("\\", "_").replace("(", "").replace(")", "").replace(" ", "_")
            translated_file_name = f"{base_name}_{sanitized_target_language}"
            if extension:
                translated_file_name += f".{extension}"
            
            # Create a temporary file for download
            temp_dir = "temp"
            os.makedirs(temp_dir, exist_ok=True)
            temp_file_path = os.path.join(temp_dir, translated_file_name)
            
            with open(temp_file_path, "w", encoding="utf-8") as f:
                f.write(translated_content)
            
            # Return file (FastAPI will clean up the temp file after response)
            return FileResponse(
                temp_file_path,
                filename=translated_file_name,
                media_type="application/octet-stream"
            )
            
        except Exception as assembly_error:
            logger.error(f"Failed to assemble document on-demand: {str(assembly_error)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to assemble document: {str(assembly_error)}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to download translation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download translation: {str(e)}"
        )

@router.post("/{translation_id}/chunks/{chunk_id}/retranslate", response_model=schemas.TranslatedChunkResponse)
async def retranslate_chunk(
    translation_id: UUID = Path(..., description="Translation ID"),
    chunk_id: UUID = Path(..., description="Chunk ID"),
    user = Depends(dependencies.get_current_user)
):
    """
    Re-translate a specific chunk, overwriting any existing translation.
    
    Args:
        translation_id: Translation ID
        chunk_id: Chunk ID
        user: Current authenticated user
        
    Returns:
        Re-translated chunk
    """
    try:
        translation = await get_translation_by_id(translation_id)
        
        if not translation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Translation with ID {translation_id} not found"
            )
        
        if str(translation.user_id) != user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this translation"
            )
        
        # Check if existing translated chunk exists and delete it
        existing_chunk = await get_translated_chunk_by_parent(translation_id, chunk_id)
        
        if existing_chunk:
            await delete_translated_chunk(existing_chunk.id)
            logger.info(f"Deleted existing translated chunk {existing_chunk.id} for re-translation")
        
        # Translate the chunk (this will now create a new one since we deleted the existing one)
        # Note: We need the original prompt for this to work properly
        translated_chunk_id = await translate_chunk(chunk_id, translation_id, "Translate the following text")
        
        if not translated_chunk_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to re-translate chunk"
            )
        
        # Get the newly created translated chunk using unified design
        new_translated_chunk = await get_chunk_by_id(translated_chunk_id)
        
        return schemas.TranslatedChunkResponse.model_validate(new_translated_chunk, from_attributes=True)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to re-translate chunk: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to re-translate chunk: {str(e)}"
        )

@router.get("/{translation_id}/chunks", response_model=schemas.TranslatedChunkListResponse)
async def get_translation_chunks(
    translation_id: UUID = Path(..., description="Translation ID"),
    user = Depends(dependencies.get_current_user)
):
    """
    Get all translated chunks for a specific translation.
    
    Args:
        translation_id: Translation ID
        user: Current authenticated user
        
    Returns:
        List of translated chunks
    """
    try:
        translation = await get_translation_by_id(translation_id)
        
        if not translation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Translation with ID {translation_id} not found"
            )
        
        if str(translation.user_id) != user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this translation"
            )
        
        # Get translated chunks using unified design
        translated_chunks = await get_translated_chunks_by_translation(translation_id)
        
        # Convert to response format
        chunk_responses = [
            schemas.TranslatedChunkResponse.model_validate(chunk, from_attributes=True)
            for chunk in translated_chunks
        ]
        
        return {"translated_chunks": chunk_responses}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get translation chunks: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get translation chunks: {str(e)}"
        )

@router.get("/{translation_id}/details", response_model=schemas.TranslationDetailsResponse)
async def get_translation_details(
    translation_id: UUID = Path(..., description="Translation ID"),
    user = Depends(dependencies.get_current_user)
):
    """
    Get translation details with original and translated chunk pairs for side-by-side comparison.
    
    Args:
        translation_id: Translation ID
        user: Current authenticated user
        
    Returns:
        Translation details with chunk pairs and statistics
    """
    try:
        translation = await get_translation_by_id(translation_id)
        
        if not translation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Translation with ID {translation_id} not found"
            )
        
        if str(translation.user_id) != user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this translation"
            )
        
        # Get original chunks from chunk set
        original_chunks = await get_chunks_by_chunk_set_id(translation.chunk_set_id)
        
        # Get translated chunks
        translated_chunks = await get_translated_chunks_by_translation(translation_id)
        
        # Create a mapping of parent_chunk_id to translated chunk
        translated_chunks_map = {
            chunk.parent_chunk_id: chunk for chunk in translated_chunks
        }
        
        # Create chunk pairs
        chunk_pairs = []
        error_count = 0
        
        for original_chunk in sorted(original_chunks, key=lambda x: x.sequence_number):
            translated_chunk = translated_chunks_map.get(original_chunk.id)
            
            # Check if translated chunk has errors
            if translated_chunk and translated_chunk.metadata.get("status") == "failed":
                error_count += 1
            
            chunk_pair = schemas.ChunkPairResponse(
                original_chunk=original_chunk.model_dump(),
                translated_chunk=schemas.TranslatedChunkResponse.model_validate(translated_chunk, from_attributes=True) if translated_chunk else None,
                sequence_number=original_chunk.sequence_number
            )
            chunk_pairs.append(chunk_pair)
        
        # Calculate success rate
        total_chunks = len(original_chunks)
        success_count = total_chunks - error_count
        success_rate = (success_count / total_chunks) * 100 if total_chunks > 0 else 0
        
        return schemas.TranslationDetailsResponse(
            translation=schemas.TranslationResponse.model_validate(translation, from_attributes=True),
            chunk_pairs=chunk_pairs,
            success_rate=success_rate,
            error_count=error_count,
            total_chunks=total_chunks
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get translation details: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get translation details: {str(e)}"
        ) 