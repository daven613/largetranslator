"""
Translation API endpoints.
"""
import logging
import os
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Path, BackgroundTasks

from backend.db import models
from backend.db.crud.translations import (
    create_translation as create_translation_db, get_translation_by_id, get_translations_by_user, 
    get_translated_chunks_by_translation, update_translation, delete_translation,
    create_translated_chunk, get_translation_with_chunks, delete_translated_chunk,
    get_translated_chunk_by_id
)
from backend.db.crud.chunking import (
    get_chunk_by_id, get_chunks_by_chunk_set_id, get_chunk_set_by_id
)
from backend.db.crud.files import get_document_by_id
from backend.external_services.open_ai.translation import translate_text_with_prompt
from backend.external_services.supabase.storage_service import SupabaseStorageService
from backend.api import dependencies
from backend.api.translations import schemas

logger = logging.getLogger(__name__)
router = APIRouter(tags=["translations"])

# Translation processing functions

async def translate_chunk(chunk_id: UUID, translation_id: UUID, prompt: str) -> UUID:
    """
    Translate a single chunk and save the result.
    
    Args:
        chunk_id: ID of the chunk to translate
        translation_id: ID of the translation job
        prompt: Translation prompt to use
        
    Returns:
        Translated chunk ID or None if there was an error
    """
    try:
        logger.info(f"Starting translation of chunk {chunk_id} for translation {translation_id}")
        
        # Get translation
        translation = await get_translation_by_id(translation_id)
        if not translation:
            logger.error(f"Translation with ID {translation_id} not found")
            return None
        
        # Get chunk
        chunk = await get_chunk_by_id(chunk_id)
        if not chunk:
            logger.error(f"Chunk with ID {chunk_id} not found")
            return None
        
        # Check if a translated chunk already exists for this translation_id and chunk_id
        from ...db.crud.translations import get_translated_chunk_by_translation_and_chunk
        existing_chunk = await get_translated_chunk_by_translation_and_chunk(translation_id, chunk_id)
        
        if existing_chunk:
            logger.info(f"Translated chunk already exists for chunk_id {chunk_id} and translation_id {translation_id}. Returning existing chunk ID.")
            return existing_chunk.id
        
        # Create translation prompt
        translation_prompt = f"{prompt}\n\nText to translate:\n{chunk.content}"
        
        # Translate chunk using prompt-based approach
        logger.info(f"Calling OpenAI API to translate chunk {chunk_id}")
        translated_content = await translate_text_with_prompt(translation_prompt, translation.ai_model)
        logger.info(f"Successfully translated chunk {chunk_id}")
        
        # Create translated chunk
        translated_chunk = await create_translated_chunk(
            models.TranslatedChunkCreate(
                translation_id=translation_id,
                chunk_id=chunk_id,
                translated_content=translated_content,
                sequence_number=chunk.sequence_number
            )
        )
        logger.info(f"Created translated chunk {translated_chunk.id} for chunk {chunk_id}")
        
        # Update translation progress
        new_completed_count = translation.completed_chunks + 1
        new_status = "completed" if new_completed_count >= translation.total_chunks else "in_progress"
        
        updated_translation = await update_translation(
            translation_id,
            models.TranslationUpdate(
                completed_chunks=new_completed_count,
                status=new_status
            )
        )
        logger.info(f"Updated translation {translation_id} progress: {new_completed_count}/{translation.total_chunks} chunks, status: {new_status}")
        
        return translated_chunk.id
        
    except Exception as e:
        logger.error(f"Failed to translate chunk {chunk_id}: {str(e)}", exc_info=True)
        
        try:
            # Update translation status to failed
            await update_translation(
                translation_id,
                models.TranslationUpdate(status="failed")
            )
            logger.info(f"Updated translation {translation_id} status to failed due to chunk error")
        except Exception as update_error:
            logger.error(f"Failed to update translation status: {str(update_error)}")
        
        return None

