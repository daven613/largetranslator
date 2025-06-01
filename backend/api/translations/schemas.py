"""
Schema definitions for translation API endpoints.
"""
from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, UUID4, Field

from ...helpers.json_utils import Config
from ...db.models import Translation, TranslatedChunk

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

# Translated chunk schemas
class TranslatedChunkResponse(BaseModel):
    """Response model for a translated chunk."""
    id: UUID4
    translation_id: UUID4
    chunk_id: UUID4
    translated_content: str
    sequence_number: int
    created_at: datetime
    updated_at: datetime
    
    class Config(Config):
        """Pydantic configuration."""
        pass

class TranslatedChunkListResponse(BaseModel):
    """Response model for listing translated chunks."""
    translated_chunks: List[TranslatedChunkResponse]

class TranslationWithChunksResponse(TranslationResponse):
    """Response model for a translation with its translated chunks."""
    translated_chunks: List[TranslatedChunkResponse] 