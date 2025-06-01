"""
Shared API dependencies.
Defines reusable dependency functions for FastAPI routes.
"""
import logging
from typing import Dict, Tuple
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from backend.external_services.supabase.auth_service import SupabaseAuthService

logger = logging.getLogger(__name__)

# Create OAuth2 scheme for token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Get the current authenticated user.
    
    This dependency can be used across all API endpoints that require authentication.
    
    Args:
        token: JWT token from request, extracted by FastAPI
        
    Returns:
        User data dict including id and email
        
    Raises:
        HTTPException: If authentication fails
    """
    user = await SupabaseAuthService.get_user(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

async def get_current_user_with_token(token: str = Depends(oauth2_scheme)) -> Tuple[Dict, str]:
    """
    Get the current authenticated user along with their JWT token.
    
    This is used when we need to create a user-specific Supabase client
    for Row Level Security to work properly.
    
    Args:
        token: JWT token from request, extracted by FastAPI
        
    Returns:
        Tuple of (user data dict, raw JWT token)
        
    Raises:
        HTTPException: If authentication fails
    """
    user = await SupabaseAuthService.get_user(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user, token 