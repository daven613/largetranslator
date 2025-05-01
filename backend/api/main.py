"""
Main FastAPI application.
Includes all API routes and sets up middleware.
"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .auth import router as auth_router
from .files import router as files_router

# Configure logging
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Large Translator API",
    description="API for the Large Translator application",
    version="0.1.0"
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

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}

# Startup event
@app.on_event("startup")
async def startup_event():
    """Run when the API starts up."""
    logger.info("API starting up")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Run when the API shuts down."""
    logger.info("API shutting down") 