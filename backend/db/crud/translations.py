"""
CRUD operations for translations and translated chunks.
"""
import logging
from typing import Dict, List, Optional, Any
from uuid import UUID

from pydantic import UUID4

from ...external_services.supabase.client import get_supabase_client
from ...helpers.json_utils import convert_uuids_to_str
from .. import models

logger = logging.getLogger(__name__)

# Translation operations

async def create_translation(translation: models.TranslationCreate) -> models.Translation:
    """
    Create a new translation.
    
    Args:
        translation: Translation data
        
    Returns:
        Created translation
    """
    try:
        client = get_supabase_client()
        
        # Convert to dict and ensure UUIDs are strings
        translation_dict = convert_uuids_to_str(translation.model_dump())
        
        # Create translation
        result = client.table('translations').insert(translation_dict).execute()
        created_translation = result.data[0]
        
        return models.Translation(**created_translation)
    except Exception as e:
        logger.error(f"Failed to create translation: {str(e)}")
        raise


async def get_translation_by_id(translation_id: UUID) -> Optional[models.Translation]:
    """
    Get a translation by ID.
    
    Args:
        translation_id: Translation ID
        
    Returns:
        Translation or None if not found
    """
    try:
        client = get_supabase_client()
        
        # Get translation
        result = client.table('translations').select('*').eq('id', str(translation_id)).execute()
        
        if not result.data:
            return None
            
        return models.Translation(**result.data[0])
    except Exception as e:
        logger.error(f"Failed to get translation: {str(e)}")
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
        client = get_supabase_client()
        
        # Get translations
        result = client.table('translations').select('*').eq('user_id', str(user_id)).order('created_at').execute()
        
        return [models.Translation(**translation) for translation in result.data]
    except Exception as e:
        logger.error(f"Failed to get translations for user: {str(e)}")
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
        client = get_supabase_client()
        
        # Get translations
        result = client.table('translations').select('*').eq('chunk_set_id', str(chunk_set_id)).order('created_at').execute()
        
        return [models.Translation(**translation) for translation in result.data]
    except Exception as e:
        logger.error(f"Failed to get translations for chunk set: {str(e)}")
        raise


async def update_translation(translation_id: UUID, update_data: models.TranslationUpdate) -> models.Translation:
    """
    Update a translation.
    
    Args:
        translation_id: Translation ID
        update_data: Data to update
        
    Returns:
        Updated translation
    """
    try:
        client = get_supabase_client()
        
        # Filter out None values and convert UUIDs to strings
        update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
        update_dict = convert_uuids_to_str(update_dict)
        
        # Update translation
        result = client.table('translations').update(update_dict).eq('id', str(translation_id)).execute()
        
        if not result.data:
            raise ValueError(f"Translation with ID {translation_id} not found")
        
        return models.Translation(**result.data[0])
    except Exception as e:
        logger.error(f"Failed to update translation: {str(e)}")
        raise


async def delete_translation(translation_id: UUID) -> bool:
    """
    Delete a translation.
    
    Args:
        translation_id: Translation ID
        
    Returns:
        True if deleted, False if not found
    """
    try:
        client = get_supabase_client()
        
        # Delete translation
        result = client.table('translations').delete().eq('id', str(translation_id)).execute()
        
        return len(result.data) > 0
    except Exception as e:
        logger.error(f"Failed to delete translation: {str(e)}")
        raise


# Translated chunk operations

async def create_translated_chunk(translated_chunk: models.TranslatedChunkCreate) -> models.TranslatedChunk:
    """
    Create a new translated chunk.
    
    Args:
        translated_chunk: Translated chunk data
        
    Returns:
        Created translated chunk
    """
    try:
        client = get_supabase_client()
        
        # Convert to dict and ensure UUIDs are strings
        translated_chunk_dict = convert_uuids_to_str(translated_chunk.model_dump())
        
        # Create translated chunk
        result = client.table('translated_chunks').insert(translated_chunk_dict).execute()
        created_translated_chunk = result.data[0]
        
        return models.TranslatedChunk(**created_translated_chunk)
    except Exception as e:
        logger.error(f"Failed to create translated chunk: {str(e)}")
        raise


