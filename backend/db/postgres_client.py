"""
Direct PostgreSQL client using asyncpg for high-performance database operations.
This bypasses Supabase's REST API to avoid HTTP connection limits.
"""
import asyncio
import logging
import os
from typing import Dict, List, Any, Optional, Union
from uuid import UUID
import asyncpg
import json
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

class PostgreSQLClient:
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
        self._initialized = False
        
    async def initialize(self):
        """Initialize the PostgreSQL connection pool."""
        if self._initialized:
            return
            
        try:
            # Get database URL from Supabase environment
            database_url = os.environ.get("SUPABASE_DB_URL")
            logger.info(f"SUPABASE_DB_URL from environment: {database_url[:50]}..." if database_url else "SUPABASE_DB_URL not found")
            
            if not database_url:
                # Fall back to constructing from individual components
                host = os.environ.get("SUPABASE_DB_HOST", "localhost")
                port = int(os.environ.get("SUPABASE_DB_PORT", "5432"))
                database = os.environ.get("SUPABASE_DB_NAME", "postgres")
                user = os.environ.get("SUPABASE_DB_USER", "postgres")
                password = os.environ.get("SUPABASE_DB_PASSWORD", "")
                
                logger.info(f"Constructing DB URL from components - Host: {host}, Port: {port}, User: {user}, DB: {database}")
                database_url = f"postgresql://{user}:{password}@{host}:{port}/{database}"
            
            logger.info(f"Final database URL: postgresql://{database_url.split('://')[1].split(':')[0]}:***@{database_url.split('@')[1] if '@' in database_url else 'unknown'}")
            
            # Test the connection first before creating the pool
            logger.info("Testing PostgreSQL connection...")
            test_conn = await asyncpg.connect(database_url)
            await test_conn.close()
            logger.info("PostgreSQL connection test successful")
            
            # Create connection pool with optimized settings for mixed workload
            # Reserving connections for API endpoints while allowing background task concurrency
            self.pool = await asyncpg.create_pool(
                database_url,
                min_size=10,     # Higher minimum for immediate API response
                max_size=60,     # Increased max to handle background tasks
                max_queries=1000, # Queries per connection
                max_inactive_connection_lifetime=300,  # 5 minutes
                command_timeout=30,  # 30 second timeout per query
                server_settings={
                    'jit': 'off',  # Disable JIT for faster simple queries
                }
            )
            
            self._initialized = True
            logger.info("PostgreSQL client initialized with pool: min=10, max=60 connections (optimized for mixed API + background workload)")
            
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL client: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            if "does not appear to be an IPv4 or IPv6 address" in str(e):
                logger.error("This appears to be a hostname resolution issue.")
                logger.error("Please check your SUPABASE_DB_URL in the .env file.")
                logger.error("The correct format should be: postgresql://postgres:[password]@db.[project-ref].supabase.co:5432/postgres")
            raise
            
    async def close(self):
        """Close the connection pool."""
        if self.pool:
            await self.pool.close()
            self.pool = None
            self._initialized = False
            logger.info("PostgreSQL client closed")

    @asynccontextmanager
    async def get_connection(self):
        """Get a connection from the pool."""
        if not self._initialized:
            await self.initialize()
            
        conn = await self.pool.acquire()
        try:
            yield conn
        finally:
            await self.pool.release(conn)

    async def fetch_one(self, table: str, filters: Dict[str, Any] = None, select: str = "*") -> Optional[Dict[str, Any]]:
        """Fetch one record from table."""
        async with self.get_connection() as conn:
            where_clause = ""
            values = []
            
            if filters:
                where_conditions = []
                for i, (key, value) in enumerate(filters.items(), 1):
                    where_conditions.append(f"{key} = ${i}")
                    values.append(value)
                where_clause = f" WHERE {' AND '.join(where_conditions)}"
            
            query = f"SELECT {select} FROM {table}{where_clause} LIMIT 1"
            
            row = await conn.fetchrow(query, *values)
            return dict(row) if row else None
    
    async def fetch_all(self, table: str, filters: Dict[str, Any] = None, select: str = "*", 
                       order_by: Optional[str] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Fetch all records from table."""
        async with self.get_connection() as conn:
            where_clause = ""
            values = []
            
            if filters:
                where_conditions = []
                for i, (key, value) in enumerate(filters.items(), 1):
                    where_conditions.append(f"{key} = ${i}")
                    values.append(value)
                where_clause = f" WHERE {' AND '.join(where_conditions)}"
            
            query = f"SELECT {select} FROM {table}{where_clause}"
            
            if order_by:
                query += f" ORDER BY {order_by}"
            if limit:
                query += f" LIMIT {limit}"
            
            rows = await conn.fetch(query, *values)
            return [dict(row) for row in rows]
    
    async def insert_returning(self, table: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Insert record and return it."""
        async with self.get_connection() as conn:
            columns = list(data.keys())
            values = list(data.values())
            placeholders = [f"${i+1}" for i in range(len(values))]
            
            # Convert JSON-serializable values
            processed_values = []
            for value in values:
                if isinstance(value, (dict, list)):
                    processed_values.append(json.dumps(value))
                elif isinstance(value, UUID):
                    processed_values.append(str(value))
                else:
                    processed_values.append(value)
            
            query = f"""
                INSERT INTO {table} ({', '.join(columns)}) 
                VALUES ({', '.join(placeholders)}) 
                RETURNING *
            """
            
            row = await conn.fetchrow(query, *processed_values)
            return dict(row) if row else None
    
    async def update_returning(self, table: str, data: Dict[str, Any], 
                              filters: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update record and return it."""
        async with self.get_connection() as conn:
            set_clauses = []
            values = []
            
            # Process update data
            for i, (key, value) in enumerate(data.items(), 1):
                set_clauses.append(f"{key} = ${i}")
                if isinstance(value, (dict, list)):
                    values.append(json.dumps(value))
                elif isinstance(value, UUID):
                    values.append(str(value))
                else:
                    values.append(value)
            
            # Process where conditions
            where_conditions = []
            for key, value in filters.items():
                values.append(value)
                where_conditions.append(f"{key} = ${len(values)}")
            
            query = f"""
                UPDATE {table} 
                SET {', '.join(set_clauses)} 
                WHERE {' AND '.join(where_conditions)} 
                RETURNING *
            """
            
            row = await conn.fetchrow(query, *values)
            return dict(row) if row else None
    
    async def delete_returning(self, table: str, filters: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Delete record and return it."""
        async with self.get_connection() as conn:
            where_conditions = []
            values = []
            
            for i, (key, value) in enumerate(filters.items(), 1):
                where_conditions.append(f"{key} = ${i}")
                values.append(value)
            
            query = f"""
                DELETE FROM {table} 
                WHERE {' AND '.join(where_conditions)} 
                RETURNING *
            """
            
            row = await conn.fetchrow(query, *values)
            return dict(row) if row else None

    async def execute_query(self, query: str, *args) -> Any:
        """Execute raw SQL query."""
        async with self.get_connection() as conn:
            return await conn.fetch(query, *args)

    async def execute_transaction(self, operations: List[tuple]) -> List[Any]:
        """
        Execute multiple operations in a transaction.
        
        Args:
            operations: List of (method_name, args, kwargs) tuples
            
        Returns:
            List of results from each operation
        """
        async with self.get_connection() as conn:
            async with conn.transaction():
                results = []
                for method_name, args, kwargs in operations:
                    method = getattr(self, method_name)
                    result = await method(*args, **kwargs)
                    results.append(result)
                return results

# Global client instance
_pg_client: Optional[PostgreSQLClient] = None

async def get_postgres_client() -> PostgreSQLClient:
    """Get the global PostgreSQL client instance."""
    global _pg_client
    if _pg_client is None:
        _pg_client = PostgreSQLClient()
        await _pg_client.initialize()
    return _pg_client

async def close_postgres_client():
    """Close the global PostgreSQL client."""
    global _pg_client
    if _pg_client:
        await _pg_client.close()
        _pg_client = None 