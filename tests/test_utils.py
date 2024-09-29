# tests/test_text_splitter.py

import unittest
from utils import iterative_text_splitter

class TestIterativeTextSplitter(unittest.TestCase):

    def test_example_sentence(self):
        text = "This is a test sentence.\n\nHere is another sentence.\nThis is yet another sentence."
        max_size = 50
        separators = ['\n\n', '\n', '.', ',', ' ']
        expected = ['This is a test sentence.\n\n', 'Here is another sentence.\n', 'This is yet another sentence.']
        self.assertEqual(iterative_text_splitter(text, max_size, separators), expected)

    def test_short_sentences(self):
        text = "Short sentence. Another short one."
        max_size = 20
        separators = ['.', ' ']
        expected = ['Short sentence.', ' Another short one.']
        self.assertEqual(iterative_text_splitter(text, max_size, separators), expected)

    def test_comma_separated(self):
        text = "One, two, three, four."
        max_size = 10
        separators = [', ', ' ']
        expected = ['One, two, ', 'three, ', 'four.']
        self.assertEqual(iterative_text_splitter(text, max_size, separators), expected)

    def test_no_separators_match(self):
        text = "No separators match"
        max_size = 5
        separators = ['.', ',']
        expected = ['No se', 'parat', 'ors m', 'atch']
        self.assertEqual(iterative_text_splitter(text, max_size, separators), expected)

    def test_empty_text(self):
        text = ""
        max_size = 5
        separators = ['\n', ' ', '.']
        expected = ['']
        self.assertEqual(iterative_text_splitter(text, max_size, separators), expected)


# Allows the test to be run directly from this script
if __name__ == '__main__':
    unittest.main()
