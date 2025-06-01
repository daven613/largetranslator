"""
Schemas for file management API.
Defines Pydantic models for request/response validation.
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, UUID4

class FileUploadResponse(BaseModel):
    """Schema for file upload response"""
    id: UUID4 = Field(..., description="Database ID of the document record")
    file_id: str = Field(..., description="Storage path or identifier from the storage service (e.g., Supabase Storage path)")
    file_name: str = Field(..., description="Name of the uploaded file")
    file_size: int = Field(..., description="Size of the file in bytes")
    content_type: str = Field(..., description="MIME type of the file")
    created_at: datetime = Field(..., description="When the file was uploaded")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "8f7b5db1-9c2a-4fe1-89a4-3e48e68c99a1",
                "file_id": "8f7b5db1-9c2a-4fe1-89a4-3e48e68c99a1",
                "file_name": "example.txt",
                "file_size": 1024,
                "content_type": "text/plain",
                "created_at": "2023-07-21T15:30:45Z"
            }
        }

class FileMetadata(BaseModel):
    """Schema for file metadata"""
    file_id: str = Field(..., description="Unique identifier for the file")
    file_name: str = Field(..., description="Name of the file")
    file_size: int = Field(..., description="Size of the file in bytes")
    content_type: str = Field(..., description="MIME type of the file")
    created_at: datetime = Field(..., description="When the file was uploaded")
    
    class Config:
        json_schema_extra = {
            "example": {
                "file_id": "8f7b5db1-9c2a-4fe1-89a4-3e48e68c99a1",
                "file_name": "example.txt",
                "file_size": 1024,
                "content_type": "text/plain",
                "created_at": "2023-07-21T15:30:45Z"
            }
        }

class FileMetadataResponse(BaseModel):
    """Schema for single file metadata response"""
    metadata: FileMetadata = Field(..., description="File metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "metadata": {
                    "file_id": "8f7b5db1-9c2a-4fe1-89a4-3e48e68c99a1",
                    "file_name": "example.txt",
                    "file_size": 1024,
                    "content_type": "text/plain",
                    "created_at": "2023-07-21T15:30:45Z"
                }
            }
        }

class FileList(BaseModel):
    """Schema for listing files"""
    files: List[FileMetadata] = Field(default_factory=list, description="List of files")
    
    class Config:
        json_schema_extra = {
            "example": {
                "files": [
                    {
                        "file_id": "8f7b5db1-9c2a-4fe1-89a4-3e48e68c99a1",
                        "file_name": "example1.txt",
                        "file_size": 1024,
                        "content_type": "text/plain",
                        "created_at": "2023-07-21T15:30:45Z"
                    },
                    {
                        "file_id": "7e6a4cb0-8b19-3ed0-78a3-2e37d57b88a0",
                        "file_name": "example2.txt",
                        "file_size": 2048,
                        "content_type": "text/plain",
                        "created_at": "2023-07-22T10:15:30Z"
                    }
                ]
            }
        }

class FileContent(BaseModel):
    """Schema for file content"""
    file_id: str = Field(..., description="Unique identifier for the file")
    file_name: str = Field(..., description="Name of the file")
    content: str = Field(..., description="Text content of the file")
    content_type: str = Field(..., description="MIME type of the file")
    
    class Config:
        json_schema_extra = {
            "example": {
                "file_id": "8f7b5db1-9c2a-4fe1-89a4-3e48e68c99a1",
                "file_name": "example.txt",
                "content": "This is the content of the example text file.",
                "content_type": "text/plain"
            }
        }

class DeleteFileResponse(BaseModel):
    """Schema for file deletion response"""
    success: bool = Field(..., description="Whether the file was successfully deleted")
    file_id: str = Field(..., description="ID of the deleted file")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "file_id": "8f7b5db1-9c2a-4fe1-89a4-3e48e68c99a1"
            }
        }

class DocumentResponse(BaseModel):
    """Schema for document response"""
    id: UUID4 = Field(..., description="Database UUID of the document")
    name: str = Field(..., description="Name of the document")
    file_size: int = Field(..., description="Size of the file in bytes")
    file_path: Optional[str] = Field(None, description="Storage path of the file")
    created_at: datetime = Field(..., description="When the document was created")
    updated_at: datetime = Field(..., description="When the document was last updated")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "8f7b5db1-9c2a-4fe1-89a4-3e48e68c99a1",
                "name": "example.txt",
                "file_size": 1024,
                "file_path": "user123/example.txt",
                "created_at": "2023-07-21T15:30:45Z",
                "updated_at": "2023-07-21T15:30:45Z",
                "metadata": {"content_type": "text/plain"}
            }
        }

class DocumentListResponse(BaseModel):
    """Schema for listing documents"""
    documents: List[DocumentResponse] = Field(default_factory=list, description="List of documents")
    
    class Config:
        json_schema_extra = {
            "example": {
                "documents": [
                    {
                        "id": "8f7b5db1-9c2a-4fe1-89a4-3e48e68c99a1",
                        "name": "example1.txt",
                        "file_size": 1024,
                        "file_path": "user123/example1.txt",
                        "created_at": "2023-07-21T15:30:45Z",
                        "updated_at": "2023-07-21T15:30:45Z",
                        "metadata": {"content_type": "text/plain"}
                    }
                ]
            }
        } 