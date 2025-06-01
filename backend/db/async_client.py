"""
Async wrapper for Supabase client.
Provides async operations using thread pools for sync Supabase operations.
"""
import asyncio
import logging
import os
from typing import Dict, List, Any, Optional
from functools import wraps

from ..external_services.supabase.client import get_supabase_client

logger = logging.getLogger(__name__)

def async_supabase_operation(func):
    """Decorator to convert sync Supabase operations to async using thread pool."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, func, *args, **kwargs)
    return wrapper

class AsyncSupabaseClient:
    def __init__(self):
        self.client = None
        self._initialized = False
        
    async def initialize(self):
        """Initialize the Supabase client."""
        if not self._initialized:
            # Get the sync client - this is fast, no network calls
            self.client = get_supabase_client()
            self._initialized = True
            logger.info("Async Supabase client initialized successfully")
    
    async def close(self):
        """Close the client (no-op for Supabase client)."""
        if self._initialized:
            self._initialized = False
            logger.info("Async Supabase client closed")
    
    @async_supabase_operation
    def _sync_fetch_one(self, table: str, filters: Dict[str, Any] = None, select: str = "*") -> Optional[Dict[str, Any]]:
        """Sync method to fetch one record."""
        query = self.client.table(table).select(select)
        
        if filters:
            for key, value in filters.items():
                query = query.eq(key, value)
        
        result = query.execute()
        return result.data[0] if result.data else None
    
    @async_supabase_operation
    def _sync_fetch_all(self, table: str, filters: Dict[str, Any] = None, select: str = "*") -> List[Dict[str, Any]]:
        """Sync method to fetch all records."""
        query = self.client.table(table).select(select)
        
        if filters:
            for key, value in filters.items():
                query = query.eq(key, value)
        
        result = query.execute()
        return result.data if result.data else []
    
    @async_supabase_operation
    def _sync_insert(self, table: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Sync method to insert a record."""
        result = self.client.table(table).insert(data).execute()
        return result.data[0] if result.data else None
    
    @async_supabase_operation
    def _sync_update(self, table: str, data: Dict[str, Any], filters: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Sync method to update a record."""
        query = self.client.table(table).update(data)
        
        if filters:
            for key, value in filters.items():
                query = query.eq(key, value)
        
        result = query.execute()
        return result.data[0] if result.data else None
    
    @async_supabase_operation
    def _sync_delete(self, table: str, filters: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Sync method to delete a record."""
        query = self.client.table(table).delete()
        
        if filters:
            for key, value in filters.items():
                query = query.eq(key, value)
        
        result = query.execute()
        return result.data[0] if result.data else None
    
    # Public async methods
    async def fetch_one(self, table: str, filters: Dict[str, Any] = None, select: str = "*") -> Optional[Dict[str, Any]]:
        """Async method to fetch one record."""
        if not self._initialized:
            await self.initialize()
        return await self._sync_fetch_one(table, filters, select)
    
    async def fetch_all(self, table: str, filters: Dict[str, Any] = None, select: str = "*") -> List[Dict[str, Any]]:
        """Async method to fetch all records."""
        if not self._initialized:
            await self.initialize()
        return await self._sync_fetch_all(table, filters, select)
    
    async def insert_returning(self, table: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Async method to insert and return the record."""
        if not self._initialized:
            await self.initialize()
        return await self._sync_insert(table, data)
    
    async def update_returning(self, table: str, data: Dict[str, Any], filters: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Async method to update and return the record."""
        if not self._initialized:
            await self.initialize()
        return await self._sync_update(table, data, filters)
    
    async def delete_returning(self, table: str, filters: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Async method to delete and return the record."""
        if not self._initialized:
            await self.initialize()
        return await self._sync_delete(table, filters)

# Global client instance
_db_client: Optional[AsyncSupabaseClient] = None

async def get_db_client() -> AsyncSupabaseClient:
    """Get the global async Supabase client instance."""
    global _db_client
    if _db_client is None:
        _db_client = AsyncSupabaseClient()
        await _db_client.initialize()
    return _db_client

async def close_db_client():
    """Close the global async Supabase client."""
    global _db_client
    if _db_client:
        await _db_client.close()
        _db_client = None 