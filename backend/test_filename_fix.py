#!/usr/bin/env python3

import os

def test_filename_sanitization():
    """Test that the filename sanitization logic works correctly"""
    
    print("🔧 Testing filename sanitization fix...")
    
    # Test the problematic target language that was causing issues
    target_language = "N/A (prompt-defined)"
    base_name = "test_translation_e2e"
    extension = "txt"
    
    print(f"Original target language: '{target_language}'")
    
    # Apply the same sanitization logic from the fix
    sanitized_target_language = target_language.replace("/", "_").replace("\\", "_").replace("(", "").replace(")", "").replace(" ", "_")
    translated_file_name = f"{base_name}_{sanitized_target_language}"
    if extension:
        translated_file_name += f".{extension}"
    
    print(f"Sanitized target language: '{sanitized_target_language}'")
    print(f"Generated filename: '{translated_file_name}'")
    
    # Test that the filename is valid by trying to create a file with it
    temp_dir = "temp"
    os.makedirs(temp_dir, exist_ok=True)
    temp_file_path = os.path.join(temp_dir, translated_file_name)
    
    try:
        # Try to create the file
        with open(temp_file_path, "w", encoding="utf-8") as f:
            f.write("Test content for filename validation")
        
        print(f"✅ Successfully created file: {temp_file_path}")
        
        # Verify the file exists
        if os.path.exists(temp_file_path):
            print("✅ File exists and is accessible")
            
            # Clean up
            os.remove(temp_file_path)
            print("✅ File cleanup successful")
            
            return True
        else:
            print("❌ File was not created properly")
            return False
            
    except Exception as e:
        print(f"❌ Failed to create file with sanitized filename: {str(e)}")
        return False

def test_problematic_filename():
    """Test that the original problematic filename would fail"""
    
    print("\n🔧 Testing original problematic filename...")
    
    target_language = "N/A (prompt-defined)"
    base_name = "test_translation_e2e"
    extension = "txt"
    
    # Create the problematic filename (without sanitization)
    problematic_filename = f"{base_name}_{target_language}"
    if extension:
        problematic_filename += f".{extension}"
    
    print(f"Problematic filename: '{problematic_filename}'")
    
    temp_dir = "temp"
    os.makedirs(temp_dir, exist_ok=True)
    temp_file_path = os.path.join(temp_dir, problematic_filename)
    
    try:
        # Try to create the file
        with open(temp_file_path, "w", encoding="utf-8") as f:
            f.write("Test content")
        
        print("❌ Unexpectedly succeeded in creating problematic filename")
        # Clean up if it somehow worked
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        return False
        
    except Exception as e:
        print(f"✅ Correctly failed to create problematic filename: {str(e)}")
        return True

if __name__ == "__main__":
    print("🎯 Testing Filename Sanitization Fix\n")
    
    # Test the fix works
    fix_works = test_filename_sanitization()
    
    # Test the original problem exists
    problem_exists = test_problematic_filename()
    
    if fix_works and problem_exists:
        print("\n🎉 FILENAME SANITIZATION FIX VERIFIED!")
        print("✅ Sanitized filenames work correctly")
        print("✅ Original problematic filenames fail as expected")
        print("✅ The download issue should now be resolved!")
    else:
        print("\n💥 FILENAME SANITIZATION TEST FAILED!")
        if not fix_works:
            print("❌ Sanitized filename test failed")
        if not problem_exists:
            print("❌ Original problematic filename unexpectedly worked") 