async def get_translated_chunk_by_id(translated_chunk_id: UUID) -> Optional[models.TranslatedChunk]:
    """
    Get a translated chunk by ID.
    
    Args:
        translated_chunk_id: Translated chunk ID
        
    Returns:
        Translated chunk or None if not found
    """
    try:
        client = get_supabase_client()
        
        # Get translated chunk
        result = client.table('translated_chunks').select('*').eq('id', str(translated_chunk_id)).execute()
        
        if not result.data:
            return None
            
        return models.TranslatedChunk(**result.data[0])
    except Exception as e:
        logger.error(f"Failed to get translated chunk: {str(e)}")
        raise


async def get_translated_chunks_by_translation(translation_id: UUID) -> List[models.TranslatedChunk]:
    """
    Get all translated chunks for a translation.
    
    Args:
        translation_id: Translation ID
        
    Returns:
        List of translated chunks
    """
    try:
        client = get_supabase_client()
        
        # Get translated chunks
        result = client.table('translated_chunks').select('*').eq('translation_id', str(translation_id)).order('sequence_number').execute()
        
        return [models.TranslatedChunk(**translated_chunk) for translated_chunk in result.data]
    except Exception as e:
        logger.error(f"Failed to get translated chunks for translation: {str(e)}")
        raise


async def update_translated_chunk(translated_chunk_id: UUID, update_data: models.TranslatedChunkUpdate) -> models.TranslatedChunk:
    """
    Update a translated chunk.
    
    Args:
        translated_chunk_id: Translated chunk ID
        update_data: Data to update
        
    Returns:
        Updated translated chunk
    """
    try:
        client = get_supabase_client()
        
        # Filter out None values and convert UUIDs to strings
        update_dict = {k: v for k, v in update_data.dict().items() if v is not None}
        update_dict = convert_uuids_to_str(update_dict)
        
        # Update translated chunk
        result = client.table('translated_chunks').update(update_dict).eq('id', str(translated_chunk_id)).execute()
        
        if not result.data:
            raise ValueError(f"Translated chunk with ID {translated_chunk_id} not found")
            
        return models.TranslatedChunk(**result.data[0])
    except Exception as e:
        logger.error(f"Failed to update translated chunk: {str(e)}")
        raise


async def delete_translated_chunk(translated_chunk_id: UUID) -> bool:
    """
    Delete a translated chunk.
    
    Args:
        translated_chunk_id: Translated chunk ID
        
    Returns:
        True if deleted, False if not found
    """
    try:
        client = get_supabase_client()
        
        # Delete translated chunk
        result = client.table('translated_chunks').delete().eq('id', str(translated_chunk_id)).execute()
        
        return len(result.data) > 0
    except Exception as e:
        logger.error(f"Failed to delete translated chunk: {str(e)}")
        raise


async def get_translation_with_chunks(translation_id: UUID) -> Optional[models.TranslationWithChunks]:
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
        
        # Create combined model
        translation_dict = translation.model_dump()
        translation_dict["translated_chunks"] = translated_chunks
        
        return models.TranslationWithChunks(**translation_dict)
    except Exception as e:
        logger.error(f"Failed to get translation with chunks: {str(e)}")
        raise


async def get_translated_chunk_by_translation_and_chunk(translation_id: UUID, chunk_id: UUID) -> Optional[models.TranslatedChunk]:
    """
    Get a translated chunk by translation ID and chunk ID.
    
    Args:
        translation_id: Translation ID
        chunk_id: Chunk ID
        
    Returns:
        Translated chunk or None if not found
    """
    try:
        client = get_supabase_client()
        
        # Get translated chunk by translation_id and chunk_id
        result = client.table('translated_chunks').select('*').eq('translation_id', str(translation_id)).eq('chunk_id', str(chunk_id)).execute()
        
        if not result.data:
            return None
            
        return models.TranslatedChunk(**result.data[0])
    except Exception as e:
        logger.error(f"Failed to get translated chunk by translation and chunk: {str(e)}")
        raise 