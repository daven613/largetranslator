"""
Authentication service for Supabase.
Provides methods for user signup, login, and token verification.
"""
import logging
import base64
import json
import time
import os
import asyncio
from typing import Dict, Any, Optional
from supabase import Client
from .client import get_supabase_client

logger = logging.getLogger(__name__)

# Simple in-memory cache for token validation
_token_cache: Dict[str, Dict[str, Any]] = {}
_cache_ttl = 300  # 5 minutes

class SupabaseAuthService:
    @staticmethod
    def _get_auth_client() -> Client:
        """Helper to get a Supabase client with service role for auth operations."""
        supabase_url = os.environ.get("SUPABASE_URL", "")
        # Use SUPABASE_SERVICE_ROLE_KEY for auth operations.
        supabase_service_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")

        if not supabase_url or not supabase_service_key:
            logger.error("Supabase URL or SUPABASE_SERVICE_ROLE_KEY not found for auth service")
            raise Exception("SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY is missing for auth operations.")
        
        # Need to import create_client here if it's not already available globally in this file
        from supabase import create_client
        return create_client(supabase_url, supabase_service_key)

    @staticmethod
    async def sign_up(email: str, password: str) -> Dict[str, Any]:
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
            # Run synchronous Supabase call in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, 
                SupabaseAuthService._sync_sign_up, 
                email, 
                password
            )
            return result
        except Exception as e:
            logger.error(f"Error during signup: {str(e)}")
            raise
    
    @staticmethod
    def _sync_sign_up(email: str, password: str) -> Dict[str, Any]:
        """Synchronous signup helper."""
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
    
    @staticmethod
    async def sign_in(email: str, password: str) -> Dict[str, Any]:
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
            # Run synchronous Supabase call in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, 
                SupabaseAuthService._sync_sign_in, 
                email, 
                password
            )
            return result
        except Exception as e:
            logger.error(f"Error during authentication: {str(e)}")
            raise
    
    @staticmethod
    def _sync_sign_in(email: str, password: str) -> Dict[str, Any]:
        """Synchronous sign in helper."""
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
    async def get_user(token: str) -> Optional[Dict[str, Any]]:
        """
        Get user information from JWT token with caching.
        
        Args:
            token: JWT token
            
        Returns:
            User data dict or None if invalid
        """
        try:
            # Check cache first
            current_time = int(time.time())
            if token in _token_cache:
                cached_data = _token_cache[token]
                if cached_data['cached_at'] + _cache_ttl > current_time:
                    logger.debug("Token validation cache hit")
                    return cached_data['user_data']
                else:
                    # Remove expired cache entry
                    del _token_cache[token]
            
            # Validate token
            user_data = await SupabaseAuthService._validate_token(token)
            
            # Cache the result if valid
            if user_data:
                _token_cache[token] = {
                    'user_data': user_data,
                    'cached_at': current_time
                }
                logger.debug("Token validation result cached")
            
            return user_data
            
        except Exception as e:
            logger.error(f"Error validating token: {str(e)}")
            return None
    
    @staticmethod
    async def _validate_token(token: str) -> Optional[Dict[str, Any]]:
        """
        Validate JWT token asynchronously.
        
        Args:
            token: JWT token
            
        Returns:
            User data dict or None if invalid
        """
        try:
            # Run token validation in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, 
                SupabaseAuthService._sync_validate_token, 
                token
            )
            return result
        except Exception as e:
            logger.error(f"Error in async token validation: {str(e)}")
            return None
    
    @staticmethod
    def _sync_validate_token(token: str) -> Optional[Dict[str, Any]]:
        """
        Synchronous token validation helper.
        
        Args:
            token: JWT token
            
        Returns:
            User data dict or None if invalid
        """
        try:
            # Decode the JWT payload (second part)
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
    
    @staticmethod
    def clear_token_cache():
        """Clear the token validation cache."""
        global _token_cache
        _token_cache.clear()
        logger.info("Token validation cache cleared") 