"""
Text chunking API endpoints.
"""
import logging
from typing import List, Optional
import os
import uuid
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Path, Body, Query
from fastapi.responses import JSONResponse

from backend import db
from backend.db.crud.files import get_document_by_id, create_document, get_documents_by_user, update_document
from backend.db.crud.chunking import (
    create_chunk_set, get_chunk_set_by_id, get_chunks_by_chunk_set_id,
    get_chunk_sets_by_document, create_chunks, get_chunk_by_id, update_chunk, delete_chunk
)
from backend.helpers import text_chunker
from backend.external_services.supabase.storage_service import SupabaseStorageService
from .. import dependencies
from . import schemas

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chunking", tags=["chunking"])

@router.post("", response_model=schemas.ChunkingResponse, status_code=status.HTTP_201_CREATED)
async def chunk_file(
    chunking_request: schemas.ChunkingRequest,
    user = Depends(dependencies.get_current_user)
):
    """
    Process a stored file into chunks.
    
    Args:
        chunking_request: Request with file_id and chunking parameters
        user: Current authenticated user
        
    Returns:
        Document metadata and chunk count
    """
    try:
        # Parse file_id to extract user_id and file_name
        file_path_parts = chunking_request.file_id.split('/')
        if len(file_path_parts) != 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file_id format. Expected 'user_id/file_name'"
            )
        
        stored_user_id, file_name = file_path_parts
        
        # Check if the file belongs to the current user
        if stored_user_id != user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this file"
            )
        
        # Get file content from storage
        try:
            file_result = SupabaseStorageService.get_file(
                user_id=user["id"],
                file_name=file_name
            )
            text_content = file_result["content"]
            file_size = len(text_content.encode('utf-8'))
        except Exception as e:
            logger.error(f"Failed to get file: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File not found or cannot be accessed: {str(e)}"
            )
        
        # Generate a unique session ID if not provided
        session_id = chunking_request.session_id or f"sess_{uuid.uuid4().hex[:10]}"
        
        # Check if document already exists in database
        existing_document = None
        try:
            documents = await get_documents_by_user(user["id"])
            for doc in documents:
                if doc.name == file_name:
                    existing_document = doc
                    break
        except Exception as e:
            logger.warning(f"Failed to check for existing document: {str(e)}")
        
        # Process text into chunks
        chunks_data = text_chunker.process_document(
            text_content, 
            metadata={
                "filename": file_name,
                "session_id": session_id,
                "target_chunk_size": chunking_request.target_chunk_size,
                "processor_type": chunking_request.processor_type
            }
        )
            
        # If document exists, use it, otherwise create a new one
        if existing_document:
            document = existing_document
            
            # Update the document metadata if needed
            if not document.file_path:
                update_data = update_document(
                    document_id=document.id,
                    metadata={
                        **document.metadata,
                        "last_processed": datetime.now().isoformat()
                    },
                    file_path=chunking_request.file_id
                )
                document = await update_document(update_data)
        else:
            # Create document record in database
            document_data = create_document(
                user_id=user["id"],
                name=file_name,
                file_size=file_size,
                file_path=chunking_request.file_id,
                metadata={
                    "content_type": "text/plain",
                    "last_processed": datetime.now().isoformat()
                }
            )
            document = await create_document(document_data)
        
        # First, create the Pydantic model instance for ChunkSetCreate
        chunk_set_create_payload = db.models.ChunkSetCreate(
            document_id=document.id,
            name=f"Chunking {datetime.now().isoformat()}",
            chunk_size=chunking_request.target_chunk_size,  # Storing in the explicit DB column
            total_chunks=len(chunks_data)                   # Storing in the explicit DB column
            # session_id and processor_type are not stored as per current schema
        )
        # Then, pass this instance to the CRUD function
        chunk_set = await create_chunk_set(chunk_set_create_payload)
        
        # Create chunk records
        chunk_create_payloads = [] 
        for chunk_data in chunks_data:
            chunk_metadata = chunk_data["metadata"]
            
            chunk_create_payload = db.models.ChunkCreate(
                document_id=document.id,
                chunk_set_id=chunk_set.id,
                sequence_number=chunk_data["sequence_number"],
                content=chunk_data["content"],
                metadata=chunk_metadata
            )
            chunk_create_payloads.append(chunk_create_payload)
        
        chunks = await create_chunks(chunk_create_payloads)
        
        # Collect all chunk IDs for the response
        chunk_ids = [str(chunk.id) for chunk in chunks]
        
        # Return document with chunk count and IDs
        return {
            "document_id": document.id,
            "original_file_id": chunking_request.file_id,
            "chunk_set_id": chunk_set.id,
            "chunk_count": len(chunks),
            "chunk_ids": chunk_ids,
            "file_size": file_size,
            "created_at": document.created_at
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chunking failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to chunk file: {str(e)}"
        )

