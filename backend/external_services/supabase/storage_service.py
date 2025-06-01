"""
Supabase Storage service for file operations.
"""
import io
import logging
import os
from typing import Dict, List, Any, BinaryIO, Optional
from datetime import datetime
import mimetypes
from .client import get_supabase_client, get_user_supabase_client

logger = logging.getLogger(__name__)

# Bucket name for user text files
TEXT_FILES_BUCKET = "user-text-files"

class SupabaseStorageService:
    """Service for interacting with Supabase Storage"""
    
    @classmethod
    def initialize_storage(cls, user_token: Optional[str] = None) -> None:
        """
        Initialize storage by checking that the bucket exists.
        
        Args:
            user_token: Optional JWT token for user-specific context
        """
        try:
            # Use user-specific client if token provided, otherwise use global client
            if user_token:
                client = get_user_supabase_client(user_token)
            else:
                client = get_supabase_client()
            
            # Check if we can access the bucket directly
            try:
                client.storage.from_(TEXT_FILES_BUCKET).list()
                logger.info(f"Successfully accessed bucket '{TEXT_FILES_BUCKET}'")
            except Exception as e:
                logger.error(f"Error accessing bucket: {str(e)}")
                logger.error(f"The bucket '{TEXT_FILES_BUCKET}' might not exist yet.")
                raise Exception(f"Bucket '{TEXT_FILES_BUCKET}' is not accessible. Please check your Supabase storage.")
                
        except Exception as e:
            logger.error(f"Failed to initialize storage: {str(e)}")
            raise
    
    @classmethod
    def upload_file(cls, user_id: str, file_name: str, file_content: bytes, content_type: str = None, user_token: Optional[str] = None) -> Dict[str, Any]:
        """
        Upload a file to Supabase storage.
        
        Args:
            user_id: ID of the user uploading the file
            file_name: Name of the file
            file_content: Binary content of the file
            content_type: MIME type of the file
            user_token: Optional JWT token for user-specific context
            
        Returns:
            Dictionary with metadata of the uploaded file
        """
        try:
            # Log the inputs for debugging
            logger.info(f"storage_service.upload_file called with:")
            logger.info(f"  user_id: {user_id}")
            logger.info(f"  file_name: {file_name}")
            logger.info(f"  content_type: {content_type}")
            logger.info(f"  user_token provided: {'Yes' if user_token else 'No'}")
            if user_token:
                logger.info(f"  user_token length: {len(user_token)}")
            
            # Create the client once and reuse it for both operations
            if user_token:
                client = get_user_supabase_client(user_token)
            else:
                client = get_supabase_client()
            
            # Check bucket access with the same client we'll use for upload
            try:
                client.storage.from_(TEXT_FILES_BUCKET).list()
                logger.info(f"Successfully accessed bucket '{TEXT_FILES_BUCKET}' with upload client")
            except Exception as e:
                logger.error(f"Error accessing bucket with upload client: {str(e)}")
                raise Exception(f"Bucket '{TEXT_FILES_BUCKET}' is not accessible. Please check your Supabase storage.")
            
            # Generate a path that includes the user ID to separate files by user
            file_path = f"{user_id}/{file_name}"
            logger.info(f"  Generated file_path: {file_path}")
            
            # If content type is not provided, try to guess it
            if not content_type:
                content_type, _ = mimetypes.guess_type(file_name)
                if not content_type:
                    content_type = "text/plain"  # Default to text/plain
            
            # Upload the file using the same client we used for bucket access
            logger.info(f"Attempting upload with same client instance...")
            result = client.storage.from_(TEXT_FILES_BUCKET).upload(
                path=file_path,
                file=file_content, 
                file_options={"content-type": content_type, "x-upsert": "true"}
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
    def get_file_metadata(cls, user_id: str, file_name: str) -> Dict[str, Any]:
        """
        Get a file's metadata without downloading its content.
        
        Args:
            user_id: ID of the user
            file_name: Name of the file
            
        Returns:
            Dictionary with file metadata
        """
        try:
            # Ensure the bucket exists
            cls.initialize_storage()
            
            client = get_supabase_client()
            file_path = f"{user_id}/{file_name}"
            
            # List files in the user's directory to find this specific file
            files = client.storage.from_(TEXT_FILES_BUCKET).list(user_id)
            
            # Find the specific file
            file_info = None
            for file in files:
                if file['name'] == file_name:
                    file_info = file
                    break
            
            if not file_info:
                raise ValueError(f"File {file_name} not found")
            
            # Get public URL
            file_url = client.storage.from_(TEXT_FILES_BUCKET).get_public_url(file_path)
            
            return {
                "file_id": file_path,
                "file_name": file_name,
                "file_size": file_info.get("metadata", {}).get("size", 0),
                "content_type": file_info.get("metadata", {}).get("mimetype", "text/plain"),
                "created_at": file_info.get("created_at", datetime.now().isoformat()),
                "url": file_url
            }
        except Exception as e:
            logger.error(f"Failed to get file metadata: {str(e)}")
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
    def download_file(cls, storage_path: str, local_path: str, user_id: str) -> None:
        """
        Download a file from storage to a local path.
        
        Args:
            storage_path: Path in storage (e.g., "translations/123/file.txt")
            local_path: Local file path to save to
            user_id: User ID for access control
        """
        try:
            # Ensure the bucket exists
            cls.initialize_storage()
            
            client = get_supabase_client()
            
            # Download file content
            response = client.storage.from_(TEXT_FILES_BUCKET).download(storage_path)
            
            # Write to local file
            with open(local_path, 'wb') as f:
                f.write(response)
                
        except Exception as e:
            logger.error(f"Failed to download file: {str(e)}")
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