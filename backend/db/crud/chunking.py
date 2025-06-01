"""
CRUD operations for chunks and chunk sets.
"""
import logging
from typing import Dict, List, Optional, Any
from uuid import UUID
from datetime import datetime

from pydantic import UUID4

from ...helpers.json_utils import convert_uuids_to_str
from .. import models
from ..async_client import get_db_client

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
        db = await get_db_client()
        
        # Convert to dict and ensure UUIDs are strings
        chunk_dict = chunk.model_dump()
        
        # Convert UUID fields to strings
        if 'document_id' in chunk_dict:
            chunk_dict['document_id'] = str(chunk_dict['document_id'])
        if 'chunk_set_id' in chunk_dict:
            chunk_dict['chunk_set_id'] = str(chunk_dict['chunk_set_id'])
        if 'user_id' in chunk_dict:
            chunk_dict['user_id'] = str(chunk_dict['user_id'])
        
        # Add timestamps
        chunk_dict['created_at'] = datetime.utcnow().isoformat()
        chunk_dict['updated_at'] = datetime.utcnow().isoformat()
        
        # Create chunk
        result = await db.insert_returning("chunks", chunk_dict)
        
        if not result:
            raise ValueError("Failed to create chunk")
        
        return models.Chunk(**result)
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
            
        db = await get_db_client()
        
        # Insert chunks one by one (Supabase doesn't have efficient bulk insert returning)
        created_chunks = []
        for chunk in chunks:
            chunk_dict = chunk.model_dump()
            
            # Convert UUID fields to strings
            if 'document_id' in chunk_dict:
                chunk_dict['document_id'] = str(chunk_dict['document_id'])
            if 'chunk_set_id' in chunk_dict:
                chunk_dict['chunk_set_id'] = str(chunk_dict['chunk_set_id'])
            if 'user_id' in chunk_dict:
                chunk_dict['user_id'] = str(chunk_dict['user_id'])
            
            # Add timestamps
            chunk_dict['created_at'] = datetime.utcnow().isoformat()
            chunk_dict['updated_at'] = datetime.utcnow().isoformat()
            
            result = await db.insert_returning("chunks", chunk_dict)
            if result:
                created_chunks.append(models.Chunk(**result))
        
        return created_chunks
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
        db = await get_db_client()
        
        # Get chunk using filters
        result = await db.fetch_one("chunks", filters={"id": str(chunk_id)})
        
        if not result:
            return None
            
        return models.Chunk(**result)
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
        db = await get_db_client()
        
        # Get chunks for document
        results = await db.fetch_all(
            "chunks", 
            filters={"document_id": str(document_id)},
            select="*"
        )
        
        # Sort by sequence_number (do this in Python since we can't specify ORDER BY in simple filters)
        chunks = [models.Chunk(**chunk) for chunk in results]
        chunks.sort(key=lambda x: x.sequence_number or 0)
        
        return chunks
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
        db = await get_db_client()
        
        # Get chunks with the chunk_set_id
        results = await db.fetch_all(
            "chunks", 
            filters={"chunk_set_id": str(chunk_set_id)},
            select="*"
        )
        
        # Sort by sequence_number (do this in Python since we can't specify ORDER BY in simple filters)
        chunks = [models.Chunk(**chunk) for chunk in results]
        chunks.sort(key=lambda x: x.sequence_number or 0)
        
        return chunks
    except Exception as e:
        logger.error(f"Failed to get chunks by chunk set ID: {str(e)}")
        raise


