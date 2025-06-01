"""
CRUD operations for chunks and chunk sets.
"""
import logging
from typing import Dict, List, Optional, Any
from uuid import UUID

from pydantic import UUID4

from ...external_services.supabase.client import get_supabase_client
from ...helpers.json_utils import convert_uuids_to_str
from .. import models

logger = logging.getLogger(__name__)

# Chunk operations

async def create_chunk(chunk: models.ChunkCreate) -> models.Chunk:
    """
    Create a new chunk.
    
    Args:
        chunk: Chunk data
        
    Returns:
        Created chunk
    """
    try:
        client = get_supabase_client()
        
        # Convert to dict and ensure UUIDs are strings
        chunk_dict = convert_uuids_to_str(chunk.model_dump())
        
        # Create chunk
        result = client.table('chunks').insert(chunk_dict).execute()
        created_chunk = result.data[0]
        
        return models.Chunk(**created_chunk)
    except Exception as e:
        logger.error(f"Failed to create chunk: {str(e)}")
        raise


async def create_chunks(chunks: List[models.ChunkCreate]) -> List[models.Chunk]:
    """
    Create multiple chunks at once.
    
    Args:
        chunks: List of chunk data
        
    Returns:
        List of created chunks
    """
    try:
        if not chunks:
            return []
            
        client = get_supabase_client()
        
        # Convert to dicts and ensure UUIDs are strings
        chunks_data = [convert_uuids_to_str(chunk.model_dump()) for chunk in chunks]
        
        # Create chunks
        result = client.table('chunks').insert(chunks_data).execute()
        created_chunks = result.data
        
        return [models.Chunk(**chunk) for chunk in created_chunks]
    except Exception as e:
        logger.error(f"Failed to create chunks: {str(e)}")
        raise


async def get_chunk_by_id(chunk_id: UUID4) -> Optional[models.Chunk]:
    """
    Get a chunk by ID.
    
    Args:
        chunk_id: Chunk ID
        
    Returns:
        Chunk or None if not found
    """
    try:
        client = get_supabase_client()
        
        # Get chunk
        result = client.table('chunks').select('*').eq('id', str(chunk_id)).execute()
        
        if not result.data:
            return None
            
        return models.Chunk(**result.data[0])
    except Exception as e:
        logger.error(f"Failed to get chunk: {str(e)}")
        raise


async def get_chunks_by_document(document_id: UUID4) -> List[models.Chunk]:
    """
    Get all chunks for a document.
    
    Args:
        document_id: Document ID
        
    Returns:
        List of chunks
    """
    try:
        client = get_supabase_client()
        
        # Get chunks
        result = client.table('chunks').select('*').eq('document_id', str(document_id)).order('sequence_number').execute()
        
        return [models.Chunk(**chunk) for chunk in result.data]
    except Exception as e:
        logger.error(f"Failed to get chunks for document: {str(e)}")
        raise


async def get_chunks_by_chunk_set_id(chunk_set_id: UUID4) -> List[models.Chunk]:
    """
    Retrieve all chunks from a specific chunk set.
    
    Args:
        chunk_set_id: Chunk set ID
        
    Returns:
        List of chunk objects sorted by sequence_number
    """
    try:
        client = get_supabase_client()
        
        # Get chunks with the chunk_set_id
        result = client.table('chunks').select('*').eq('chunk_set_id', str(chunk_set_id)).order('sequence_number').execute()
        
        return [models.Chunk(**chunk) for chunk in result.data]
    except Exception as e:
        logger.error(f"Failed to get chunks by chunk set ID: {str(e)}")
        raise


async def search_chunks_by_content(user_id: UUID4, search_text: str) -> List[Dict[str, Any]]:
    """
    Search for chunks containing specific text.
    
    Args:
        user_id: User ID
        search_text: Text to search for
        
    Returns:
        Array of matching chunks with document metadata
    """
    try:
        client = get_supabase_client()
        
        # This query requires a special function in Supabase
        # Using a raw SQL query for text search
        query = f"""
        SELECT c.*, d.name as document_name, d.user_id
        FROM chunks c
        JOIN documents d ON c.document_id = d.id
        WHERE d.user_id = '{user_id}'
        AND c.content ILIKE '%{search_text}%'
        ORDER BY c.document_id, c.sequence_number
        """
        
        result = client.rpc('run_query', {'query': query}).execute()
        
        return result.data
    except Exception as e:
        logger.error(f"Failed to search chunks by content: {str(e)}")
        raise


