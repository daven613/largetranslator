"""
CRUD operations for document files.
"""
import logging
from typing import Dict, List, Optional, Any
from uuid import UUID
from datetime import datetime, timezone

from pydantic import UUID4

from ...external_services.supabase.client import get_supabase_client, get_user_supabase_client
from ...helpers.json_utils import convert_uuids_to_str
from .. import models

logger = logging.getLogger(__name__)


async def create_document(document: models.DocumentCreate, user_token: Optional[str] = None) -> models.Document:
    """
    Create a new document in the database.
    
    Args:
        document: Document data
        user_token: Optional JWT token for RLS context
        
    Returns:
        Created document
    """
    try:
        client_type = "" # For logging
        if user_token:
            client = get_user_supabase_client(user_token)
            client_type = "user-specific (RLS)"
            logger.info(f"create_document: Using {client_type} client.")
        else:
            # This case might be problematic if a user context is strictly required.
            client = get_supabase_client()
            client_type = "global admin (bypasses RLS)"
            logger.warning(f"create_document: Using {client_type} client. This might bypass RLS if user_id is present in document data.")
        
        doc_dict = convert_uuids_to_str(document.model_dump())
        
        # Log the user_id being inserted
        inserted_user_id = doc_dict.get('user_id')
        logger.info(f"create_document: Attempting to insert document with user_id: {inserted_user_id} using {client_type} client.")

        now_utc_iso = datetime.now(timezone.utc).isoformat()
        doc_dict["created_at"] = now_utc_iso
        doc_dict["updated_at"] = now_utc_iso
        
        # Set default metadata if not provided
        if "metadata" not in doc_dict or doc_dict["metadata"] is None:
            doc_dict["metadata"] = {}
        
        # Insert document into database
        result = client.table("documents").insert(doc_dict).execute()
        
        if not result.data:
            raise ValueError("Failed to create document")
        
        # Convert result to Document model
        return models.Document(**result.data[0])
    except Exception as e:
        logger.error(f"Failed to create document: {str(e)}")
        raise


async def get_document_by_id(document_id: UUID4) -> Optional[models.Document]:
    """
    Get a document by ID.
    
    Args:
        document_id: Document ID
        
    Returns:
        Document or None if not found
    """
    try:
        client = get_supabase_client()
        
        # Get document
        result = client.table('documents').select('*').eq('id', str(document_id)).execute()
        
        if not result.data:
            return None
            
        return models.Document(**result.data[0])
    except Exception as e:
        logger.error(f"Failed to get document: {str(e)}")
        raise


async def get_document_by_user_and_name(user_id: UUID4, document_name: str, user_token: Optional[str] = None) -> Optional[models.Document]:
    """
    Get a document by user ID and document name.
    
    Args:
        user_id: User ID
        document_name: Name of the document
        user_token: Optional JWT token for RLS context
        
    Returns:
        Document or None if not found
    """
    try:
        # Use user-specific client if token provided, otherwise use global client
        if user_token:
            client = get_user_supabase_client(user_token)
        else:
            client = get_supabase_client()
        result = client.table('documents') \
            .select('*') \
            .eq('user_id', str(user_id)) \
            .eq('name', document_name) \
            .limit(1) \
            .execute()
        
        if not result.data or len(result.data) == 0 or not result.data[0]:
            return None
            
        return models.Document(**result.data[0])
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
        client = get_supabase_client()
        
        # Get documents
        result = client.table('documents').select('*').eq('user_id', str(user_id)).execute()
        
        return [models.Document(**doc) for doc in result.data]
    except Exception as e:
        logger.error(f"Failed to get documents for user: {str(e)}")
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
        client = get_supabase_client()
        
        # Start with user filter
        query = client.table('documents').select('*').eq('user_id', str(user_id))
        
        # Add metadata filters
        # This is a simplified implementation - for more complex queries,
        # consider using Postgres JSON operators more extensively
        for key, value in metadata_query.items():
            query = query.filter(f"metadata->>'{key}'", 'eq', value)
        
        result = query.execute()
        
        return [models.Document(**doc) for doc in result.data]
    except Exception as e:
        logger.error(f"Failed to get documents by metadata: {str(e)}")
        raise


async def update_document(document_id: UUID4, update_data: models.DocumentUpdate, user_token: Optional[str] = None) -> models.Document:
    """
    Update a document in the database.
    
    Args:
        document_id: ID of the document to update
        update_data: Document data to update
        user_token: Optional JWT token for RLS context
        
    Returns:
        Updated document
    """
    try:
        # Use user-specific client if token provided, otherwise use global client
        if user_token:
            client = get_user_supabase_client(user_token)
        else:
            client = get_supabase_client()
        
        # Convert UUIDs to strings for Supabase
        # Filter out None values to only update provided fields
        update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
        
        # Always update updated_at field to UTC
        update_dict["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        # Update document in database
        result = client.table("documents").update(update_dict).eq("id", str(document_id)).execute()
        
        if not result.data:
            raise ValueError(f"Document with ID {document_id} not found")
        
        # Convert result to Document model
        return models.Document(**result.data[0])
    except Exception as e:
        logger.error(f"Failed to update document: {str(e)}")
        raise


async def delete_document(document_id: UUID4) -> bool:
    """
    Delete a document.
    
    Args:
        document_id: Document ID
        
    Returns:
        True if deleted, False if not found
    """
    try:
        client = get_supabase_client()
        
        # Delete document
        result = client.table('documents').delete().eq('id', str(document_id)).execute()
        
        return len(result.data) > 0
    except Exception as e:
        logger.error(f"Failed to delete document: {str(e)}")
        raise


async def update_document_metadata(document_id: UUID4, metadata_updates: Dict[str, Any]) -> models.Document:
    """
    Update document metadata without replacing the entire metadata object.
    
    Args:
        document_id: Document ID
        metadata_updates: Metadata fields to update/add
        
    Returns:
        Updated document
    """
    try:
        # First get the current document to access its metadata
        doc = await get_document_by_id(document_id)
        if not doc:
            raise ValueError(f"Document with ID {document_id} not found")
        
        # Update metadata with new fields
        metadata = doc.metadata.copy()
        metadata.update(metadata_updates)
        
        # Update document with new metadata
        update_data = models.DocumentUpdate(metadata=metadata)
        return await update_document(document_id, update_data)
        
    except Exception as e:
        logger.error(f"Failed to update metadata: {str(e)}")
        raise 