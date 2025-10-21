# Large Translator

A Streamlit web application for translating Hebrew Halachic texts using OpenAI's GPT-4 API.

## Features

- Upload and process large text files
- Intelligent text chunking with hierarchical separators
- Progress tracking with pause/resume functionality
- Error handling and retry mechanism
- Automatic encoding detection
- CSV output with input/output/error columns

## Setup

1. **Install requirements**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up API key**
   - Copy `.env.example` to `.env` (or set environment variable)
   - Add your OpenAI API key:
     ```bash
     export OPENAI_API_KEY="your-api-key-here"
     ```

3. **Start the app**
   ```bash
   streamlit run main.py
   ```

## Utility Scripts

### Extract English Output
Extract translated text from CSV to TXT:
```bash
python "extract eng.py" <input_csv> <output_txt>
```

### CSV Reader
Preview CSV files with automatic encoding detection:
```bash
python reader_csv.py <csv_file> [nrows]
```

## Testing

Run tests using unittest:
```bash
python -m unittest discover -s tests -v
python -m unittest test_merge_file -v
```
