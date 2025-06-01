"""
JSON utilities for the Large Translator application.
"""
from uuid import UUID
from typing import Any, Dict

# Simple Config class for UUID serialization
class Config:
    """Pydantic configuration with UUID serialization."""
    json_encoders = {UUID: str}
    
def convert_uuids_to_str(data: Any) -> Any:
    """
    Recursively convert all UUID values in a dictionary or list to strings.
    
    Args:
        data: Any data structure that might contain UUIDs
        
    Returns:
        Same data structure with UUIDs converted to strings
    """
    if isinstance(data, UUID):
        return str(data)
    elif isinstance(data, dict):
        return {k: convert_uuids_to_str(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [convert_uuids_to_str(item) for item in data]
    elif isinstance(data, tuple):
        return tuple(convert_uuids_to_str(item) for item in data)
    else:
        return data 