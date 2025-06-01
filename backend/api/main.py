"""
Main FastAPI application.
Includes all API routes and sets up middleware.
"""
import logging
import os
from dotenv import load_dotenv
from contextlib import asynccontextmanager

# Load environment variables from .env file in the backend directory
# This should be one of the first things done, before other modules try to access env vars.
ENV_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env") # Assuming main.py is in api/ and .env is in backend/
load_dotenv(ENV_PATH)

# Also try loading from the project root in case .env is there
PROJECT_ROOT_ENV = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
if os.path.exists(PROJECT_ROOT_ENV):
    load_dotenv(PROJECT_ROOT_ENV, override=True)
    print(f"Loaded environment from project root: {PROJECT_ROOT_ENV}")
elif os.path.exists(ENV_PATH):
    print(f"Loaded environment from backend dir: {ENV_PATH}")
else:
    print(f"Warning: No .env file found at {ENV_PATH} or {PROJECT_ROOT_ENV}")

# Debug: Check if SUPABASE_DB_URL is loaded
supabase_db_url = os.environ.get("SUPABASE_DB_URL")
print(f"SUPABASE_DB_URL loaded: {'Yes' if supabase_db_url else 'No'}")
if supabase_db_url:
    print(f"DB URL (masked): {supabase_db_url[:30]}...")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .auth import router as auth_router
from .files import router as files_router
from .chunking import router as chunking_router
from .translations import router as translations_router
from .debug_env_router import router as debug_router

# Configure logging
logger = logging.getLogger(__name__)

# Lifespan context manager for startup and shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan with proper async setup and teardown."""
    logger.info("API starting up - initializing direct PostgreSQL connection pool")
    
    # Initialize the direct PostgreSQL client for high-performance operations
    try:
        from backend.db.postgres_client import get_postgres_client
        pg_client = await get_postgres_client()  # This will initialize the connection pool
        logger.info("Direct PostgreSQL connection pool initialized successfully")
        logger.info("High-concurrency parallel translation system ready!")
    except Exception as e:
        logger.error(f"Failed to initialize PostgreSQL connection: {str(e)}")
        raise RuntimeError("PostgreSQL connection is required for the application to run")
    
    yield  # Application runs here
    
    # Cleanup on shutdown
    logger.info("API shutting down - closing database connections")
    try:
        # Close PostgreSQL connections
        from backend.db.postgres_client import close_postgres_client
        await close_postgres_client()
        logger.info("PostgreSQL connections closed successfully")
    except Exception as e:
        logger.warning(f"Error closing PostgreSQL connections: {e}")

# Create FastAPI app with lifespan management
app = FastAPI(
    title="Large Translator API",
    description="API for the Large Translator application with high-concurrency parallel processing",
    version="0.2.0",  # Updated version to reflect new architecture
    lifespan=lifespan
)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router, prefix="/api")
app.include_router(files_router, prefix="/api")
app.include_router(chunking_router, prefix="/api")
app.include_router(translations_router, prefix="/api/translations", tags=["translations"])
app.include_router(debug_router, prefix="/api")

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    try:
        from backend.db.postgres_client import get_postgres_client
        pg_client = await get_postgres_client()
        
        # Test the connection
        result = await pg_client.fetch_one("SELECT 1 as test", {})
        
        return {
            "status": "ok", 
            "database": "direct_postgresql",
            "connection": "active",
            "high_concurrency": True,
            "parallel_batch_size": os.environ.get("PARALLEL_TRANSLATION_BATCH_SIZE", "10"),
            "test_query": result["test"] if result else None
        }
    except Exception as e:
        return {
            "status": "error", 
            "database": "direct_postgresql",
            "connection": "failed",
            "error": str(e),
            "high_concurrency": False
        } 