@router.get("/chunks/by-chunk-set/{chunk_set_id}", response_model=schemas.ChunkListResponse)
async def list_chunks_by_chunk_set_id(
    chunk_set_id: UUID = Path(..., description="Chunk set ID to filter chunks"),
    user = Depends(dependencies.get_current_user)
):
    """
    List all chunks for a specific chunk set.
    
    Args:
        chunk_set_id: Chunk set ID to filter chunks
        user: Current authenticated user
        
    Returns:
        List of chunks
    """
    try:
        # Get the chunk set to check ownership
        chunk_set = await get_chunk_set_by_id(chunk_set_id)
        if not chunk_set:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Chunk set with ID {chunk_set_id} not found"
            )
        
        # Get the document to check ownership
        document = await get_document_by_id(chunk_set.document_id)
        if str(document.user_id) != user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this chunk set"
            )
        
        # Get all chunks for this chunk set
        chunks = await get_chunks_by_chunk_set_id(chunk_set_id)
        
        return {"chunks": chunks}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list chunks by chunk set ID: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list chunks: {str(e)}"
        )

@router.get("/chunk-sets/by-document/{document_id}", response_model=schemas.ChunkSetListResponse)
async def list_chunk_sets_by_document(
    document_id: UUID = Path(..., description="Document ID to filter chunk sets"),
    user = Depends(dependencies.get_current_user)
):
    """
    List all chunk sets for a specific document.
    
    Args:
        document_id: Document ID to filter chunk sets
        user: Current authenticated user
        
    Returns:
        List of chunk sets
    """
    try:
        # Get the document to check ownership
        document = await get_document_by_id(document_id)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document with ID {document_id} not found"
            )
        
        if str(document.user_id) != user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this document"
            )
        
        # Get all chunk sets for this document
        chunk_sets = await get_chunk_sets_by_document(document_id)
        
        return {"chunk_sets": chunk_sets}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list chunk sets by document ID: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list chunk sets: {str(e)}"
        )

@router.get("/chunks/{chunk_id}", response_model=schemas.ChunkResponse)
async def get_chunk(
    chunk_id: UUID = Path(...),
    user = Depends(dependencies.get_current_user)
):
    """
    Get a specific chunk.
    
    Args:
        chunk_id: ID of the chunk
        user: Current authenticated user
        
    Returns:
        Chunk data
    """
    try:
        chunk = await get_chunk_by_id(chunk_id)
        
        if not chunk:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Chunk with ID {chunk_id} not found"
            )
        
        # Get document to check ownership
        document = await get_document_by_id(chunk.document_id)
        
        # Check document ownership
        if str(document.user_id) != user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this chunk"
            )
            
        return chunk
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get chunk: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get chunk: {str(e)}"
        )

@router.put("/chunks/{chunk_id}", response_model=schemas.ChunkResponse)
async def update_chunk(
    chunk_update: schemas.ChunkUpdateRequest,
    chunk_id: UUID = Path(...),
    user = Depends(dependencies.get_current_user)
):
    """
    Update a chunk's content or metadata.
    
    Args:
        chunk_update: Data to update
        chunk_id: ID of the chunk to update
        user: Current authenticated user
        
    Returns:
        Updated chunk data
    """
    try:
        # Get chunk to check ownership
        chunk = await get_chunk_by_id(chunk_id)
        
        if not chunk:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Chunk with ID {chunk_id} not found"
            )
        
        # Get document to check ownership
        document = await get_document_by_id(chunk.document_id)
        
        # Check document ownership
        if str(document.user_id) != user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to update this chunk"
            )
        
        # Update chunk
        update_data = update_chunk(
            chunk_id=chunk_id,
            content=chunk_update.content,
            metadata=chunk_update.metadata
        )
        
        updated_chunk = await update_chunk(update_data)
        
        return updated_chunk
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update chunk: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update chunk: {str(e)}"
        )

@router.delete("/chunks/{chunk_id}", response_model=schemas.DeleteResponse)
async def delete_chunk(
    chunk_id: UUID = Path(...),
    user = Depends(dependencies.get_current_user)
):
    """
    Delete a specific chunk.
    
    Args:
        chunk_id: ID of the chunk to delete
        user: Current authenticated user
        
    Returns:
        Deletion status
    """
    try:
        # Get chunk to check ownership
        chunk = await get_chunk_by_id(chunk_id)
        
        if not chunk:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Chunk with ID {chunk_id} not found"
            )
        
        # Get document to check ownership
        document = await get_document_by_id(chunk.document_id)
        
        # Check document ownership
        if str(document.user_id) != user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to delete this chunk"
            )
        
        # Delete chunk
        deleted = await delete_chunk(chunk_id)
        
        return {"success": deleted}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete chunk: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete chunk: {str(e)}"
        ) 