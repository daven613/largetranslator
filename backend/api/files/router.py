"""
File management router for FastAPI.
Defines endpoints for uploading, listing, and deleting text files.
"""
import logging
from typing import List
import os
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, Form
from fastapi.responses import JSONResponse

from . import schemas
from ..dependencies import get_current_user
from ...external_services.supabase.storage_service import SupabaseStorageService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/files", tags=["files"])

@router.post("/upload", response_model=schemas.FileUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    user = Depends(get_current_user)
):
    """
    Upload a text file.
    
    Args:
        file: File to upload
        user: Current authenticated user
        
    Returns:
        Metadata of the uploaded file
    
    Raises:
        HTTPException: If upload fails or file is not text-based
    """
    try:
        # Read file content
        content = await file.read()
        
        # Check if it's a text file by trying to decode it
        try:
            content.decode('utf-8')
        except UnicodeDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only text files can be uploaded. The file appears to be binary."
            )
        
        # Upload file to Supabase storage
        result = SupabaseStorageService.upload_file(
            user_id=user["id"],
            file_name=file.filename,
            file_content=content,
            content_type=file.content_type
        )
        
        return result
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
        result = SupabaseStorageService.delete_file(
            user_id=user["id"],
            file_name=file_name
        )
        return result
    except Exception as e:
        logger.error(f"Failed to delete file {file_name}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete file: {str(e)}"
        ) 