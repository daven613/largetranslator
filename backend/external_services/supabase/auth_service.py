"""
Authentication service for Supabase.
Provides methods for user signup, login, and token verification.
"""
import logging
import base64
import json
import time
import os
from typing import Dict, Any, Optional
from supabase import Client
from .client import get_supabase_client

logger = logging.getLogger(__name__)

class SupabaseAuthService:
    @staticmethod
    def _get_auth_client() -> Client:
        """Helper to get a Supabase client with service role for auth operations."""
        supabase_url = os.environ.get("SUPABASE_URL", "")
        # Use SUPABASE_SERVICE_ROLE_KEY for auth operations.
        supabase_service_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")

        if not supabase_url or not supabase_service_key:
            logger.error("Supabase URL or SUPABASE_SERVICE_ROLE_KEY not found for auth service")
            raise Exception("SupABASE_URL or SUPABASE_SERVICE_ROLE_KEY is missing for auth operations.")
        
        # Need to import create_client here if it's not already available globally in this file
        from supabase import create_client
        return create_client(supabase_url, supabase_service_key)

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
            client = SupabaseAuthService._get_auth_client()
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
            client = SupabaseAuthService._get_auth_client()
            response = client.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if response.user and response.session:
                logger.info(f"User authenticated successfully: {email}")
                
                # Debug: Log token details
                token = response.session.access_token
                SupabaseAuthService._log_token_details(token)
                
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
    def _log_token_details(token: str) -> None:
        """Debug helper to log token details including expiration."""
        try:
            # Decode the JWT payload (second part)
            parts = token.split('.')
            if len(parts) != 3:
                logger.error("Invalid JWT token format for debugging")
                return
            
            # Decode the payload
            payload_part = parts[1]
            # Add padding if needed
            payload_part += "=" * ((4 - len(payload_part) % 4) % 4)
            payload_bytes = base64.b64decode(payload_part)
            payload = json.loads(payload_bytes.decode('utf-8'))
            
            # Log important token details
            logger.info("====== TOKEN DEBUG INFO ======")
            logger.info(f"TOKEN PAYLOAD: {json.dumps(payload, indent=2)}")
            
            # Check and log expiration details
            if 'exp' in payload:
                exp_time = payload['exp']
                current_time = int(time.time())
                time_left = exp_time - current_time
                
                logger.info(f"TOKEN EXPIRES AT: {exp_time} (Unix timestamp)")
                logger.info(f"CURRENT TIME: {current_time} (Unix timestamp)")
                logger.info(f"TIME UNTIL EXPIRATION: {time_left} seconds ({time_left/60:.2f} minutes)")
                
                # Format as human-readable time
                from datetime import datetime
                exp_datetime = datetime.fromtimestamp(exp_time)
                logger.info(f"EXPIRATION DATE/TIME: {exp_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                logger.info("NO EXPIRATION FOUND IN TOKEN")
                
            logger.info("==============================")
        except Exception as e:
            logger.error(f"Error decoding token for debug: {str(e)}")
    
    @staticmethod
    def get_user(token: str) -> Optional[Dict[str, Any]]:
        """
        Get user information from JWT token.
        This method primarily decodes the token and checks its validity (like expiration).
        It does not strictly need a Supabase client if we are just decoding.
        However, if Supabase client's `auth.get_user(token)` is preferred, 
        it should use a client initialized with the ANON key for consistency, 
        as `get_user` is often about validating a user-provided token.

        For this implementation, we continue with direct decoding as it was.
        If a client-based approach is needed, it should use the anon key.
        """
        try:
            # Simplified approach: Decode and validate the JWT directly
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