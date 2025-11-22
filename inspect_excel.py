"""
Inspect Excel file structure to understand column layout
"""
import sys
import pandas as pd

# Fix encoding for Windows
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

if len(sys.argv) > 1:
    filename = sys.argv[1]
else:
    filename = 'input_files/7228_09_2025.xlsx'

print(f"Inspecting: {filename}")
print("="*80)

# Try reading without header
df = pd.read_excel(filename, header=None)
print(f"\nTotal rows: {len(df)}")
print(f"Total columns: {len(df.columns)}")
print("\nFirst 15 rows:")
print("="*80)
print(df.head(15).to_string())

# Try to find header row
print("\n" + "="*80)
print("Looking for header row...")
for i in range(min(15, len(df))):
    row = df.iloc[i]
    if row.notna().sum() > 4:  # Row has more than 4 non-null values
        print(f"\nRow {i}: {row.tolist()}")
