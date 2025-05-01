"""
Admin utilities for the Large Translator API.
Use this script to perform administrative tasks like initializing storage buckets.
"""
import logging
import argparse
import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import Supabase services
from external_services.supabase.client import get_supabase_client

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Bucket name defined in storage_service.py
TEXT_FILES_BUCKET = "user-text-files"

def create_storage_bucket():
    """Create the storage bucket for user files."""
    try:
        logger.info(f"Creating storage bucket '{TEXT_FILES_BUCKET}'...")
        client = get_supabase_client()
        
        # Check if bucket already exists
        try:
            buckets = client.storage.list_buckets()
            bucket_names = [bucket['name'] for bucket in buckets]
            
            if TEXT_FILES_BUCKET in bucket_names:
                logger.info(f"Bucket '{TEXT_FILES_BUCKET}' already exists.")
                return
        except Exception as e:
            logger.error(f"Error checking buckets: {str(e)}")
        
        # Create the bucket with the required format
        response = client.storage.create_bucket({
            'name': TEXT_FILES_BUCKET,
            'id': TEXT_FILES_BUCKET,
            'public': False
        })
        
        logger.info(f"Storage bucket '{TEXT_FILES_BUCKET}' created successfully!")
        logger.info(f"Response: {response}")
        
    except Exception as e:
        logger.error(f"Failed to create storage bucket: {str(e)}")
        raise

def main():
    """Run admin tasks based on command line arguments."""
    parser = argparse.ArgumentParser(description='Admin utilities for Large Translator API')
    parser.add_argument('--create-bucket', action='store_true', help='Create storage bucket for user files')
    
    args = parser.parse_args()
    
    if args.create_bucket:
        create_storage_bucket()
    else:
        parser.print_help()

if __name__ == '__main__':
    main() 