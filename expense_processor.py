"""
Expense Processor - Reads and processes credit card Excel files
"""
import pandas as pd
import os
from datetime import datetime
from typing import List, Dict, Tuple, Optional
import json
import re


class ExpenseProcessor:
    def __init__(self, config_path: str = "config.json"):
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        self.categories = self.config['categories']

        # Comprehensive column name mapping for all credit card types
        # Maps standard column names to all possible variations
        self.column_variations = {
            'purchase_date': [
                # Hebrew variations
                'תאריך רכישה', 'תאריך עסקה', 'תאריך קניה', 'תאריך', 'ת. רכישה',
                'תאריך ביצוע עסקה', 'תאריך העסקה', 'תאריך ביצוע',
                # English variations
                'purchase date', 'transaction date', 'date', 'trans date',
                'date of transaction', 'purchase dt'
            ],
            'business_name': [
                # Hebrew variations
                'שם בית עסק', 'שם בית העסק', 'בית עסק', 'שם העסק',
                'שם עסק', 'שם בית-עסק', 'בית-עסק', 'סוחר', 'שם סוחר',
                # English variations
                'business name', 'merchant', 'merchant name', 'business',
                'vendor', 'vendor name', 'payee', 'description'
            ],
            'transaction_amount': [
                # Hebrew variations
                'סכום עסקה', 'סכום במטבע עסקה', 'סכום מקורי', 'סכום במטבע זר',
                'סכום במט"ח', 'סכום במטבע חוץ', 'מטבע עסקה',
                # English variations
                'transaction amount', 'original amount', 'foreign amount',
                'amount in foreign currency', 'original currency amount'
            ],
            'transaction_currency': [
                # Hebrew variations
                'מטבע עסקה', 'מטבע', 'מט"ח', 'סוג מטבע', 'מטבע העסקה',
                # English variations
                'transaction currency', 'currency', 'curr', 'transaction curr',
                'original currency'
            ],
            'billing_amount': [
                # Hebrew variations
                'סכום חיוב', 'סכום לחיוב', 'סכום בש"ח', 'סכום בשקלים',
                'חיוב בש"ח', 'סכום', 'סה"כ', 'חיוב',
                # English variations
                'billing amount', 'charge amount', 'amount', 'total amount',
                'ils amount', 'amount in ils', 'charged amount', 'debit amount'
            ],
            'billing_currency': [
                # Hebrew variations
                'מטבע חיוב', 'מטבע לחיוב', 'מטבע החיוב',
                # English variations
                'billing currency', 'charge currency', 'billing curr'
            ],
            'voucher_number': [
                # Hebrew variations
                'מס\' שובר', 'מס׳ שובר', "מס' שובר", 'מספר שובר',
                'מס. שובר', 'שובר', 'מספר אסמכתא', 'אסמכתא', 'מס אסמכתא',
                # English variations
                'voucher number', 'voucher no', 'reference number', 'ref no',
                'transaction number', 'trans no', 'confirmation number'
            ],
            'additional_details': [
                # Hebrew variations
                'פירוט נוסף', 'פרטים נוספים', 'הערות', 'פירוט', 'מידע נוסף',
                'הסבר', 'תיאור',
                # English variations
                'additional details', 'details', 'notes', 'comments',
                'description', 'memo', 'additional info'
            ]
        }

    def _normalize_text(self, text: str) -> str:
        """Normalize text for fuzzy matching - remove spaces, punctuation, make lowercase"""
        if pd.isna(text):
            return ""
        text = str(text).strip().lower()
        # Remove common punctuation and special characters
        text = re.sub(r'[\'"\.,\-\s]+', '', text)
        return text

    def _find_column(self, df: pd.DataFrame, standard_name: str) -> Optional[str]:
        """
        Find a column in the dataframe that matches one of the variations for the standard name.
        Uses fuzzy matching to handle minor differences.

        Args:
            df: DataFrame to search in
            standard_name: Standard column name (e.g., 'purchase_date', 'billing_amount')

        Returns:
            The actual column name in the dataframe, or None if not found
        """
        if standard_name not in self.column_variations:
            return None

        variations = self.column_variations[standard_name]

        # First pass: exact match (case-insensitive)
        for col in df.columns:
            col_lower = str(col).strip().lower()
            for variation in variations:
                if col_lower == variation.lower():
                    return col

        # Second pass: fuzzy match (normalized)
        normalized_variations = {self._normalize_text(v): v for v in variations}
        for col in df.columns:
            normalized_col = self._normalize_text(col)
            if normalized_col in normalized_variations:
                return col

        # Third pass: substring match for very similar names
        for col in df.columns:
            col_normalized = self._normalize_text(col)
            for variation in variations:
                variation_normalized = self._normalize_text(variation)
                # Check if one is contained in the other
                if (variation_normalized and col_normalized and
                    (variation_normalized in col_normalized or col_normalized in variation_normalized)):
                    # Make sure it's a significant match (at least 60% of the shorter string)
                    min_len = min(len(variation_normalized), len(col_normalized))
                    max_len = max(len(variation_normalized), len(col_normalized))
                    if min_len > 0 and min_len / max_len >= 0.6:
                        return col

        return None

    def _map_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Map all columns in the dataframe to standard names.

        Returns:
            DataFrame with standardized column names
        """
        column_mapping = {}

        # Find and map each standard column
        for standard_name in self.column_variations.keys():
            found_col = self._find_column(df, standard_name)
            if found_col:
                column_mapping[found_col] = standard_name

        # Rename columns
        df_renamed = df.rename(columns=column_mapping)

        return df_renamed

    def read_excel_file(self, file_path: str) -> pd.DataFrame:
        """
        Read credit card Excel file and return DataFrame.
        Automatically detects column names from various credit card formats.

        Handles Israeli credit card format where header row is not at the top.
        """
        try:
            # First, read without header to find the actual header row
            df_temp = pd.read_excel(file_path, header=None)

            # Find the header row by looking for key billing/amount keywords
            header_row = None
            key_patterns = [
                'סכום חיוב', 'billing amount', 'חיוב', 'amount',  # Billing amount
                'תאריך רכישה', 'purchase date', 'תאריך', 'date'  # Date
            ]

            for idx, row in df_temp.iterrows():
                row_str = ' '.join([str(cell).lower() for cell in row if pd.notna(cell)])
                # Check if row contains any of the key patterns
                if any(pattern in row_str for pattern in key_patterns):
                    # Additional check: row should have multiple non-empty cells
                    non_empty = sum(1 for cell in row if pd.notna(cell) and str(cell).strip())
                    if non_empty >= 3:  # At least 3 columns
                        header_row = idx
                        break

            if header_row is None:
                # Try default reading (header at row 0)
                df = pd.read_excel(file_path)
            else:
                # Read with the correct header row
                df = pd.read_excel(file_path, header=header_row)

            # Clean up column names (remove extra spaces, newlines, tabs)
            df.columns = [str(col).strip().replace('\n', ' ').replace('\t', ' ') for col in df.columns]

            # Use the new auto-detection to map columns to standard names
            df = self._map_columns(df)

            # Verify required columns exist
            required_columns = ['purchase_date', 'billing_amount']
            missing_cols = [col for col in required_columns if col not in df.columns]

            if missing_cols:
                # Show available columns to help debug
                available = list(df.columns)
                raise ValueError(
                    f"Could not auto-detect required columns: {missing_cols}\n"
                    f"Available columns: {available}\n"
                    f"Please ensure the file contains date and amount columns."
                )

            # Add business_name if not found (use empty string)
            if 'business_name' not in df.columns:
                df['business_name'] = ''

            # Clean and prepare data
            # Israeli date format is DD.MM.YY or DD/MM/YYYY (day first!)
            df['purchase_date'] = pd.to_datetime(df['purchase_date'], format='%d.%m.%y', errors='coerce')
            # If that didn't work, try DD/MM/YYYY format
            if df['purchase_date'].isna().sum() > len(df) * 0.5:  # If more than half failed
                df['purchase_date'] = pd.to_datetime(df['purchase_date'], format='%d/%m/%Y', errors='coerce')
            # If still failing, try general dayfirst parsing
            if df['purchase_date'].isna().sum() > len(df) * 0.5:
                df['purchase_date'] = pd.to_datetime(df['purchase_date'], dayfirst=True, errors='coerce')
            # Last resort: try auto-detection
            if df['purchase_date'].isna().sum() > len(df) * 0.5:
                df['purchase_date'] = pd.to_datetime(df['purchase_date'], errors='coerce')

            # Convert billing amount to numeric
            df['billing_amount'] = pd.to_numeric(df['billing_amount'], errors='coerce')

            # Handle optional transaction_amount (foreign currency amount)
            if 'transaction_amount' in df.columns:
                df['transaction_amount'] = pd.to_numeric(df['transaction_amount'], errors='coerce')

            # Set default values for optional columns
            if 'transaction_currency' not in df.columns:
                df['transaction_currency'] = 'ILS'
            if 'billing_currency' not in df.columns:
                df['billing_currency'] = 'ILS'
            if 'voucher_number' not in df.columns:
                df['voucher_number'] = ''
            if 'additional_details' not in df.columns:
                df['additional_details'] = ''

            # Remove rows with invalid data (missing date or amount)
            original_len = len(df)
            df = df.dropna(subset=['purchase_date', 'billing_amount'])
            if len(df) < original_len:
                print(f"  Note: Removed {original_len - len(df)} rows with invalid date or amount")

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
        # Pattern: look for MM_YYYY or similar patterns
        match = re.search(r'_(\d{2})_(\d{4})', filename)
        if match:
            file_month = int(match.group(1))
            file_year = int(match.group(2))
            # Override the date with the first day of the month from filename
            df['purchase_date'] = pd.Timestamp(year=file_year, month=file_month, day=1)

        # Add category column
        df['category'] = df['business_name'].apply(self.categorize_expense)

        # Add source file information
        df['source_file'] = os.path.basename(file_path)
        df['processed_date'] = datetime.now()

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
        mask = (df['purchase_date'].dt.year == year) & (df['purchase_date'].dt.month == month)
        month_df = df[mask]

        if len(month_df) == 0:
            return None

        # Calculate summary by category
        category_summary = month_df.groupby('category')['billing_amount'].agg(['sum', 'count']).round(2)
        category_summary.columns = ['סכום', 'כמות עסקאות']

        summary = {
            'year': year,
            'month': month,
            'total_expenses': float(month_df['billing_amount'].sum()),
            'transaction_count': len(month_df),
            'by_category': category_summary.to_dict('index'),
            'top_expenses': month_df.nlargest(10, 'billing_amount')[
                ['purchase_date', 'business_name', 'billing_amount', 'category']
            ].to_dict('records')
        }

        return summary
