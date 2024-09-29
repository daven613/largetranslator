import pandas as pd


def csv_to_txt(input_csv, output_txt):
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


# File paths
input_file = 'Arukh HaShulchan -even ezer_progress.csv'
output_file = 'english_output.txt'

# Run the extraction
csv_to_txt(input_file, output_file)