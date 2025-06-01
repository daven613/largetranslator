"""
Database models for the Large Translator application.
"""
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field, UUID4

from ..helpers.json_utils import Config

class DocumentBase(BaseModel):
    """Base model for document data."""
    name: str
    file_size: int
    metadata: Dict[str, Any] = Field(default_factory=dict)
    file_path: Optional[str] = None

class DocumentCreate(DocumentBase):
    """Model for creating a new document."""
    user_id: UUID4

class DocumentUpdate(BaseModel):
    """Model for updating an existing document."""
    name: Optional[str] = None
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None

class Document(DocumentBase):
    """Model representing a document in the database."""
    id: UUID4
    user_id: UUID4
    created_at: datetime
    updated_at: datetime

    class Config(Config):
        """Pydantic configuration."""
        orm_mode = True

class ChunkSetBase(BaseModel):
    """Base model for chunk set data."""
    name: Optional[str] = None

class ChunkSetCreate(ChunkSetBase):
    """Model for creating a new chunk set."""
    document_id: UUID4
    chunk_size: int
    total_chunks: int

class ChunkSetUpdate(BaseModel):
    """Model for updating an existing chunk set."""
    name: Optional[str] = None
    chunk_size: Optional[int] = None
    total_chunks: Optional[int] = None

class ChunkSet(ChunkSetBase):
    """Model representing a chunk set in the database."""
    id: UUID4
    document_id: UUID4
    chunk_size: int
    total_chunks: int
    created_at: datetime
    updated_at: datetime

    class Config(Config):
        """Pydantic configuration."""
        orm_mode = True

class ChunkBase(BaseModel):
    """Base model for chunk data."""
    sequence_number: int
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ChunkCreate(ChunkBase):
    """Model for creating a new chunk."""
    document_id: UUID4
    chunk_set_id: UUID4

class ChunkUpdate(BaseModel):
    """Model for updating an existing chunk."""
    content: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    chunk_set_id: Optional[UUID4] = None

class Chunk(ChunkBase):
    """Model representing a chunk in the database."""
    id: UUID4
    document_id: UUID4
    chunk_set_id: Optional[UUID4] = None
    created_at: datetime
    embedding: Optional[List[float]] = None

    class Config(Config):
        """Pydantic configuration."""
        orm_mode = True

class DocumentWithChunks(Document):
    """Model representing a document with its chunks."""
    chunks: List[Chunk] = []

# Translation models
class TranslationBase(BaseModel):
    """Base model for translation data."""
    target_language: str
    name: str
    ai_model: str = "gpt-4.1-nano"
    
class TranslationCreate(TranslationBase):
    """Model for creating a new translation."""
    chunk_set_id: UUID4
    user_id: UUID4
    total_chunks: int

class TranslationUpdate(BaseModel):
    """Model for updating an existing translation."""
    status: Optional[str] = None
    completed_chunks: Optional[int] = None
    output_file_path: Optional[str] = None
    
class Translation(TranslationBase):
    """Model representing a translation in the database."""
    id: UUID4
    chunk_set_id: UUID4
    user_id: UUID4
    status: str
    completed_chunks: int
    total_chunks: int
    output_file_path: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config(Config):
        """Pydantic configuration."""
        orm_mode = True

# Translated chunk models
class TranslatedChunkBase(BaseModel):
    """Base model for translated chunk data."""
    translated_content: str
    sequence_number: int
    
class TranslatedChunkCreate(TranslatedChunkBase):
    """Model for creating a new translated chunk."""
    translation_id: UUID4
    chunk_id: UUID4
    
class TranslatedChunkUpdate(BaseModel):
    """Model for updating an existing translated chunk."""
    translated_content: Optional[str] = None
    
class TranslatedChunk(TranslatedChunkBase):
    """Model representing a translated chunk in the database."""
    id: UUID4
    translation_id: UUID4
    chunk_id: UUID4
    created_at: datetime
    updated_at: datetime
    
    class Config(Config):
        """Pydantic configuration."""
        orm_mode = True

class TranslationWithChunks(Translation):
    """Model representing a translation with its translated chunks."""
    translated_chunks: List[TranslatedChunk] = []
    
    model_config = {"extra": "allow"}
