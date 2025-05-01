"""
Supabase Storage service for file operations.
"""
import io
import logging
import os
from typing import Dict, List, Any, BinaryIO
from datetime import datetime
import mimetypes
from .client import get_supabase_client

logger = logging.getLogger(__name__)

# Bucket name for user text files
TEXT_FILES_BUCKET = "user-text-files"

class SupabaseStorageService:
    """Service for interacting with Supabase Storage"""
    
    @classmethod
    def initialize_storage(cls) -> None:
        """
        Initialize storage by creating necessary buckets if they don't exist.
        Note: For first-time setup, you need to run the admin script:
        python -m backend.api.admin --create-bucket
        """
        try:
            client = get_supabase_client()
            
            # Check if we can access the bucket directly
            # (we don't try to create it here as that might require elevated permissions)
            try:
                client.storage.from_(TEXT_FILES_BUCKET).list()
                logger.info(f"Successfully accessed bucket '{TEXT_FILES_BUCKET}'")
            except Exception as e:
                logger.error(f"Error accessing bucket: {str(e)}")
                logger.error(f"The bucket '{TEXT_FILES_BUCKET}' might not exist yet.")
                logger.error(f"Run 'python -m backend.api.admin --create-bucket' to create it.")
                raise Exception(f"Bucket '{TEXT_FILES_BUCKET}' is not accessible. Run the admin script to create it.")
                
        except Exception as e:
            logger.error(f"Failed to initialize storage: {str(e)}")
            raise
    
    @classmethod
    def upload_file(cls, user_id: str, file_name: str, file_content: bytes, content_type: str = None) -> Dict[str, Any]:
        """
        Upload a file to Supabase storage.
        
        Args:
            user_id: ID of the user uploading the file
            file_name: Name of the file
            file_content: Binary content of the file
            content_type: MIME type of the file
            
        Returns:
            Dictionary with metadata of the uploaded file
        """
        try:
            # Ensure the bucket exists
            cls.initialize_storage()
            
            # Generate a path that includes the user ID to separate files by user
            file_path = f"{user_id}/{file_name}"
            
            # If content type is not provided, try to guess it
            if not content_type:
                content_type, _ = mimetypes.guess_type(file_name)
                if not content_type:
                    content_type = "text/plain"  # Default to text/plain
            
            # Upload the file
            client = get_supabase_client()
            result = client.storage.from_(TEXT_FILES_BUCKET).upload(
                file_path,
                file_content,
                {"content-type": content_type}
            )
            
            # Get file metadata
            file_url = client.storage.from_(TEXT_FILES_BUCKET).get_public_url(file_path)
            file_size = len(file_content)
            
            return {
                "file_id": file_path,  # Use the path as ID
                "file_name": file_name,
                "file_size": file_size,
                "content_type": content_type,
                "created_at": datetime.now().isoformat(),
                "url": file_url
            }
        except Exception as e:
            logger.error(f"Failed to upload file: {str(e)}")
            raise
    
    @classmethod
    def list_files(cls, user_id: str) -> List[Dict[str, Any]]:
        """
        List all files for a user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            List of file metadata
        """
        try:
            # Ensure the bucket exists
            cls.initialize_storage()
            
            client = get_supabase_client()
            
            # List files in the user's directory
            files = client.storage.from_(TEXT_FILES_BUCKET).list(user_id)
            
            # Format the response
            result = []
            for file in files:
                # Create file path
                file_path = f"{user_id}/{file['name']}"
                
                result.append({
                    "file_id": file_path,
                    "file_name": file["name"],
                    "file_size": file.get("metadata", {}).get("size", 0),
                    "content_type": file.get("metadata", {}).get("mimetype", "text/plain"),
                    "created_at": file.get("created_at", datetime.now().isoformat())
                })
            
            return result
        except Exception as e:
            logger.error(f"Failed to list files: {str(e)}")
            # Return empty list instead of raising if bucket doesn't exist yet
            if "bucket does not exist" in str(e).lower() or "bucket not found" in str(e).lower():
                logger.warning("Bucket not found, returning empty list")
                return []
            raise
    
    @classmethod
    def get_file(cls, user_id: str, file_name: str) -> Dict[str, Any]:
        """
        Get a file's content and metadata.
        
        Args:
            user_id: ID of the user
            file_name: Name of the file
            
        Returns:
            Dictionary with file content and metadata
        """
        try:
            # Ensure the bucket exists
            cls.initialize_storage()
            
            client = get_supabase_client()
            file_path = f"{user_id}/{file_name}"
            
            # Download file
            response = client.storage.from_(TEXT_FILES_BUCKET).download(file_path)
            
            # Get metadata
            file_info = client.storage.from_(TEXT_FILES_BUCKET).get_public_url(file_path)
            
            # Try to decode as text
            content = response.decode('utf-8')
            
            return {
                "file_id": file_path,
                "file_name": file_name,
                "content": content,
                "content_type": "text/plain"  # Assuming text file
            }
        except UnicodeDecodeError:
            # If cannot decode as text, it's not a valid text file
            logger.error(f"File {file_name} is not a valid text file")
            raise ValueError(f"File {file_name} is not a valid text file")
        except Exception as e:
            logger.error(f"Failed to get file: {str(e)}")
            raise
    
    @classmethod
    def delete_file(cls, user_id: str, file_name: str) -> Dict[str, Any]:
        """
        Delete a file.
        
        Args:
            user_id: ID of the user
            file_name: Name of the file
            
        Returns:
            Dictionary with deletion status
        """
        try:
            # Ensure the bucket exists
            cls.initialize_storage()
            
            client = get_supabase_client()
            file_path = f"{user_id}/{file_name}"
            
            # Delete the file
            client.storage.from_(TEXT_FILES_BUCKET).remove([file_path])
            
            return {
                "success": True,
                "file_id": file_path
            }
        except Exception as e:
            logger.error(f"Failed to delete file: {str(e)}")
            raise 