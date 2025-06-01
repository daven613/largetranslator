"""
Tests for the JSON utilities module.
"""
import unittest
import uuid
from .json_utils import convert_uuids_to_str, Config

class TestJsonUtils(unittest.TestCase):
    """Test cases for the JSON utilities module."""
    
    def test_convert_uuids_to_str(self):
        """Test that UUIDs are properly converted to strings."""
        # Create test UUIDs
        test_uuid1 = uuid.uuid4()
        test_uuid2 = uuid.uuid4()
        
        # Test single UUID
        result = convert_uuids_to_str(test_uuid1)
        self.assertEqual(result, str(test_uuid1))
        
        # Test dictionary with UUID values
        test_dict = {
            "id": test_uuid1,
            "name": "Test Document",
            "metadata": {
                "related_id": test_uuid2
            }
        }
        result = convert_uuids_to_str(test_dict)
        
        self.assertEqual(result["id"], str(test_uuid1))
        self.assertEqual(result["metadata"]["related_id"], str(test_uuid2))
        
        # Test list with UUID values
        test_list = [test_uuid1, "string item", {"id": test_uuid2}]
        result = convert_uuids_to_str(test_list)
        
        self.assertEqual(result[0], str(test_uuid1))
        self.assertEqual(result[2]["id"], str(test_uuid2))
        
        # Test tuple with UUID values
        test_tuple = (test_uuid1, "string item")
        result = convert_uuids_to_str(test_tuple)
        
        self.assertEqual(result[0], str(test_uuid1))
        
    def test_config_class(self):
        """Test that the Config class has the right UUID encoder."""
        self.assertIn(uuid.UUID, Config.json_encoders)
        encoder_func = Config.json_encoders[uuid.UUID]
        
        test_uuid = uuid.uuid4()
        self.assertEqual(encoder_func(test_uuid), str(test_uuid))
        
if __name__ == "__main__":
    unittest.main() 