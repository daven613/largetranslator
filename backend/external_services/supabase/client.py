"""
Supabase client initialization and management.
"""
import os
import logging
from supabase import create_client, Client

logger = logging.getLogger(__name__)

class SupabaseClient:
    _instance = None
    _client = None
    
    @classmethod
    def get_instance(cls) -> Client:
        """
        Get or create Supabase client instance.
        Returns a singleton instance of the Supabase client.
        """
        if cls._client is None:
            cls._initialize_client()
        return cls._client
    
    @classmethod
    def _initialize_client(cls) -> None:
        """Initialize the Supabase client with credentials from environment variables."""
        try:
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_KEY")
            
            if not supabase_url or not supabase_key:
                logger.error("Supabase credentials not found in environment variables")
                raise ValueError("Supabase credentials are missing. Please check your .env file.")
            
            cls._client = create_client(supabase_url, supabase_key)
            logger.info("Supabase client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {str(e)}")
            raise

# Convenience function to get client
def get_supabase_client() -> Client:
    """Get the Supabase client instance."""
    return SupabaseClient.get_instance() 