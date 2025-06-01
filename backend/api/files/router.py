"""
File management router for FastAPI.
Defines endpoints for uploading, listing, and deleting text files.
"""
import logging
from typing import List
import os
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, Form
from fastapi.responses import JSONResponse
from datetime import datetime
from datetime import timezone as dt_timezone

from . import schemas
from backend.api.dependencies import get_current_user, get_current_user_with_token
from backend.db.crud.files import (
    create_document,
    get_document_by_user_and_name,
    update_document,
    get_documents_by_user,
    delete_document
)
from backend.db import models
from backend.external_services.supabase.storage_service import SupabaseStorageService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/files", tags=["files"])

@router.post("/upload", response_model=schemas.FileUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    user_with_token = Depends(get_current_user_with_token)
):
    """
    Upload a text file.
    
    Args:
        file: File to upload
        user_with_token: Tuple of (current authenticated user, JWT token)
        
    Returns:
        Metadata of the uploaded file
    
    Raises:
        HTTPException: If upload fails or file is not text-based
    """
    try:
        user, token = user_with_token
        # Read file content
        content = await file.read()
        
        # Check if it's a text file by trying to decode it
        try:
            text_content = content.decode('utf-8')
        except UnicodeDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only text files can be uploaded. The file appears to be binary."
            )
        
        # Upload file to Supabase storage
        storage_result = SupabaseStorageService.upload_file(
            user_id=str(user["id"]),
            file_name=file.filename,
            file_content=content,
            content_type=file.content_type,
            user_token=token
        )
        
        # Upsert logic for document metadata in the database
        try:
            existing_document = await get_document_by_user_and_name(
                user_id=user["id"],
                document_name=file.filename,
                user_token=token
            )

            current_time = datetime.now(dt_timezone.utc)

            if existing_document:
                # Update existing document
                logger.info(f"Document '{file.filename}' already exists for user '{user['id']}'. Updating it.")
                document_update_data = models.DocumentUpdate(
                    file_path=storage_result["file_id"], # New storage path/ID
                    file_size=len(content),
                    metadata={
                        **existing_document.metadata, # Preserve existing metadata
                        "content_type": file.content_type,
                        "upload_source": "api_upload_upsert",
                        "upload_time": storage_result["created_at"], # From storage result
                        "last_known_storage_path": storage_result["file_id"]
                    },
                )
                db_document = await update_document(
                    document_id=existing_document.id, 
                    update_data=document_update_data,
                    user_token=token
                )
                if not db_document:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Failed to update document record after storage upsert."
                    )
            else:
                # Create new document
                logger.info(f"Creating new document record for '{file.filename}' for user '{user['id']}'.")
                document_create_data = models.DocumentCreate(
                    user_id=user["id"],
                    name=file.filename,
                    file_size=len(content),
                    file_path=storage_result["file_id"], 
                    metadata={
                        "content_type": file.content_type,
                        "upload_source": "api_upload_create",
                        "upload_time": storage_result["created_at"],
                        "initial_storage_path": storage_result["file_id"]
                    }
                )
                db_document = await create_document(document_create_data, user_token=token)
            
        except Exception as db_error:
            logger.error(f"Database operation failed for document '{file.filename}': {str(db_error)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"File uploaded to storage, but database operation failed: {str(db_error)}"
            )
        
        # Construct the response using data from db_document
        return schemas.FileUploadResponse(
            id=db_document.id,
            file_id=db_document.file_path, 
            file_name=db_document.name,    
            file_size=db_document.file_size, 
            content_type=file.content_type,  
            created_at=db_document.created_at 
        )
    except HTTPException: 
        raise
    except Exception as e:
        logger.error(f"File upload failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}"
        )

@router.get("", response_model=schemas.FileList)
async def list_files(user = Depends(get_current_user)):
    """
    List all files for the current user.
    
    Args:
        user: Current authenticated user
        
    Returns:
        List of file metadata
    """
    try:
        files = SupabaseStorageService.list_files(user_id=user["id"])
        return {"files": files}
    except Exception as e:
        logger.error(f"Failed to list files: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list files: {str(e)}"
        )

