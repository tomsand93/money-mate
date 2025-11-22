"""
Expense Processor - Reads and processes credit card Excel files
"""
import pandas as pd
import os
from datetime import datetime
from typing import List, Dict, Tuple
import json


class ExpenseProcessor:
    def __init__(self, config_path: str = "config.json"):
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        self.categories = self.config['categories']

    def read_excel_file(self, file_path: str) -> pd.DataFrame:
        """
        Read credit card Excel file and return DataFrame
        Expected columns: תאריך רכישה, שם בית עסק, סכום עסקה, מטבע עסקה,
                         סכום חיוב, מטבע חיוב, מס' שובר, פירוט נוסף

        Handles Israeli credit card format where header row is not at the top
        """
        try:
            # First, read without header to find the actual header row
            df_temp = pd.read_excel(file_path, header=None)

            # Find the row that contains 'תאריך רכישה' AND 'סכום חיוב'
            header_row = None
            for idx, row in df_temp.iterrows():
                row_str = ' '.join([str(cell) for cell in row if pd.notna(cell)])
                # Look for both key columns to ensure we have the right header
                if 'תאריך רכישה' in row_str and 'סכום חיוב' in row_str:
                    header_row = idx
                    break

            if header_row is None:
                # Try just looking for סכום חיוב
                for idx, row in df_temp.iterrows():
                    if any('סכום חיוב' in str(cell) for cell in row if pd.notna(cell)):
                        header_row = idx
                        break

            if header_row is None:
                # Try default reading (header at row 0)
                df = pd.read_excel(file_path)
            else:
                # Read with the correct header row
                df = pd.read_excel(file_path, header=header_row)

            # Clean up column names (remove extra spaces, newlines)
            df.columns = [str(col).strip().replace('\n', ' ') for col in df.columns]

            # Normalize column names (handle variations like "שם בית עסק" vs "שם בית העסק")
            if 'שם בית העסק' in df.columns:
                df = df.rename(columns={'שם בית העסק': 'שם בית עסק'})

            # Verify required columns exist
            required_columns = ['תאריך רכישה', 'שם בית עסק', 'סכום חיוב']
            missing_cols = [col for col in required_columns if col not in df.columns]

            if missing_cols:
                # Show available columns to help debug
                available = list(df.columns)
                raise ValueError(f"Missing required columns: {missing_cols}\nAvailable columns: {available}")

            # Clean and prepare data
            # Israeli date format is DD.MM.YY or DD/MM/YYYY (day first!)
            df['תאריך רכישה'] = pd.to_datetime(df['תאריך רכישה'], format='%d.%m.%y', errors='coerce')
            # If that didn't work, try DD/MM/YYYY format
            if df['תאריך רכישה'].isna().sum() > len(df) * 0.5:  # If more than half failed
                df['תאריך רכישה'] = pd.to_datetime(df['תאריך רכישה'], format='%d/%m/%Y', errors='coerce')
            # If still failing, try general dayfirst parsing
            if df['תאריך רכישה'].isna().sum() > len(df) * 0.5:
                df['תאריך רכישה'] = pd.to_datetime(df['תאריך רכישה'], dayfirst=True, errors='coerce')
            df['סכום חיוב'] = pd.to_numeric(df['סכום חיוב'], errors='coerce')

            # Remove rows with invalid data
            df = df.dropna(subset=['תאריך רכישה', 'סכום חיוב'])

            return df

        except Exception as e:
            print(f"Error reading file {file_path}: {str(e)}")
            raise

    def categorize_expense(self, business_name: str) -> str:
        """
        Automatically categorize expense based on business name
        """
        if pd.isna(business_name):
            return "אחר"

        business_name_lower = str(business_name).lower()

        # Search for matching keywords in each category
        for category, keywords in self.categories.items():
            for keyword in keywords:
                if keyword.lower() in business_name_lower:
                    return category

        return "אחר"

    def process_file(self, file_path: str) -> pd.DataFrame:
        """
        Process a single Excel file and add categories
        """
        df = self.read_excel_file(file_path)

        # Extract year and month from filename (e.g., "9309_07_2025.xlsx" -> month=07, year=2025)
        filename = os.path.basename(file_path)
        import re
        # Pattern: look for MM_YYYY or similar patterns
        match = re.search(r'_(\d{2})_(\d{4})', filename)
        if match:
            file_month = int(match.group(1))
            file_year = int(match.group(2))
            # Override the date with the first day of the month from filename
            df['תאריך רכישה'] = pd.Timestamp(year=file_year, month=file_month, day=1)

        # Add category column
        df['קטגוריה'] = df['שם בית עסק'].apply(self.categorize_expense)

        # Add source file information
        df['קובץ מקור'] = os.path.basename(file_path)
        df['תאריך עיבוד'] = datetime.now()

        return df

    def process_folder(self, folder_path: str) -> List[pd.DataFrame]:
        """
        Process all Excel files in a folder
        """
        processed_dfs = []

        if not os.path.exists(folder_path):
            print(f"Folder {folder_path} does not exist")
            return processed_dfs

        for filename in os.listdir(folder_path):
            if filename.endswith(('.xlsx', '.xls')) and not filename.startswith('~'):
                file_path = os.path.join(folder_path, filename)
                print(f"Processing {filename}...")

                try:
                    df = self.process_file(file_path)
                    processed_dfs.append(df)
                    print(f"  ✓ Processed {len(df)} transactions")
                except Exception as e:
                    print(f"  ✗ Error processing {filename}: {str(e)}")

        return processed_dfs

    def get_monthly_summary(self, df: pd.DataFrame, year: int, month: int) -> Dict:
        """
        Generate summary for a specific month
        """
        # Filter by month
        mask = (df['תאריך רכישה'].dt.year == year) & (df['תאריך רכישה'].dt.month == month)
        month_df = df[mask]

        if len(month_df) == 0:
            return None

        # Calculate summary by category
        category_summary = month_df.groupby('קטגוריה')['סכום חיוב'].agg(['sum', 'count']).round(2)
        category_summary.columns = ['סכום', 'כמות עסקאות']

        summary = {
            'year': year,
            'month': month,
            'total_expenses': float(month_df['סכום חיוב'].sum()),
            'transaction_count': len(month_df),
            'by_category': category_summary.to_dict('index'),
            'top_expenses': month_df.nlargest(10, 'סכום חיוב')[
                ['תאריך רכישה', 'שם בית עסק', 'סכום חיוב', 'קטגוריה']
            ].to_dict('records')
        }

        return summary
