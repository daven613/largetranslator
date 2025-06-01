"""
Schema definitions for text chunking API endpoints.
"""
from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, UUID4, Field

from backend.helpers.json_utils import Config

# Document schemas
class DocumentResponse(BaseModel):
    """Document response model."""
    id: UUID4
    name: str
    file_size: int
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)
    file_path: Optional[str] = None
    
    class Config(Config):
        """Pydantic configuration."""
        pass

class DocumentListResponse(BaseModel):
    """Response model for listing documents."""
    documents: List[DocumentResponse]

# Chunk set schemas
class ChunkSetResponse(BaseModel):
    """Chunk set response model."""
    id: UUID4
    document_id: UUID4
    name: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config(Config):
        """Pydantic configuration."""
        pass

class ChunkSetCreateRequest(BaseModel):
    """Request model for creating a chunk set."""
    document_id: UUID4
    name: Optional[str] = None
    description: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ChunkSetListResponse(BaseModel):
    """Response model for listing chunk sets."""
    chunk_sets: List[ChunkSetResponse]

# Chunk schemas
class ChunkResponse(BaseModel):
    """Chunk response model."""
    id: UUID4
    document_id: UUID4
    chunk_set_id: Optional[UUID4] = None
    sequence_number: int
    content: str
    created_at: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config(Config):
        """Pydantic configuration."""
        pass

class ChunkListResponse(BaseModel):
    """Response model for listing chunks."""
    chunks: List[ChunkResponse]

class ChunkCreateRequest(BaseModel):
    """Request model for creating a chunk."""
    document_id: UUID4
    chunk_set_id: UUID4
    sequence_number: int
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config(Config):
        """Pydantic configuration."""
        pass

class ChunkUpdateRequest(BaseModel):
    """Request model for updating a chunk."""
    content: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    chunk_set_id: Optional[UUID4] = None

# Chunking request schema
class ChunkingRequest(BaseModel):
    """Request model for chunking a file."""
    file_id: str
    target_chunk_size: int = 2000
    session_id: Optional[str] = None
    processor_type: str = "text_chunker"

# Chunking response schema
class ChunkingResponse(BaseModel):
    """Response model for chunking operation."""
    document_id: UUID4
    original_file_id: str
    chunk_set_id: UUID4
    chunk_count: int
    chunk_ids: List[str] = Field(default_factory=list, description="List of IDs for all created chunks")
    file_size: int
    created_at: datetime
    
    class Config(Config):
        """Pydantic configuration."""
        pass

# Common response schemas
class DeleteResponse(BaseModel):
    """Response model for delete operations."""
    success: bool 