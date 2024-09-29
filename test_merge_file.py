from unittest.mock import patch
import streamlit as st
import openai
import pandas as pd

# Generated by CodiumAI

from utils import merge_file
import main
import unittest

class TestMergeFile(unittest.TestCase):

    #  should concatenate all chunks into a single string
    def test_concatenate_chunks(self):
        # Arrange
        chunks = ['Hello', ' ', 'World!']
    
        # Act
        result = merge_file(chunks)
    
        # Assert
        self.assertEqual(result, 'Hello World!')

    #  should handle very large chunks
    def test_large_chunks(self):
        # Arrange
        chunks = ['a' * 10**6] * 10**3
    
        # Act
        result = merge_file(chunks)
    
        # Assert
        self.assertEqual(result, 'a' * 10**9)

