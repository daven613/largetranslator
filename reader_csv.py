import pandas as pd
import chardet
import sys


def read_csv_with_encoding(filepath, nrows=5):
    """
    Detects file encoding and reads CSV file with proper encoding.

    Args:
        filepath (str): Path to the CSV file
        nrows (int): Number of rows to preview (default: 5)
    """
    # Detect the file encoding
    with open(filepath, 'rb') as file:
        raw_data = file.read()
        result = chardet.detect(raw_data)
        encoding = result['encoding']

    print(f"Detected encoding: {encoding}")

    # Read the first few rows to get an idea of the structure
    df = pd.read_csv(filepath, nrows=nrows, encoding=encoding)

    # Display basic information about the DataFrame
    print(df.info())

    # Show the first few rows
    print(df.head())


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python reader_csv.py <csv_file> [nrows]")
        print("Example: python reader_csv.py 'Arukh HaShulchan -even ezer_progress.csv' 5")
        sys.exit(1)

    filepath = sys.argv[1]
    nrows = int(sys.argv[2]) if len(sys.argv) > 2 else 5

    read_csv_with_encoding(filepath, nrows)