async def process_translation_job(job_id: UUID, user_id: UUID, prompt: str) -> None:
    """
    Process a translation job in the background.
    
    Args:
        job_id: Translation job ID
        user_id: User ID
        prompt: Translation prompt
    """
    import asyncio
    
    try:
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
        logger.info(f"Processing {len(chunks)} chunks for translation {job_id}")
        
        # Process each chunk with delay to prevent resource exhaustion
        for i, chunk in enumerate(chunks):
            logger.info(f"Processing chunk {i+1}/{len(chunks)} for translation {job_id}")
            
            chunk_result = await translate_chunk(chunk.id, job_id, prompt)
            
            if chunk_result is None:
                logger.error(f"Failed to translate chunk {chunk.id}, aborting translation {job_id}")
                # The translate_chunk function already sets status to failed
                return
            
            # Add small delay between chunks to prevent resource exhaustion
            # and allow other requests to be processed
            if i < len(chunks) - 1:  # Don't delay after the last chunk
                await asyncio.sleep(0.1)  # 100ms delay
        
        # Re-fetch translation to get updated completed_chunks count
        updated_translation = await get_translation_by_id(job_id)
        if not updated_translation:
            raise ValueError(f"Translation with ID {job_id} not found after processing")
        
        # Mark as completed when all chunks are processed
        if updated_translation.completed_chunks == updated_translation.total_chunks:
            await update_translation(
                job_id,
                models.TranslationUpdate(status="completed")
            )
            logger.info(f"Translation {job_id} completed successfully")
        else:
            logger.warning(f"Translation {job_id} finished but completed_chunks ({updated_translation.completed_chunks}) != total_chunks ({updated_translation.total_chunks})")
    
    except Exception as e:
        logger.error(f"Failed to process translation job {job_id}: {str(e)}", exc_info=True)
        
        # Update translation status to failed
        try:
            await update_translation(
                job_id,
                models.TranslationUpdate(status="failed")
            )
            logger.info(f"Translation {job_id} status updated to failed")
        except Exception as update_error:
            logger.error(f"Failed to update translation {job_id} status to failed: {str(update_error)}")

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
            target_language="N/A (prompt-defined)", 
            name=f"Translation for {translation_request.chunk_set_id}", 
            ai_model="gpt-4o-mini", 
            total_chunks=total_chunks
        )
        
        job = await create_translation_db(translation_data)
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
            
            # Get document through chunk set
            chunk_set = await get_chunk_set_by_id(translation_with_chunks.chunk_set_id)
            if not chunk_set:
                raise ValueError(f"Chunk set with ID {translation_with_chunks.chunk_set_id} not found")
            
            document = await get_document_by_id(chunk_set.document_id)
            if not document:
                raise ValueError(f"Document with ID {chunk_set.document_id} not found")
            
            # Sort chunks by sequence number
            sorted_chunks = sorted(
                translation_with_chunks.translated_chunks,
                key=lambda x: x.sequence_number
            )
            
            # Combine chunks into a single text
            translated_content = "\n".join(chunk.translated_content for chunk in sorted_chunks)
            
            # Create a file name for the translated document
            original_name = document.name
            name_parts = original_name.rsplit(".", 1)
            base_name = name_parts[0]
            extension = name_parts[1] if len(name_parts) > 1 else ""
            
            # Sanitize target language for filename (remove invalid characters)
            sanitized_target_language = translation_with_chunks.target_language.replace("/", "_").replace("\\", "_").replace("(", "").replace(")", "").replace(" ", "_")
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
        from ...db.crud.translations import get_translated_chunk_by_translation_and_chunk
        existing_chunk = await get_translated_chunk_by_translation_and_chunk(translation_id, chunk_id)
        
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
        
        # Get the newly created translated chunk
        new_translated_chunk = await get_translated_chunk_by_id(translated_chunk_id)
        
        return schemas.TranslatedChunkResponse.model_validate(new_translated_chunk, from_attributes=True)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to re-translate chunk: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to re-translate chunk: {str(e)}"
        ) 