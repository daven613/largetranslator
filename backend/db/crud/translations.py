"""
CRUD operations for translations and translated chunks.
"""
import logging
from typing import Dict, List, Optional, Any
from uuid import UUID
from datetime import datetime
import uuid

from pydantic import UUID4

from ...helpers.json_utils import convert_uuids_to_str
from .. import models
from ..async_client import get_db_client

logger = logging.getLogger(__name__)

# Translation operations

async def create_translation(user_id: uuid.UUID, translation_data: models.TranslationCreate) -> models.Translation:
    """
    Create a new translation.
    
    Args:
        user_id: User ID
        translation_data: Translation data
        
    Returns:
        Created translation
    """
    try:
        db = await get_db_client()
        
        # Prepare translation data for insertion
        translation_dict = {
            "user_id": str(user_id),
            "chunk_set_id": str(translation_data.chunk_set_id),
            "target_language": translation_data.target_language,
            "name": translation_data.name,
            "ai_model": translation_data.ai_model,
            "status": "pending",
            "completed_chunks": 0,
            "total_chunks": translation_data.total_chunks,
            "output_file_path": None,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Insert translation
        result = await db.insert_returning("translations", translation_dict)
        
        if result:
            return models.Translation(**result)
        else:
            raise Exception("Failed to create translation")
            
    except Exception as e:
        logger.error(f"Error creating translation: {str(e)}")
        raise


async def get_translation_by_id(translation_id: UUID, user_id: Optional[UUID] = None) -> Optional[models.Translation]:
    """
    Get a translation by ID, optionally filtering by user.
    
    Args:
        translation_id: Translation ID
        user_id: User ID
        
    Returns:
        Translation or None if not found
    """
    try:
        db = await get_db_client()
        
        # Build filters
        filters = {"id": str(translation_id)}
        if user_id:
            filters["user_id"] = str(user_id)
        
        # Fetch translation
        result = await db.fetch_one("translations", filters=filters)
        
        if result:
            return models.Translation(**result)
        return None
        
    except Exception as e:
        logger.error(f"Error fetching translation {translation_id}: {str(e)}")
        raise


async def get_translations_by_user(user_id: UUID) -> List[models.Translation]:
    """
    Get all translations for a user.
    
    Args:
        user_id: User ID
        
    Returns:
        List of translations
    """
    try:
        db = await get_db_client()
        
        # Fetch translations for user
        results = await db.fetch_all(
            "translations", 
            filters={"user_id": str(user_id)},
            select="*"
        )
        
        return [models.Translation(**trans) for trans in results]
        
    except Exception as e:
        logger.error(f"Error fetching translations for user {user_id}: {str(e)}")
        raise


async def get_translations_by_chunk_set(chunk_set_id: UUID) -> List[models.Translation]:
    """
    Get all translations for a chunk set.
    
    Args:
        chunk_set_id: Chunk set ID
        
    Returns:
        List of translations
    """
    try:
        db = await get_db_client()
        
        # Get translations
        results = await db.fetch_all(
            "translations", 
            filters={"chunk_set_id": str(chunk_set_id)},
            select="*"
        )
        
        return [models.Translation(**translation) for translation in results]
    except Exception as e:
        logger.error(f"Failed to get translations for chunk set: {str(e)}")
        raise


async def update_translation(translation_id: UUID, update_data: models.TranslationUpdate, user_id: Optional[UUID] = None) -> Optional[models.Translation]:
    """
    Update a translation.
    
    Args:
        translation_id: Translation ID
        update_data: Data to update
        user_id: User ID
        
    Returns:
        Updated translation or None if not found
    """
    try:
        db = await get_db_client()
        
        # Prepare update data (exclude None values)
        update_dict = {}
        if update_data.status is not None:
            update_dict["status"] = update_data.status
        if update_data.completed_chunks is not None:
            update_dict["completed_chunks"] = update_data.completed_chunks
        if update_data.output_file_path is not None:
            update_dict["output_file_path"] = update_data.output_file_path
        
        # Always update the updated_at timestamp
        update_dict["updated_at"] = datetime.utcnow().isoformat()
        
        if not update_dict:
            # No fields to update
            return await get_translation_by_id(translation_id, user_id)
        
        # Build filters
        filters = {"id": str(translation_id)}
        if user_id:
            filters["user_id"] = str(user_id)
        
        # Update translation
        result = await db.update_returning("translations", update_dict, filters)
        
        if result:
            return models.Translation(**result)
        return None
        
    except Exception as e:
        logger.error(f"Error updating translation {translation_id}: {str(e)}")
        raise


async def delete_translation(translation_id: UUID, user_id: Optional[UUID] = None) -> bool:
    """
    Delete a translation.
    
    Args:
        translation_id: Translation ID
        user_id: User ID
        
    Returns:
        True if deleted, False if not found
    """
    try:
        db = await get_db_client()
        
        # Build filters
        filters = {"id": str(translation_id)}
        if user_id:
            filters["user_id"] = str(user_id)
        
        # First delete all translated chunks for this translation
        await db.delete_returning("chunks", {
            "translation_id": str(translation_id),
            "chunk_type": "translated"
        })
        
        # Then delete the translation
        result = await db.delete_returning("translations", filters)
        
        return result is not None
        
    except Exception as e:
        logger.error(f"Error deleting translation {translation_id}: {str(e)}")
        raise


# Translated chunks using unified chunks table

async def create_translated_chunk(
    translation_id: uuid.UUID,
    parent_chunk_id: uuid.UUID,
    translated_content: str,
    sequence_number: int,
    target_language: str,
    document_id: uuid.UUID,
    metadata: Optional[Dict[str, Any]] = None
) -> models.Chunk:
    """
    Create a translated chunk using the unified chunks table.
    
    Args:
        translation_id: Translation ID
        parent_chunk_id: Original chunk ID
        translated_content: Translated content
        sequence_number: Sequence number
        target_language: Target language
        document_id: Document ID
        metadata: Optional metadata
        
    Returns:
        Created translated chunk
    """
    try:
        db = await get_db_client()
        
        # Prepare chunk data for insertion using provided document_id
        chunk_dict = {
            "document_id": str(document_id),
            "chunk_set_id": None,  # Will be set to None for translated chunks
            "parent_chunk_id": str(parent_chunk_id),
            "translation_id": str(translation_id),
            "sequence_number": sequence_number,
            "content": translated_content,
            "chunk_type": "translated",
            "target_language": target_language,
            "metadata": metadata or {},
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Insert translated chunk
        result = await db.insert_returning("chunks", chunk_dict)
        
        if result:
            return models.Chunk(**result)
        else:
            raise Exception("Failed to create translated chunk")
            
    except Exception as e:
        logger.error(f"Error creating translated chunk: {str(e)}")
        raise


async def get_translated_chunks_by_translation(translation_id: uuid.UUID) -> List[models.Chunk]:
    """
    Get all translated chunks for a translation using the unified chunks table.
    
    Args:
        translation_id: Translation ID
        
    Returns:
        List of translated chunks
    """
    try:
        db = await get_db_client()
        
        # Fetch translated chunks for translation
        results = await db.fetch_all(
            "chunks", 
            filters={
                "translation_id": str(translation_id),
                "chunk_type": "translated"
            },
            select="*"
        )
        
        # Sort by sequence_number
        chunks = [models.Chunk(**chunk) for chunk in results]
        chunks.sort(key=lambda x: x.sequence_number or 0)
        
        return chunks
        
    except Exception as e:
        logger.error(f"Error fetching translated chunks for translation {translation_id}: {str(e)}")
        raise


async def get_translated_chunk_by_parent(translation_id: uuid.UUID, parent_chunk_id: uuid.UUID) -> Optional[models.Chunk]:
    """
    Get translated chunk by translation ID and parent chunk ID.
    
    Args:
        translation_id: Translation ID
        parent_chunk_id: Parent chunk ID
        
    Returns:
        Translated chunk or None if not found
    """
    try:
        db = await get_db_client()
        
        # Get translated chunk
        result = await db.fetch_one(
            "chunks", 
            filters={
                "translation_id": str(translation_id),
                "parent_chunk_id": str(parent_chunk_id),
                "chunk_type": "translated"
            }
        )
        
        if not result:
            return None
        
        return models.Chunk(**result)
    except Exception as e:
        logger.error(f"Failed to get translated chunk by parent: {str(e)}")
        raise


async def update_translated_chunk(chunk_id: uuid.UUID, translated_content: str, metadata: Optional[Dict[str, Any]] = None) -> models.Chunk:
    """
    Update a translated chunk.
    
    Args:
        chunk_id: Chunk ID
        translated_content: New translated content
        metadata: Optional metadata updates
        
    Returns:
        Updated chunk
    """
    try:
        db = await get_db_client()
        
        update_data = {
            'content': translated_content,
            'updated_at': datetime.utcnow().isoformat()
        }
        
        if metadata is not None:
            update_data['metadata'] = metadata
        
        # Update chunk
        result = await db.update_returning("chunks", update_data, {"id": str(chunk_id)})
        
        if not result:
            raise ValueError(f"Chunk with ID {chunk_id} not found")
        
        return models.Chunk(**result)
    except Exception as e:
        logger.error(f"Failed to update translated chunk: {str(e)}")
        raise


async def delete_translated_chunk(chunk_id: uuid.UUID) -> bool:
    """
    Delete a translated chunk.
    
    Args:
        chunk_id: Chunk ID
        
    Returns:
        True if deleted, False if not found
    """
    try:
        db = await get_db_client()
        
        # Delete translated chunk
        result = await db.delete_returning("chunks", {
            "id": str(chunk_id),
            "chunk_type": "translated"
        })
        
        return result is not None
    except Exception as e:
        logger.error(f"Failed to delete translated chunk: {str(e)}")
        raise


async def get_translation_with_chunks(translation_id: uuid.UUID) -> Optional[Dict[str, Any]]:
    """
    Get a translation with all its translated chunks.
    
    Args:
        translation_id: Translation ID
        
    Returns:
        Translation with chunks or None if not found
    """
    try:
        # Get translation
        translation = await get_translation_by_id(translation_id)
        if not translation:
            return None
        
        # Get translated chunks
        translated_chunks = await get_translated_chunks_by_translation(translation_id)
        
        # Create response with chunks
        result = translation.model_dump()
        result["translated_chunks"] = translated_chunks
        
        return result
    except Exception as e:
        logger.error(f"Failed to get translation with chunks: {str(e)}")
        raise


# Legacy functions for backward compatibility

async def create_translated_chunk_legacy(translated_chunk: models.TranslatedChunkCreate) -> models.TranslatedChunk:
    """
    Legacy function for creating translated chunks.
    """
    logger.warning("Using legacy create_translated_chunk_legacy function")
    raise NotImplementedError("Legacy function not implemented with async client")


async def get_translated_chunk_by_id(translated_chunk_id: UUID) -> Optional[models.TranslatedChunk]:
    """
    Legacy function for getting translated chunks by ID.
    """
    logger.warning("Using legacy get_translated_chunk_by_id function")
    raise NotImplementedError("Legacy function not implemented with async client")


async def get_translated_chunk_by_translation_and_chunk(translation_id: UUID, chunk_id: UUID) -> Optional[models.TranslatedChunk]:
    """
    Legacy function for getting translated chunks.
    """
    logger.warning("Using legacy get_translated_chunk_by_translation_and_chunk function")
    raise NotImplementedError("Legacy function not implemented with async client") 