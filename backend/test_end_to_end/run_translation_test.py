#!/usr/bin/env python3
"""
Simple runner for the translation E2E test.
Usage: python run_translation_test.py
"""
import asyncio
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from test_translation_e2e_live import run_test_with_token

async def main():
    print("🧪 Translation E2E Test Runner")
    print("=" * 50)
    
    # Get token from user
    token = input("Enter your auth token: ").strip()
    if not token:
        print("❌ No token provided!")
        return
    
    # Get prompt from user (optional)
    prompt = input("Enter translation prompt (or press Enter for default): ").strip()
    if not prompt:
        prompt = "Translate this text to Spanish"
    
    print(f"\n🚀 Starting test with prompt: '{prompt}'")
    print("=" * 50)
    
    try:
        await run_test_with_token(token, prompt)
        print("\n🎉 Test completed successfully!")
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 