async def search_chunks_by_content(user_id: UUID4, search_text: str) -> List[Dict[str, Any]]:
    """
    Search for chunks containing specific text.
    Note: This is a simplified version using basic text matching.
    For full-text search, you'd need to use PostgreSQL's full-text search features.
    
    Args:
        user_id: User ID
        search_text: Text to search for
        
    Returns:
        Array of matching chunks with document metadata
    """
    try:
        db = await get_db_client()
        
        # Get all chunks for user's documents
        # Note: This is simplified - in practice you'd want a proper join query
        results = await db.fetch_all("chunks", select="*")
        
        # Filter by content containing search text (case-insensitive)
        matching_chunks = []
        for chunk in results:
            if chunk.get('content', '').lower().find(search_text.lower()) != -1:
                matching_chunks.append(chunk)
        
        return matching_chunks
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
    Note: This is a placeholder - vector search requires pgvector extension
    and specific SQL queries.
    
    Args:
        user_id: User ID
        query_vector: Vector embedding of the query
        similarity_threshold: Minimum similarity score (0-1)
        limit: Maximum number of results
        
    Returns:
        Array of chunks sorted by similarity
    """
    try:
        logger.warning("Vector search not implemented with simplified async client")
        return []
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
        db = await get_db_client()
        
        # Prepare update data (exclude None values)
        update_dict = {}
        if update_data.content is not None:
            update_dict["content"] = update_data.content
        if update_data.sequence_number is not None:
            update_dict["sequence_number"] = update_data.sequence_number
        if update_data.metadata is not None:
            update_dict["metadata"] = update_data.metadata
        
        # Always update the updated_at timestamp
        update_dict["updated_at"] = datetime.utcnow().isoformat()
        
        if not update_dict:
            # No fields to update
            return await get_chunk_by_id(chunk_id)
        
        # Update chunk
        result = await db.update_returning("chunks", update_dict, {"id": str(chunk_id)})
        
        if not result:
            raise ValueError(f"Chunk with ID {chunk_id} not found")
        
        return models.Chunk(**result)
    except Exception as e:
        logger.error(f"Failed to update chunk: {str(e)}")
        raise


async def update_chunk_embedding(chunk_id: UUID4, embedding: List[float]) -> models.Chunk:
    """
    Update a chunk's embedding vector.
    
    Args:
        chunk_id: Chunk ID
        embedding: Vector embedding
        
    Returns:
        Updated chunk
    """
    try:
        db = await get_db_client()
        
        update_data = {
            'embedding': embedding,
            'updated_at': datetime.utcnow().isoformat()
        }
        
        # Update chunk
        result = await db.update_returning("chunks", update_data, {"id": str(chunk_id)})
        
        if not result:
            raise ValueError(f"Chunk with ID {chunk_id} not found")
        
        return models.Chunk(**result)
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
        db = await get_db_client()
        
        # Delete chunk
        result = await db.delete_returning("chunks", {"id": str(chunk_id)})
        
        return result is not None
    except Exception as e:
        logger.error(f"Failed to delete chunk: {str(e)}")
        raise


async def delete_chunks_by_document(document_id: UUID4) -> int:
    """
    Delete all chunks for a document.
    
    Args:
        document_id: Document ID
        
    Returns:
        Number of deleted chunks
    """
    try:
        db = await get_db_client()
        
        # First get count of chunks to delete
        chunks = await db.fetch_all("chunks", filters={"document_id": str(document_id)})
        count = len(chunks)
        
        # Delete chunks (Note: this doesn't return count in Supabase, so we count first)
        if count > 0:
            await db.delete_returning("chunks", {"document_id": str(document_id)})
        
        return count
    except Exception as e:
        logger.error(f"Failed to delete chunks by document: {str(e)}")
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
        db = await get_db_client()
        
        # Convert to dict and ensure UUIDs are strings
        chunk_set_dict = chunk_set.model_dump()
        
        # Convert UUID fields to strings
        if 'document_id' in chunk_set_dict:
            chunk_set_dict['document_id'] = str(chunk_set_dict['document_id'])
        if 'user_id' in chunk_set_dict:
            chunk_set_dict['user_id'] = str(chunk_set_dict['user_id'])
        
        # Add timestamps
        chunk_set_dict['created_at'] = datetime.utcnow().isoformat()
        chunk_set_dict['updated_at'] = datetime.utcnow().isoformat()
        
        # Create chunk set
        result = await db.insert_returning("chunk_sets", chunk_set_dict)
        
        if not result:
            raise ValueError("Failed to create chunk set")
        
        return models.ChunkSet(**result)
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
        db = await get_db_client()
        
        # Get chunk set
        result = await db.fetch_one("chunk_sets", filters={"id": str(chunk_set_id)})
        
        if not result:
            return None
            
        return models.ChunkSet(**result)
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
        db = await get_db_client()
        
        # Get chunk sets for document
        results = await db.fetch_all(
            "chunk_sets", 
            filters={"document_id": str(document_id)},
            select="*"
        )
        
        return [models.ChunkSet(**chunk_set) for chunk_set in results]
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
        db = await get_db_client()
        
        # Prepare update data (exclude None values)
        update_dict = {}
        if update_data.chunk_size is not None:
            update_dict["chunk_size"] = update_data.chunk_size
        if update_data.overlap_size is not None:
            update_dict["overlap_size"] = update_data.overlap_size
        if update_data.total_chunks is not None:
            update_dict["total_chunks"] = update_data.total_chunks
        if update_data.processing_status is not None:
            update_dict["processing_status"] = update_data.processing_status
        if update_data.metadata is not None:
            update_dict["metadata"] = update_data.metadata
        
        # Always update the updated_at timestamp
        update_dict["updated_at"] = datetime.utcnow().isoformat()
        
        if not update_dict:
            # No fields to update
            return await get_chunk_set_by_id(chunk_set_id)
        
        # Update chunk set
        result = await db.update_returning("chunk_sets", update_dict, {"id": str(chunk_set_id)})
        
        if not result:
            raise ValueError(f"Chunk set with ID {chunk_set_id} not found")
        
        return models.ChunkSet(**result)
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
        db = await get_db_client()
        
        # Delete chunk set
        result = await db.delete_returning("chunk_sets", {"id": str(chunk_set_id)})
        
        return result is not None
    except Exception as e:
        logger.error(f"Failed to delete chunk set: {str(e)}")
        raise 