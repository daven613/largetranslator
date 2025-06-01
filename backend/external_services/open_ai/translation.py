"""
OpenAI translation functionality.

This module provides functions for translating text using the OpenAI API.
"""

import asyncio
import logging
import os
from typing import Optional

from openai import OpenAI

# Setup logging
logger = logging.getLogger(__name__)

# Initialize OpenAI client function
def get_client():
    """Get OpenAI client with API key."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.error("OPENAI_API_KEY environment variable not found.")
        raise ValueError("OPENAI_API_KEY not set in environment")
    # Log a portion of the key for verification, but not the whole thing
    logger.info(f"OpenAI client initialized with API key starting with: {api_key[:5]}... and ending with: ...{api_key[-4:]}")
    return OpenAI(api_key=api_key)

async def translate_text(
    text: str, 
    target_language: str, 
    model: str = "gpt-4"
) -> str:
    """
    Translate text using OpenAI API.
    
    Args:
        text: Text to translate
        target_language: Target language code or name
        model: OpenAI model to use (default: gpt-4)
        
    Returns:
        Translated text
    """
    try:
        # Initialize client inside function
        client = get_client()
        
        # Prepare the prompt
        prompt = f"Translate the following text to {target_language}. Preserve formatting and maintain the original meaning as accurately as possible:\n\n{text}"
        
        logger.info(f"Attempting to translate text to {target_language} using model {model}. Text length: {len(text)}")
        
        # CRITICAL FIX: Run the synchronous OpenAI call in a thread pool to prevent blocking the event loop
        def _sync_call():
            return client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a professional translator."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # Lower temperature for more consistent translations
            )
        
        # Run in thread pool to avoid blocking the async event loop
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, _sync_call)
        
        translation = response.choices[0].message.content.strip()
        logger.info(f"Successfully received translation from OpenAI. Translated text length: {len(translation)}")
        return translation
        
    except Exception as e:
        logger.error(f"Error during OpenAI API call or processing: {str(e)}", exc_info=True)
        # Re-raise the exception so it can be handled by the calling function
        # which might want to set a 'failed' status on the translation job.
        raise

async def translate_text_with_prompt(
    prompt: str, 
    model: str = "gpt-4"
) -> str:
    """
    Translate text using OpenAI API with a custom prompt.
    
    Args:
        prompt: Complete prompt including instructions and text to translate
        model: OpenAI model to use (default: gpt-4)
        
    Returns:
        Translated text
    """
    try:
        # Initialize client inside function
        client = get_client()
        
        logger.info(f"Attempting translation with custom prompt using model {model}. Prompt length: {len(prompt)}")
        
        # CRITICAL FIX: Run the synchronous OpenAI call in a thread pool to prevent blocking the event loop
        def _sync_call():
            return client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a professional translator. Follow the user's instructions carefully."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # Lower temperature for more consistent translations
            )
        
        # Run in thread pool to avoid blocking the async event loop
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, _sync_call)
        
        translation = response.choices[0].message.content.strip()
        logger.info(f"Successfully received translation from OpenAI. Translated text length: {len(translation)}")
        return translation
        
    except Exception as e:
        logger.error(f"Error during OpenAI API call or processing: {str(e)}", exc_info=True)
        # Re-raise the exception so it can be handled by the calling function
        # which might want to set a 'failed' status on the translation job.
        raise