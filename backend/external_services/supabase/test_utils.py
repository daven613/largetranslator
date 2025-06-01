"""
Test utilities for Supabase.
Provides mock clients and credentials for testing.
"""
import os
import logging
from unittest.mock import MagicMock, patch
from typing import Dict, Any, List
from supabase import Client

logger = logging.getLogger(__name__)

# Mock Supabase credentials
MOCK_SUPABASE_URL = "https://example-test-project.supabase.co"
MOCK_SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.mock-key-for-testing"

class MockSupabaseFixture:
    """Fixture for setting up mock Supabase environment"""
    
    @staticmethod
    def setup_env():
        """Set up environment variables for testing"""
        os.environ["SUPABASE_URL"] = MOCK_SUPABASE_URL
        os.environ["SUPABASE_KEY"] = MOCK_SUPABASE_KEY
        logger.info("Mock Supabase environment set up with test credentials")
    
    @staticmethod
    def create_mock_client():
        """Create a mock Supabase client with pre-configured responses"""
        mock_client = MagicMock(spec=Client)
        
        # Create a class for the mock execute response
        class MockExecuteResponse:
            def __init__(self, data=None):
                self.data = data or []
        
        # Set up the mock chain for tables
        mock_table = MagicMock()
        mock_client.table.return_value = mock_table
        
        # Create mock responses for chained methods
        mock_select = MagicMock()
        mock_insert = MagicMock()
        mock_update = MagicMock()
        mock_delete = MagicMock()
        
        mock_table.select.return_value = mock_select
        mock_table.insert.return_value = mock_insert
        mock_table.update.return_value = mock_update
        mock_table.delete.return_value = mock_delete
        
        # Create mocks for the filter operations
        mock_eq = MagicMock()
        mock_filter = MagicMock()
        mock_order = MagicMock()
        
        # Configure the chain methods
        for mock_obj in [mock_select, mock_insert, mock_update, mock_delete]:
            mock_obj.eq.return_value = mock_eq
            mock_obj.filter.return_value = mock_filter
            mock_obj.order.return_value = mock_order
            mock_obj.execute.return_value = MockExecuteResponse()
        
        for mock_obj in [mock_eq, mock_filter, mock_order]:
            mock_obj.eq.return_value = mock_eq
            mock_obj.filter.return_value = mock_filter
            mock_obj.order.return_value = mock_order
            mock_obj.execute.return_value = MockExecuteResponse()
        
        # Mock storage
        mock_storage = MagicMock()
        mock_client.storage = mock_storage
        mock_bucket = MagicMock()
        mock_storage.from_.return_value = mock_bucket
        
        # Mock auth
        mock_auth = MagicMock()
        mock_client.auth = mock_auth

        # Configure the execute result based on the table being accessed
        def configure_mock_data(table_name: str, data: List[Dict[str, Any]]):
            """Configure mock data for a specific table"""
            # Create a mock execute function that returns the specified data
            def mock_execute(*args, **kwargs):
                return MockExecuteResponse(data)
            
            # Set up a dynamic side effect for the table method
            def table_side_effect(name):
                if name == table_name:
                    # For this specific table, set up the execute methods to return our data
                    mock_table_obj = MagicMock()
                    
                    # Set up chain methods
                    mock_table_select = MagicMock()
                    mock_table_insert = MagicMock()
                    mock_table_update = MagicMock()
                    mock_table_delete = MagicMock()
                    
                    mock_table_obj.select.return_value = mock_table_select
                    mock_table_obj.insert.return_value = mock_table_insert
                    mock_table_obj.update.return_value = mock_table_update
                    mock_table_obj.delete.return_value = mock_table_delete
                    
                    # Set up filter methods
                    mock_table_eq = MagicMock()
                    mock_table_filter = MagicMock()
                    mock_table_order = MagicMock()
                    
                    # Configure the chain methods
                    for mock_obj in [mock_table_select, mock_table_insert, mock_table_update, mock_table_delete]:
                        mock_obj.eq.return_value = mock_table_eq
                        mock_obj.filter.return_value = mock_table_filter
                        mock_obj.order.return_value = mock_table_order
                        mock_obj.execute.return_value = MockExecuteResponse(data)
                    
                    for mock_obj in [mock_table_eq, mock_table_filter, mock_table_order]:
                        mock_obj.eq.return_value = mock_table_eq
                        mock_obj.filter.return_value = mock_table_filter
                        mock_obj.order.return_value = mock_table_order
                        mock_obj.execute.return_value = MockExecuteResponse(data)
                    
                    return mock_table_obj
                else:
                    # For other tables, return the default mock
                    return mock_table
            
            # Set the side effect on the table method
            mock_client.table.side_effect = table_side_effect
        
        # Add helper method to the mock client to easily configure data
        mock_client.configure_mock_data = configure_mock_data
        
        return mock_client

def patch_supabase_client(mock_data: Dict[str, List[Dict[str, Any]]] = None):
    """
    Patch the Supabase client for testing with optional mock data.
    
    Args:
        mock_data: Dictionary mapping table names to lists of record dictionaries
                  Example: {"documents": [{"id": "123", "name": "Test"}]}
    """
    # Set up environment variables
    MockSupabaseFixture.setup_env()
    
    # Create mock client
    mock_client = MockSupabaseFixture.create_mock_client()
    
    # Configure mock data if provided
    if mock_data:
        for table_name, data in mock_data.items():
            mock_client.configure_mock_data(table_name, data)
    
    # Apply patches
    client_patcher = patch('backend.external_services.supabase.client._supabase_client', mock_client)
    init_patcher = patch('backend.external_services.supabase.client.initialize_supabase', return_value=mock_client)
    get_client_patcher = patch('backend.external_services.supabase.client.get_supabase_client', return_value=mock_client)
    
    # Start patches
    client_patcher.start()
    init_patcher.start()
    get_client_patcher.start()
    
    return mock_client 