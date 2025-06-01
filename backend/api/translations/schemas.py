"""
Schema definitions for translation API endpoints.
"""
from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, UUID4, Field

from ...helpers.json_utils import Config
from ...db.models import Translation

# Translation schemas
class TranslationCreateRequest(BaseModel):
    """Request model for creating a translation."""
    chunk_set_id: UUID4
    prompt: str

class TranslationResponse(BaseModel):
    """Response model for a translation."""
    id: UUID4
    chunk_set_id: UUID4
    user_id: UUID4
    target_language: str
    name: str
    status: str
    completed_chunks: int
    total_chunks: int
    ai_model: str
    output_file_path: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config(Config):
        """Pydantic configuration."""
        pass

class TranslationListResponse(BaseModel):
    """Response model for listing translations."""
    translations: List[TranslationResponse]

# Unified chunk schemas for translated chunks
class TranslatedChunkResponse(BaseModel):
    """Response model for a translated chunk using unified chunk design."""
    id: UUID4
    document_id: UUID4
    sequence_number: int
    content: str  # This is the translated content
    chunk_type: str = "translated"
    parent_chunk_id: Optional[UUID4] = None  # Reference to original chunk
    translation_id: Optional[UUID4] = None
    target_language: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config(Config):
        """Pydantic configuration."""
        pass

class TranslatedChunkListResponse(BaseModel):
    """Response model for listing translated chunks."""
    translated_chunks: List[TranslatedChunkResponse]

class TranslationWithChunksResponse(TranslationResponse):
    """Response model for a translation with its translated chunks."""
    translated_chunks: List[TranslatedChunkResponse]

# Chunk pair response for side-by-side comparison
class ChunkPairResponse(BaseModel):
    """Response model for original and translated chunk pair."""
    original_chunk: Dict[str, Any]
    translated_chunk: Optional[TranslatedChunkResponse] = None
    sequence_number: int
    
class TranslationDetailsResponse(BaseModel):
    """Response model for translation details with chunk pairs."""
    translation: TranslationResponse
    chunk_pairs: List[ChunkPairResponse]
    success_rate: float
    error_count: int
    total_chunks: int 