async def search_chunks_by_vector(
    user_id: UUID4,
    query_vector: List[float],
    similarity_threshold: float = 0.5,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Semantic search using vector embeddings.
    
    Args:
        user_id: User ID
        query_vector: Vector embedding of the query
        similarity_threshold: Minimum similarity score (0-1)
        limit: Maximum number of results
        
    Returns:
        Array of chunks sorted by similarity
    """
    try:
        client = get_supabase_client()
        
        # This query requires pgvector extension and a special function in Supabase
        query = f"""
        SELECT c.*, d.name as document_name, d.user_id,
               1 - (c.embedding <=> '{query_vector}'::vector) as similarity
        FROM chunks c
        JOIN documents d ON c.document_id = d.id
        WHERE d.user_id = '{user_id}'
        AND 1 - (c.embedding <=> '{query_vector}'::vector) > {similarity_threshold}
        ORDER BY similarity DESC
        LIMIT {limit}
        """
        
        result = client.rpc('run_query', {'query': query}).execute()
        
        return result.data
    except Exception as e:
        logger.error(f"Failed to search chunks by vector: {str(e)}")
        raise


async def update_chunk(chunk_id: UUID4, update_data: models.ChunkUpdate) -> models.Chunk:
    """
    Update a chunk.
    
    Args:
        chunk_id: Chunk ID
        update_data: Data to update
        
    Returns:
        Updated chunk
    """
    try:
        client = get_supabase_client()
        
        # Filter out None values and convert UUIDs to strings
        update_dict = {k: v for k, v in update_data.dict().items() if v is not None}
        update_dict = convert_uuids_to_str(update_dict)
        
        # Update chunk
        result = client.table('chunks').update(update_dict).eq('id', str(chunk_id)).execute()
        
        if not result.data:
            raise ValueError(f"Chunk with ID {chunk_id} not found")
            
        return models.Chunk(**result.data[0])
    except Exception as e:
        logger.error(f"Failed to update chunk: {str(e)}")
        raise


async def update_chunk_embedding(chunk_id: UUID4, embedding: List[float]) -> models.Chunk:
    """
    Update the vector embedding for a chunk.
    
    Args:
        chunk_id: Chunk ID
        embedding: Vector embedding
        
    Returns:
        Updated chunk
    """
    try:
        client = get_supabase_client()
        
        # Update chunk embedding
        result = client.table('chunks').update({'embedding': embedding}).eq('id', str(chunk_id)).execute()
        
        if not result.data:
            raise ValueError(f"Chunk with ID {chunk_id} not found")
            
        return models.Chunk(**result.data[0])
    except Exception as e:
        logger.error(f"Failed to update chunk embedding: {str(e)}")
        raise


async def delete_chunk(chunk_id: UUID4) -> bool:
    """
    Delete a chunk.
    
    Args:
        chunk_id: Chunk ID
        
    Returns:
        True if deleted, False if not found
    """
    try:
        client = get_supabase_client()
        
        # Delete chunk
        result = client.table('chunks').delete().eq('id', str(chunk_id)).execute()
        
        return len(result.data) > 0
    except Exception as e:
        logger.error(f"Failed to delete chunk: {str(e)}")
        raise


async def delete_chunks_by_document(document_id: UUID4) -> int:
    """
    Delete all chunks for a document.
    
    Args:
        document_id: Document ID
        
    Returns:
        Number of chunks deleted
    """
    try:
        client = get_supabase_client()
        
        # Delete chunks
        result = client.table('chunks').delete().eq('document_id', str(document_id)).execute()
        
        return len(result.data)
    except Exception as e:
        logger.error(f"Failed to delete chunks for document: {str(e)}")
        raise


# Chunk set operations

async def create_chunk_set(chunk_set: models.ChunkSetCreate) -> models.ChunkSet:
    """
    Create a new chunk set.
    
    Args:
        chunk_set: Chunk set data
        
    Returns:
        Created chunk set
    """
    try:
        client = get_supabase_client()
        
        # Convert to dict and ensure UUIDs are strings
        chunk_set_dict = convert_uuids_to_str(chunk_set.model_dump())
        
        # Create chunk set
        result = client.table('chunk_sets').insert(chunk_set_dict).execute()
        created_chunk_set = result.data[0]
        
        return models.ChunkSet(**created_chunk_set)
    except Exception as e:
        logger.error(f"Failed to create chunk set: {str(e)}")
        raise


async def get_chunk_set_by_id(chunk_set_id: UUID4) -> Optional[models.ChunkSet]:
    """
    Get a chunk set by ID.
    
    Args:
        chunk_set_id: Chunk set ID
        
    Returns:
        Chunk set or None if not found
    """
    try:
        client = get_supabase_client()
        
        # Get chunk set
        result = client.table('chunk_sets').select('*').eq('id', str(chunk_set_id)).execute()
        
        if not result.data:
            return None
            
        return models.ChunkSet(**result.data[0])
    except Exception as e:
        logger.error(f"Failed to get chunk set: {str(e)}")
        raise


async def get_chunk_sets_by_document(document_id: UUID4) -> List[models.ChunkSet]:
    """
    Get all chunk sets for a document.
    
    Args:
        document_id: Document ID
        
    Returns:
        List of chunk sets
    """
    try:
        client = get_supabase_client()
        
        # Get chunk sets
        result = client.table('chunk_sets').select('*').eq('document_id', str(document_id)).order('created_at').execute()
        
        return [models.ChunkSet(**chunk_set) for chunk_set in result.data]
    except Exception as e:
        logger.error(f"Failed to get chunk sets for document: {str(e)}")
        raise


async def update_chunk_set(chunk_set_id: UUID4, update_data: models.ChunkSetUpdate) -> models.ChunkSet:
    """
    Update a chunk set.
    
    Args:
        chunk_set_id: Chunk set ID
        update_data: Data to update
        
    Returns:
        Updated chunk set
    """
    try:
        client = get_supabase_client()
        
        # Filter out None values and convert UUIDs to strings
        update_dict = {k: v for k, v in update_data.dict().items() if v is not None}
        update_dict = convert_uuids_to_str(update_dict)
        
        # Update chunk set
        result = client.table('chunk_sets').update(update_dict).eq('id', str(chunk_set_id)).execute()
        
        if not result.data:
            raise ValueError(f"Chunk set with ID {chunk_set_id} not found")
            
        return models.ChunkSet(**result.data[0])
    except Exception as e:
        logger.error(f"Failed to update chunk set: {str(e)}")
        raise


async def delete_chunk_set(chunk_set_id: UUID4) -> bool:
    """
    Delete a chunk set.
    
    Args:
        chunk_set_id: Chunk set ID
        
    Returns:
        True if deleted, False if not found
    """
    try:
        client = get_supabase_client()
        
        # Delete chunk set
        result = client.table('chunk_sets').delete().eq('id', str(chunk_set_id)).execute()
        
        return len(result.data) > 0
    except Exception as e:
        logger.error(f"Failed to delete chunk set: {str(e)}")
        raise 