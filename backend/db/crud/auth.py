"""
CRUD operations for user authentication.
"""
import logging
from typing import Dict, Optional
from uuid import UUID

from pydantic import UUID4

from ...external_services.supabase.client import get_supabase_client

logger = logging.getLogger(__name__)


async def get_user_by_id(user_id: UUID4) -> Optional[Dict]:
    """
    Get a user by ID.
    
    Args:
        user_id: User ID
        
    Returns:
        User data or None if not found
    """
    try:
        client = get_supabase_client()
        
        # Get user
        result = client.table('auth.users').select('*').eq('id', str(user_id)).execute()
        
        if not result.data:
            return None
            
        return result.data[0]
    except Exception as e:
        logger.error(f"Failed to get user: {str(e)}")
        raise 