@router.get("/documents", response_model=schemas.DocumentListResponse)
async def list_documents(user = Depends(get_current_user)):
    """
    List all documents for the current user with their database UUIDs.
    
    Args:
        user: Current authenticated user
        
    Returns:
        List of document records with UUIDs
    """
    try:
        documents = await get_documents_by_user(user["id"])
        
        # Convert to response format
        document_responses = []
        for doc in documents:
            document_responses.append(schemas.DocumentResponse(
                id=doc.id,
                name=doc.name,
                file_size=doc.file_size,
                file_path=doc.file_path,
                created_at=doc.created_at,
                updated_at=doc.updated_at,
                metadata=doc.metadata or {}
            ))
        
        return {"documents": document_responses}
    except Exception as e:
        logger.error(f"Failed to list documents: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list documents: {str(e)}"
        )

@router.get("/{file_name}/metadata", response_model=schemas.FileMetadataResponse)
async def get_file_metadata(
    file_name: str,
    user = Depends(get_current_user)
):
    """
    Get a file's metadata without its content.
    
    Args:
        file_name: Name of the file to retrieve metadata for
        user: Current authenticated user
        
    Returns:
        File metadata
    
    Raises:
        HTTPException: If file not found or cannot be accessed
    """
    try:
        metadata = SupabaseStorageService.get_file_metadata(
            user_id=user["id"],
            file_name=file_name
        )
        return {"metadata": metadata}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to get file metadata for {file_name}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get file metadata: {str(e)}"
        )

@router.get("/{file_name}", response_model=schemas.FileContent)
async def get_file(
    file_name: str,
    user = Depends(get_current_user)
):
    """
    Get a file's content.
    
    Args:
        file_name: Name of the file to retrieve
        user: Current authenticated user
        
    Returns:
        File content and metadata
    
    Raises:
        HTTPException: If file not found or cannot be read
    """
    try:
        # First try to find the document in database to get file path
        documents = await get_documents_by_user(user["id"])
        file_path = None
        
        for doc in documents:
            if doc.name == file_name:
                file_path = doc.file_path
                break
                
        # If file_path is found in document, use it
        if file_path:
            user_id = file_path.split('/')[0] if '/' in file_path else user["id"]
            result = SupabaseStorageService.get_file(
                user_id=user_id,
                file_name=file_name
            )
        else:
            # Fallback to original method
            result = SupabaseStorageService.get_file(
                user_id=user["id"],
                file_name=file_name
            )
            
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to get file {file_name}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File {file_name} not found or cannot be accessed"
        )

@router.delete("/{file_name}", response_model=schemas.DeleteFileResponse)
async def delete_file(
    file_name: str,
    user = Depends(get_current_user)
):
    """
    Delete a file.
    
    Args:
        file_name: Name of the file to delete
        user: Current authenticated user
        
    Returns:
        Deletion status
    
    Raises:
        HTTPException: If deletion fails
    """
    try:
        # Find documents by name and user_id to get file path
        documents = await get_documents_by_user(user["id"])
        document_to_delete = None
        file_path = None
        
        for doc in documents:
            if doc.name == file_name:
                document_to_delete = doc
                file_path = doc.file_path
                break
        
        # Delete file from storage
        if file_path and '/' in file_path:
            user_id = file_path.split('/')[0]
            result = SupabaseStorageService.delete_file(
                user_id=user_id,
                file_name=file_name
            )
        else:
            # Fallback to original method
            result = SupabaseStorageService.delete_file(
                user_id=user["id"],
                file_name=file_name
            )
        
        # Delete the document record if found
        if document_to_delete:
            await delete_document(document_to_delete.id)
        
        return result
    except Exception as e:
        logger.error(f"Failed to delete file {file_name}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete file: {str(e)}"
        ) 