"""
Supabase client module.
"""
import os
import logging
from typing import Optional
from supabase import create_client, Client

logger = logging.getLogger(__name__)

# Global client instance
_supabase_client: Optional[Client] = None

def initialize_supabase() -> Client:
    """
    Initialize the Supabase client with credentials for service/admin operations.
    It will use SUPABASE_SERVICE_ROLE_KEY.
    
    Returns:
        Initialized Supabase client
    
    Raises:
        Exception: If credentials are missing
    """
    supabase_url = os.environ.get("SUPABASE_URL", "")
    # For service/admin operations, use the dedicated service role key
    supabase_service_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
    
    if not supabase_url or not supabase_service_key:
        logger.error("Supabase URL or SUPABASE_SERVICE_ROLE_KEY not found for service client")
        raise Exception("Supabase URL or SUPABASE_SERVICE_ROLE_KEY is missing for service client.")
    
    try:
        client = create_client(supabase_url, supabase_service_key)
        logger.info("Supabase service client initialized successfully using SUPABASE_SERVICE_ROLE_KEY")
        return client
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {str(e)}")
        raise

def get_supabase_client() -> Client:
    """
    Get the Supabase client instance, initializing it if needed.
    
    Returns:
        Supabase client instance
    """
    global _supabase_client
    
    if _supabase_client is None:
        _supabase_client = initialize_supabase()
    
    return _supabase_client

def get_user_supabase_client(access_token: str) -> Client:
    """
    Get a user-specific Supabase client with the user's JWT token for RLS.
    
    This client will have the proper auth context set so that Row Level Security
    policies work correctly with the authenticated user's permissions.
    
    Args:
        access_token: The user's JWT access token
        
    Returns:
        Supabase client instance with user auth context
    """
    try:
        supabase_url = os.environ.get("SUPABASE_URL", "")
        # For user-specific client with RLS, we *must* use the anon key.
        # This is named SUPABASE_ANON_PUBLIC in the .env file.
        supabase_anon_key = os.environ.get("SUPABASE_ANON_PUBLIC", "")
        
        if not supabase_url or not supabase_anon_key:
            logger.error("Supabase URL or SUPABASE_ANON_PUBLIC key not found for user client")
            raise Exception("Supabase URL or SUPABASE_ANON_PUBLIC key is missing for user client.")
        
        # Create a client with the anon key for user authentication with RLS
        client = create_client(supabase_url, supabase_anon_key)
            
        # Set auth on PostgREST client for database operations (works for both methods)
        # This is the key method mentioned in GitHub issue #420
        try:
            client.postgrest.auth(access_token)
            logger.debug(f"Set auth token on PostgREST client for RLS")
        except Exception as postgrest_error:
            logger.error(f"Failed to set auth on PostgREST client: {postgrest_error}")
            raise Exception("Could not set authentication context for database operations")
        
        # Set auth on storage client for storage operations
        try:
            # For storage, we need to set the Authorization header
            if hasattr(client, 'storage'):
                if hasattr(client.storage, 'session') and hasattr(client.storage.session, 'headers'):
                    client.storage.session.headers.update({"Authorization": f"Bearer {access_token}"})
                    logger.debug(f"Set Authorization header on storage client session")
                elif hasattr(client.storage, '_client') and hasattr(client.storage._client, 'session'):
                    client.storage._client.session.headers.update({"Authorization": f"Bearer {access_token}"})
                    logger.debug(f"Set Authorization header on storage _client session")
        except Exception as storage_error:
            logger.warning(f"Failed to set auth on storage client: {storage_error}")
        
        logger.info(f"Created user-specific Supabase client with auth context")
        return client
        
    except Exception as e:
        logger.error(f"Failed to create user-specific Supabase client: {str(e)}")
        raise 