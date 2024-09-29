import pandas as pd
import chardet

# Detect the file encoding
with open('Arukh HaShulchan -even ezer_progress.csv', 'rb') as file:
    raw_data = file.read()
    result = chardet.detect(raw_data)
    encoding = result['encoding']

# Read the first few rows to get an idea of the structure
df = pd.read_csv('Arukh HaShulchan -even ezer_progress.csv', nrows=5, encoding=encoding)

# Display basic information about the DataFrame
print(df.info())

# Show the first few rows
print(df.head())