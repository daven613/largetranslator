"""
CRUD operations for document files.
"""
import logging
from typing import Dict, List, Optional, Any
from uuid import UUID
from datetime import datetime, timezone

from pydantic import UUID4

from ...helpers.json_utils import convert_uuids_to_str
from .. import models
from ..async_client import get_db_client

logger = logging.getLogger(__name__)


async def create_document(user_id: UUID, document_data: models.DocumentCreate) -> models.Document:
    """
    Create a new document in the database.
    
    Args:
        user_id: User ID
        document_data: Document data
        
    Returns:
        Created document
    """
    try:
        db = await get_db_client()
        
        # Prepare document data for insertion
        document_dict = {
            "user_id": str(user_id),
            "filename": document_data.filename,
            "file_size": document_data.file_size,
            "content_type": document_data.content_type,
            "file_path": document_data.file_path,
            "status": "uploaded",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Insert document
        result = await db.insert_returning("documents", document_dict)
        
        if result:
            return models.Document(**result)
        else:
            raise Exception("Failed to create document")
            
    except Exception as e:
        logger.error(f"Error creating document: {str(e)}")
        raise


async def get_document_by_id(document_id: UUID4, user_id: Optional[UUID] = None) -> Optional[models.Document]:
    """
    Get a document by ID, optionally filtering by user.
    
    Args:
        document_id: Document ID
        user_id: Optional user ID for filtering
        
    Returns:
        Document or None if not found
    """
    try:
        db = await get_db_client()
        
        # Build filters
        filters = {"id": str(document_id)}
        if user_id:
            filters["user_id"] = str(user_id)
        
        # Fetch document
        result = await db.fetch_one("documents", filters=filters)
        
        if result:
            return models.Document(**result)
        return None
        
    except Exception as e:
        logger.error(f"Error fetching document {document_id}: {str(e)}")
        raise


async def get_document_by_user_and_name(user_id: UUID4, document_name: str, user_token: Optional[str] = None) -> Optional[models.Document]:
    """
    Get a document by user ID and document name.
    
    Args:
        user_id: User ID
        document_name: Name of the document
        user_token: Optional JWT token for RLS context (not used with direct DB access)
        
    Returns:
        Document or None if not found
    """
    try:
        db = await get_db_client()
        
        result = await db.fetch_one(
            "SELECT * FROM documents WHERE user_id = $1 AND name = $2 LIMIT 1",
            str(user_id),
            document_name
        )
        
        if not result:
            return None
            
        return models.Document(**result)
    except Exception as e:
        logger.error(f"Failed to get document by user and name: {str(e)}")
        raise


async def get_documents_by_user(user_id: UUID4) -> List[models.Document]:
    """
    Get all documents for a user.
    
    Args:
        user_id: User ID
        
    Returns:
        List of documents
    """
    try:
        db = await get_db_client()
        
        # Fetch documents for user
        results = await db.fetch_all(
            "documents", 
            filters={"user_id": str(user_id)},
            select="*"
        )
        
        return [models.Document(**doc) for doc in results]
        
    except Exception as e:
        logger.error(f"Error fetching documents for user {user_id}: {str(e)}")
        raise


async def get_documents_by_metadata(user_id: UUID4, metadata_query: Dict[str, Any]) -> List[models.Document]:
    """
    Search documents by metadata fields.
    
    Args:
        user_id: User ID
        metadata_query: Metadata query dict
        
    Returns:
        List of documents matching the metadata query
    """
    try:
        db = await get_db_client()
        
        # Build query with metadata filters
        where_clauses = ["user_id = $1"]
        params = [str(user_id)]
        
        for i, (key, value) in enumerate(metadata_query.items(), start=2):
            where_clauses.append(f"metadata->>'${i-1}' = ${i}")
            params.append(key)
            params.append(str(value))
        
        query = f"SELECT * FROM documents WHERE {' AND '.join(where_clauses)}"
        results = await db.fetch_all(query, *params)
        
        return [models.Document(**doc) for doc in results]
    except Exception as e:
        logger.error(f"Failed to get documents by metadata: {str(e)}")
        raise


async def update_document(document_id: UUID4, update_data: models.DocumentUpdate, user_id: Optional[UUID] = None) -> Optional[models.Document]:
    """
    Update a document in the database.
    
    Args:
        document_id: ID of the document to update
        update_data: Document data to update
        user_id: Optional user ID for filtering
        
    Returns:
        Updated document or None if no fields to update
    """
    try:
        db = await get_db_client()
        
        # Prepare update data (exclude None values)
        update_dict = {}
        if update_data.filename is not None:
            update_dict["filename"] = update_data.filename
        if update_data.status is not None:
            update_dict["status"] = update_data.status
        if update_data.file_path is not None:
            update_dict["file_path"] = update_data.file_path
        if update_data.content_type is not None:
            update_dict["content_type"] = update_data.content_type
        if update_data.file_size is not None:
            update_dict["file_size"] = update_data.file_size
        
        # Always update the updated_at timestamp
        update_dict["updated_at"] = datetime.utcnow().isoformat()
        
        if not update_dict:
            # No fields to update
            return await get_document_by_id(document_id, user_id)
        
        # Build filters
        filters = {"id": str(document_id)}
        if user_id:
            filters["user_id"] = str(user_id)
        
        # Update document
        result = await db.update_returning("documents", update_dict, filters)
        
        if result:
            return models.Document(**result)
        return None
        
    except Exception as e:
        logger.error(f"Error updating document {document_id}: {str(e)}")
        raise


async def delete_document(document_id: UUID4, user_id: Optional[UUID] = None) -> bool:
    """
    Delete a document.
    
    Args:
        document_id: Document ID
        user_id: Optional user ID for filtering
        
    Returns:
        True if deleted, False if not found
    """
    try:
        db = await get_db_client()
        
        # Build filters
        filters = {"id": str(document_id)}
        if user_id:
            filters["user_id"] = str(user_id)
        
        # Delete document
        result = await db.delete_returning("documents", filters)
        
        return result is not None
        
    except Exception as e:
        logger.error(f"Error deleting document {document_id}: {str(e)}")
        raise


async def update_document_metadata(document_id: UUID4, metadata_updates: Dict[str, Any]) -> models.Document:
    """
    Update metadata fields for a document.
    
    Args:
        document_id: Document ID
        metadata_updates: Dictionary of metadata updates
        
    Returns:
        Updated document
    """
    try:
        # Get current document to merge metadata
        current_doc = await get_document_by_id(document_id)
        if not current_doc:
            raise ValueError(f"Document with ID {document_id} not found")
        
        # Merge metadata
        current_metadata = current_doc.metadata or {}
        updated_metadata = {**current_metadata, **metadata_updates}
        
        # Update document with new metadata
        update_data = models.DocumentUpdate(metadata=updated_metadata)
        return await update_document(document_id, update_data)
    except Exception as e:
        logger.error(f"Failed to update document metadata: {str(e)}")
        raise 