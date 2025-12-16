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

            # Find the header row by looking for transaction table headers
            header_row = None

            # Key patterns that indicate a header row (not summary/metadata)
            header_indicators = [
                ('תאריך', 'date'),          # Date column
                ('שם', 'name', 'merchant'), # Business name column
                ('סכום', 'amount'),         # Amount column
                ('עסק', 'business'),        # Business keyword
            ]

            # Patterns that indicate this is NOT a header row (summary/metadata)
            exclusion_patterns = [
                '₪',           # Currency symbol in header is usually metadata
                'מסגרת',       # Credit limit
                'נותר',        # Remaining credit
                'יתרה',        # Balance
                'סה"כ',        # Total (when alone, indicates summary row)
                'סיכום',       # Summary
            ]

            # Find ALL potential header rows, then pick the best one
            potential_headers = []

            for idx, row in df_temp.iterrows():
                # Skip rows with very few non-empty cells
                non_empty = [cell for cell in row if pd.notna(cell) and str(cell).strip()]
                if len(non_empty) < 3:
                    continue

                row_str = ' '.join([str(cell).lower() for cell in non_empty])

                # Skip rows that look like summary/metadata
                is_excluded = False
                for excl in exclusion_patterns:
                    if excl.lower() in row_str:
                        # But allow if it's part of actual column names like "סכום חיוב"
                        if not any(indicator in row_str for indicators in header_indicators for indicator in indicators):
                            is_excluded = True
                            break

                if is_excluded:
                    continue

                # Check if row contains header-like keywords
                matches = 0
                for indicators in header_indicators:
                    if any(indicator in row_str for indicator in indicators):
                        matches += 1

                # Need at least 2 header indicators (e.g., "תאריך" AND "סכום")
                if matches >= 2:
                    # Count how many cells are non-empty (more = better header)
                    score = len(non_empty) + matches * 10  # Prioritize more matches
                    potential_headers.append((idx, score, non_empty))

            # Pick the best header (highest score = most complete)
            if potential_headers:
                potential_headers.sort(key=lambda x: x[1], reverse=True)
                header_row = potential_headers[0][0]

                # BUGFIX: The header detection sometimes picks the wrong row (like row 45 or 55)
                # Prefer earlier rows if they have a good score (within first 15 rows)
                # This fixes issues with credit card statements that have multiple sections
                for idx, score, cells in potential_headers:
                    if idx < 15 and score >= 20:  # Early row with decent score
                        header_row = idx
                        break

            if header_row is None:
                # Try default reading (header at row 0)
                print(f"  Warning: No header row detected, using row 0")
                df = pd.read_excel(file_path)
            else:
                # Read with the correct header row
                print(f"  Info: Using header row {header_row}")
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

            # Remove duplicate header rows that sometimes appear in the middle of data
            # These rows have header text like "תאריך רכישה" or "purchase date" in the date column
            header_keywords = ['תאריך', '\\bdate\\b', 'שם בית', 'business name', 'merchant']
            if 'purchase_date' in df.columns:
                # Before date parsing, check for rows with header-like text
                date_col_str = df['purchase_date'].astype(str).str.lower()
                is_not_header = ~date_col_str.str.contains('|'.join(header_keywords), na=False, regex=True)
                rows_before = len(df)
                removed_rows = df[~is_not_header]
                if len(removed_rows) > 0:
                    with open('expense_filter_log.txt', 'w', encoding='utf-8') as log:
                        log.write(f"Removing {len(removed_rows)} duplicate header rows:\n")
                        for idx in removed_rows.index:
                            log.write(f"  Row {idx}: {df.loc[idx, 'purchase_date']}\n")
                    print(f"  Note: Removed {len(removed_rows)} duplicate header rows (see expense_filter_log.txt)")
                df = df[is_not_header]

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
                print(f"  Note: Removed {original_len - len(df)} rows with invalid/missing date or amount")

            return df

        except Exception as e:
            print(f"Error reading file {file_path}: {str(e)}")
            raise

    def categorize_expense(self, business_name: str) -> dict:
        """
        Automatically categorize expense based on business name with confidence scoring.

        Returns dict with:
        - category: str
        - confidence: str (high/medium/low/uncertain)
        - confidence_score: float (0.0-1.0)
        - matched_keywords: list
        """
        if pd.isna(business_name) or str(business_name).strip() == "":
            return {
                'category': "אחר",
                'confidence': 'uncertain',
                'confidence_score': 0.0,
                'matched_keywords': []
            }

        business_name_lower = str(business_name).lower().strip()

        # Track all matches with confidence scores
        matches = []

        for category, keywords in self.categories.items():
            matched_kw = []
            for keyword in keywords:
                if keyword.lower() in business_name_lower:
                    matched_kw.append(keyword)

            if matched_kw:
                # Calculate confidence based on keyword coverage
                max_keyword_len = max(len(kw) for kw in matched_kw)
                business_len = len(business_name_lower)

                # Base confidence from keyword coverage
                coverage = max_keyword_len / business_len if business_len > 0 else 0

                # Bonus for exact match
                if any(kw.lower() == business_name_lower for kw in matched_kw):
                    coverage = min(1.0, coverage * 1.5)

                # Bonus for multiple keyword matches (balanced mode)
                if len(matched_kw) > 1:
                    coverage = min(1.0, coverage * 1.2)

                matches.append((category, matched_kw, coverage))

        # No matches found
        if not matches:
            return {
                'category': "אחר",
                'confidence': 'uncertain',
                'confidence_score': 0.0,
                'matched_keywords': []
            }

        # Sort by confidence, pick best
        matches.sort(key=lambda x: x[2], reverse=True)
        best_category, best_keywords, best_score = matches[0]

        # Determine confidence level (balanced mode thresholds)
        if best_score >= 0.8:
            conf_level = 'high'
        elif best_score >= 0.5:
            conf_level = 'medium'
        elif best_score >= 0.3:
            conf_level = 'low'
        else:
            conf_level = 'uncertain'

        # Check for ambiguity
        if len(matches) > 1:
            second_best_score = matches[1][2]
            if abs(best_score - second_best_score) < 0.15:
                # Ambiguous - downgrade confidence
                if conf_level == 'high':
                    conf_level = 'medium'
                elif conf_level == 'medium':
                    conf_level = 'low'

        return {
            'category': best_category,
            'confidence': conf_level,
            'confidence_score': round(best_score, 3),
            'matched_keywords': best_keywords
        }

    def _detect_installment(self, text: str) -> tuple:
        """
        Detect installment pattern in text and extract payment number and total.

        Patterns: "תשלום 8 מתוך 12", "8/12", "payment 8 of 12", "8 out of 12"

        Returns:
            (payment_number, total_payments) or (None, None) if not detected
        """
        if pd.isna(text):
            return (None, None)

        text_str = str(text).strip()

        # Pattern 1: תשלום X מתוך Y
        pattern1 = r'תשלום\s*(\d+)\s*מתוך\s*(\d+)'
        match = re.search(pattern1, text_str)
        if match:
            return (int(match.group(1)), int(match.group(2)))

        # Pattern 2: X/Y format
        pattern2 = r'\b(\d+)/(\d+)\b'
        match = re.search(pattern2, text_str)
        if match:
            payment = int(match.group(1))
            total = int(match.group(2))
            # Sanity check: installments are usually 2-60 payments
            if 2 <= total <= 60 and 1 <= payment <= total:
                return (payment, total)

        # Pattern 3: "payment X of Y" or "X out of Y"
        pattern3 = r'(?:payment|installment)\s*(\d+)\s*(?:of|out of)\s*(\d+)'
        match = re.search(pattern3, text_str, re.IGNORECASE)
        if match:
            return (int(match.group(1)), int(match.group(2)))

        return (None, None)

    def _adjust_installment_date(self, original_date: pd.Timestamp, payment_num: int) -> pd.Timestamp:
        """
        Calculate the correct month for an installment payment.

        Args:
            original_date: The date shown in the transaction (original purchase date)
            payment_num: Which payment this is (e.g., 8 for "payment 8 of 12")

        Returns:
            Adjusted date for this installment
        """
        # Payment 1 is in the original month
        # Payment 2 is 1 month later
        # Payment N is (N-1) months later
        months_to_add = payment_num - 1

        # Add months to the original date
        new_month = original_date.month + months_to_add
        new_year = original_date.year

        # Handle year overflow
        while new_month > 12:
            new_month -= 12
            new_year += 1

        # Keep the same day, but adjust if day doesn't exist in new month
        try:
            adjusted_date = original_date.replace(year=new_year, month=new_month)
        except ValueError:
            # Day doesn't exist in new month (e.g., Jan 31 -> Feb 31)
            # Use last day of new month instead
            import calendar
            last_day = calendar.monthrange(new_year, new_month)[1]
            adjusted_date = original_date.replace(year=new_year, month=new_month, day=last_day)

        return adjusted_date

    def process_file(self, file_path: str) -> pd.DataFrame:
        """
        Process a single Excel file and add categories with confidence scoring
        """
        df = self.read_excel_file(file_path)

        # IMPORTANT: Use the actual purchase dates from the file!
        # The dates in the Excel file are the correct transaction dates
        # Do NOT override them with the filename month

        # INSTALLMENT HANDLING: Detect and adjust dates for installment transactions
        # Check both business_name and additional_details for installment patterns
        installment_adjusted = 0
        for idx in df.index:
            # Check for installment pattern in business name or additional details
            business_name = df.at[idx, 'business_name'] if 'business_name' in df.columns else ''
            additional = df.at[idx, 'additional_details'] if 'additional_details' in df.columns else ''

            # Try to detect installment in either field
            payment_num, total_payments = self._detect_installment(business_name)
            if payment_num is None:
                payment_num, total_payments = self._detect_installment(additional)

            # If installment detected, adjust the date
            if payment_num is not None and total_payments is not None:
                original_date = df.at[idx, 'purchase_date']
                adjusted_date = self._adjust_installment_date(original_date, payment_num)
                df.at[idx, 'purchase_date'] = adjusted_date

                # Store installment info for reference
                df.at[idx, 'is_installment'] = True
                df.at[idx, 'installment_number'] = payment_num
                df.at[idx, 'total_installments'] = total_payments

                installment_adjusted += 1

        # Add installment columns if not already present
        if 'is_installment' not in df.columns:
            df['is_installment'] = False
        if 'installment_number' not in df.columns:
            df['installment_number'] = None
        if 'total_installments' not in df.columns:
            df['total_installments'] = None

        if installment_adjusted > 0:
            print(f"  Info: Adjusted dates for {installment_adjusted} installment transactions")

        # Add category column with confidence scoring
        categorization_results = df['business_name'].apply(self.categorize_expense)

        # Extract fields from results
        df['category'] = categorization_results.apply(lambda x: x['category'])
        df['classification_confidence'] = categorization_results.apply(lambda x: x['confidence_score'])
        df['classification_reason'] = categorization_results.apply(lambda x: ', '.join(x['matched_keywords']))
        df['classification_method'] = 'keyword'
        df['manually_edited'] = False

        # Also add human-readable confidence for display
        df['confidence'] = categorization_results.apply(lambda x: x['confidence'])

        # Add source file information
        df['source_file'] = os.path.basename(file_path)
        df['processed_date'] = datetime.now()

        # Generate classification summary
        total = len(df)
        high_conf = len(df[df['confidence'] == 'high'])
        medium_conf = len(df[df['confidence'] == 'medium'])
        low_conf = len(df[df['confidence'] == 'low'])
        uncertain = len(df[df['confidence'] == 'uncertain'])

        print(f"\n  Classification Summary:")
        print(f"    ✓ High confidence: {high_conf}/{total} ({high_conf/total*100:.1f}%)")
        print(f"    ~ Medium confidence: {medium_conf}/{total} ({medium_conf/total*100:.1f}%)")
        print(f"    ⚠ Low confidence: {low_conf}/{total} ({low_conf/total*100:.1f}%)")
        print(f"    ? Uncertain: {uncertain}/{total} ({uncertain/total*100:.1f}%)")

        if low_conf + uncertain > 0:
            print(f"    → {low_conf + uncertain} transactions may need manual review")

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
