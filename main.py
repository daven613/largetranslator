#!/usr/bin/env python3
"""
Main entry point for the Medical AI Chat application.
This script runs the FastAPI application using uvicorn.

How to run:
- Local development: python main.py
- On server/VM: python3 main.py
"""
import logging
from pathlib import Path
import uvicorn
from dotenv import load_dotenv
import os
import sys

# Add backend directory to Python path
project_root = Path(__file__).parent
backend_dir = project_root / "backend"
sys.path.append(str(backend_dir))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backend.log'),
        logging.StreamHandler()  # This sends output to terminal
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
env_path = Path(__file__).resolve().parent / 'backend' / '.env'
if env_path.exists():
    load_dotenv(env_path)
    logger.info(f"Loaded environment variables from {env_path}")
else:
    logger.warning(f"Warning: Environment file not found at {env_path}")

if __name__ == "__main__":
    # Get project root directory
    project_root = Path(__file__).resolve().parent
    logger.info("Starting Medical AI Chat application...")
    logger.info(f"Project root: {project_root}")
    
    # Get host and port from environment or use defaults
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    
    logger.info(f"Server will run at: http://{host}:{port}")
    
    # Start the server
    uvicorn.run(
        "backend.api.main:app",
        host=host,
        port=port,
        reload=True,
        reload_dirs=["backend"]
    ) 