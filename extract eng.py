import pandas as pd
import sys


def csv_to_txt(input_csv, output_txt):
    """
    Extracts the 'Output' column from a CSV file and saves it to a text file.

    Args:
        input_csv (str): Path to the input CSV file
        output_txt (str): Path to the output text file
    """
    # Read the CSV file, including the header
    df = pd.read_csv(input_csv)

    # Print column names
    print("Columns in the CSV file:")
    print(df.columns.tolist())

    # Check if 'Output' column exists
    if 'Output' not in df.columns:
        print("Error: 'Output' column not found in the CSV file.")
        return

    # Open the output text file
    with open(output_txt, 'w', encoding='utf-8') as f:
        # Iterate through the 'Output' column
        for text in df['Output']:
            # Write each non-null entry as a new paragraph
            if pd.notna(text):
                f.write(str(text).strip() + '\n\n')

    print(f"Extraction complete. English text saved to {output_txt}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python 'extract eng.py' <input_csv> <output_txt>")
        print("Example: python 'extract eng.py' 'progress.csv' 'output.txt'")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    # Run the extraction
    csv_to_txt(input_file, output_file)