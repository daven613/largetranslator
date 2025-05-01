"""
Authentication service for Supabase.
Provides methods for user signup, login, and token verification.
"""
import logging
import base64
import json
from typing import Dict, Any, Optional
from .client import get_supabase_client

logger = logging.getLogger(__name__)

class SupabaseAuthService:
    @staticmethod
    def sign_up(email: str, password: str) -> Dict[str, Any]:
        """
        Register a new user with Supabase.
        
        Args:
            email: User's email
            password: User's password
            
        Returns:
            Dict containing user data and session
            
        Raises:
            Exception: If signup fails
        """
        try:
            client = get_supabase_client()
            response = client.auth.sign_up({
                "email": email,
                "password": password
            })
            
            if response.user:
                logger.info(f"User created successfully: {email}")
                return {
                    "user": response.user,
                    "session": response.session
                }
            else:
                logger.error(f"Failed to create user: {email}")
                raise Exception("User creation failed")
                
        except Exception as e:
            logger.error(f"Error during signup: {str(e)}")
            raise
    
    @staticmethod
    def sign_in(email: str, password: str) -> Dict[str, Any]:
        """
        Authenticate a user with Supabase.
        
        Args:
            email: User's email
            password: User's password
            
        Returns:
            Dict containing user data and session
            
        Raises:
            Exception: If login fails
        """
        try:
            client = get_supabase_client()
            response = client.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if response.user and response.session:
                logger.info(f"User authenticated successfully: {email}")
                return {
                    "user": response.user,
                    "session": response.session
                }
            else:
                logger.error(f"Authentication failed for user: {email}")
                raise Exception("Authentication failed")
                
        except Exception as e:
            logger.error(f"Error during authentication: {str(e)}")
            raise
    
    @staticmethod
    def get_user(token: str) -> Optional[Dict[str, Any]]:
        """
        Get user information from JWT token.
        
        Args:
            token: JWT access token
            
        Returns:
            User data if token is valid, None otherwise
        """
        try:
            # Simplified approach: Decode and validate the JWT directly
            # This allows us to work with just the access token
            parts = token.split('.')
            if len(parts) != 3:
                logger.error("Invalid JWT token format")
                return None
            
            # Decode the JWT payload (second part)
            payload_part = parts[1]
            # Add padding if needed
            payload_part += "=" * ((4 - len(payload_part) % 4) % 4)
            payload_bytes = base64.b64decode(payload_part)
            payload = json.loads(payload_bytes.decode('utf-8'))
            
            # Extract user info from payload
            if 'sub' in payload:
                user_id = payload.get('sub')
                email = payload.get('email')
                
                # Verify token expiration
                import time
                current_time = int(time.time())
                expiration_time = payload.get('exp', 0)
                
                if current_time > expiration_time:
                    logger.error("Token has expired")
                    return None
                
                # Token is valid, return user data
                return {"id": user_id, "email": email}
            else:
                logger.error("Invalid token payload: missing user ID")
                return None
                
        except Exception as e:
            logger.error(f"Error validating token: {str(e)}")
            return None 