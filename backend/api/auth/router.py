"""
Authentication router for FastAPI.
Defines endpoints for user signup and login.
"""
import logging
from fastapi import APIRouter, HTTPException, status
from . import schemas
from ...external_services.supabase.auth_service import SupabaseAuthService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/signup", response_model=schemas.AuthResponse, status_code=status.HTTP_201_CREATED)
async def signup(user_data: schemas.UserSignup):
    """
    Register a new user.
    
    Args:
        user_data: User signup data including email and password
        
    Returns:
        User data and authentication token
        
    Raises:
        HTTPException: If signup fails
    """
    try:
        response = SupabaseAuthService.sign_up(
            email=user_data.email,
            password=user_data.password
        )
        
        # Format the response according to our schema
        user = response["user"]
        session = response["session"]
        
        return {
            "user": {
                "id": user.id,
                "email": user.email
            },
            "token": {
                "access_token": session.access_token,
                "token_type": "bearer"
            }
        }
    except Exception as e:
        logger.error(f"Signup failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create user: {str(e)}"
        )

@router.post("/login", response_model=schemas.AuthResponse)
async def login(user_data: schemas.UserLogin):
    """
    Authenticate a user.
    
    Args:
        user_data: User login data including email and password
        
    Returns:
        User data and authentication token
        
    Raises:
        HTTPException: If login fails
    """
    try:
        response = SupabaseAuthService.sign_in(
            email=user_data.email,
            password=user_data.password
        )
        
        # Format the response according to our schema
        user = response["user"]
        session = response["session"]
        
        return {
            "user": {
                "id": user.id,
                "email": user.email
            },
            "token": {
                "access_token": session.access_token,
                "token_type": "bearer"
            }
        }
    except Exception as e:
        logger.error(f"Login failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        ) 