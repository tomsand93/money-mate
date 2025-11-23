"""
Database Manager - Handles SQLite database for expense tracking
"""
import sqlite3
import pandas as pd
from datetime import datetime
from typing import Optional, List, Dict
import json


class ExpenseDatabase:
    def __init__(self, db_path: str = "expenses.db"):
        self.db_path = db_path
        self.init_database()

    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)

    def init_database(self):
        """Initialize database tables"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Expenses table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                purchase_date DATE NOT NULL,
                business_name TEXT,
                transaction_amount REAL,
                transaction_currency TEXT,
                billing_amount REAL NOT NULL,
                billing_currency TEXT,
                voucher_number TEXT,
                additional_details TEXT,
                category TEXT NOT NULL,
                source_file TEXT,
                processed_date TIMESTAMP,
                classification_method TEXT,
                classification_confidence REAL,
                classification_reason TEXT,
                manually_edited INTEGER DEFAULT 0,
                UNIQUE(purchase_date, business_name, billing_amount, voucher_number)
            )
        ''')

        # Add new columns to existing expenses table if they don't exist
        try:
            cursor.execute("ALTER TABLE expenses ADD COLUMN classification_method TEXT")
        except:
            pass
        try:
            cursor.execute("ALTER TABLE expenses ADD COLUMN classification_confidence REAL")
        except:
            pass
        try:
            cursor.execute("ALTER TABLE expenses ADD COLUMN classification_reason TEXT")
        except:
            pass
        try:
            cursor.execute("ALTER TABLE expenses ADD COLUMN manually_edited INTEGER DEFAULT 0")
        except:
            pass

        # Monthly income table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS monthly_income (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                year INTEGER NOT NULL,
                month INTEGER NOT NULL,
                income_amount REAL NOT NULL,
                notes TEXT,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(year, month)
            )
        ''')

        # Additional monthly expenses (not from credit card)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS additional_expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                year INTEGER NOT NULL,
                month INTEGER NOT NULL,
                description TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Processed files tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS processed_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT UNIQUE NOT NULL,
                processed_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                record_count INTEGER
            )
        ''')

        # User settings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Fixed monthly expenses table (non-credit card expenses)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS fixed_expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                expense_type TEXT NOT NULL,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(description)
            )
        ''')

        conn.commit()
        conn.close()

    def add_expenses(self, df: pd.DataFrame) -> int:
        """
        Add expenses from DataFrame to database
        Returns number of new records added
        """
        conn = self.get_connection()

        # Prepare DataFrame for insertion
        df_to_insert = df.copy()

        # Build column mapping dynamically (only rename columns that exist)
        column_mapping = {
            'תאריך רכישה': 'purchase_date',
            'שם בית עסק': 'business_name',
            'סכום עסקה': 'transaction_amount',
            'מטבע עסקה': 'transaction_currency',
            'סכום חיוב': 'billing_amount',
            'מטבע חיוב': 'billing_currency',
            'מס\' שובר': 'voucher_number',
            "מס' שובר": 'voucher_number',  # Alternative apostrophe
            'פירוט נוסף': 'additional_details',
            'קטגוריה': 'category',
            'קובץ מקור': 'source_file',
            'תאריך עיבוד': 'processed_date'
        }

        # Only rename columns that actually exist in the DataFrame
        rename_dict = {k: v for k, v in column_mapping.items() if k in df_to_insert.columns}
        df_to_insert = df_to_insert.rename(columns=rename_dict)

        # Ensure required columns exist with defaults
        if 'voucher_number' not in df_to_insert.columns:
            df_to_insert['voucher_number'] = ''
        else:
            df_to_insert['voucher_number'] = df_to_insert['voucher_number'].fillna('')

        if 'transaction_amount' not in df_to_insert.columns:
            df_to_insert['transaction_amount'] = df_to_insert['billing_amount']
        if 'transaction_currency' not in df_to_insert.columns:
            df_to_insert['transaction_currency'] = 'ILS'
        if 'billing_currency' not in df_to_insert.columns:
            df_to_insert['billing_currency'] = 'ILS'
        if 'additional_details' not in df_to_insert.columns:
            df_to_insert['additional_details'] = ''

        initial_count = pd.read_sql_query("SELECT COUNT(*) as count FROM expenses", conn).iloc[0]['count']

        try:
            df_to_insert.to_sql('expenses', conn, if_exists='append', index=False)
            final_count = pd.read_sql_query("SELECT COUNT(*) as count FROM expenses", conn).iloc[0]['count']
            new_records = final_count - initial_count
        except Exception as e:
            print(f"Error inserting records: {str(e)}")
            new_records = 0

        conn.close()
        return new_records

    def mark_file_processed(self, filename: str, record_count: int):
        """Mark a file as processed"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT OR REPLACE INTO processed_files (filename, record_count, processed_date)
            VALUES (?, ?, ?)
        ''', (filename, record_count, datetime.now()))

        conn.commit()
        conn.close()

    def is_file_processed(self, filename: str) -> bool:
        """Check if a file has already been processed"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM processed_files WHERE filename = ?', (filename,))
        result = cursor.fetchone()[0] > 0

        conn.close()
        return result

    def set_monthly_income(self, year: int, month: int, amount: float, notes: str = ""):
        """Set or update monthly income"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT OR REPLACE INTO monthly_income (year, month, income_amount, notes, created_date)
            VALUES (?, ?, ?, ?, ?)
        ''', (year, month, amount, notes, datetime.now()))

        conn.commit()
        conn.close()

    def add_additional_expense(self, year: int, month: int, description: str,
                              amount: float, category: str = "אחר"):
        """Add an additional expense (not from credit card)"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO additional_expenses (year, month, description, amount, category)
            VALUES (?, ?, ?, ?, ?)
        ''', (year, month, description, amount, category))

        conn.commit()
        conn.close()

    def get_all_expenses(self) -> pd.DataFrame:
        """Get all expenses from database"""
        conn = self.get_connection()
        df = pd.read_sql_query("SELECT * FROM expenses ORDER BY purchase_date DESC", conn)
        conn.close()

        if len(df) > 0:
            df['purchase_date'] = pd.to_datetime(df['purchase_date'])

        return df

    def get_monthly_expenses(self, year: int, month: int) -> pd.DataFrame:
        """Get expenses for a specific month"""
        conn = self.get_connection()

        query = '''
            SELECT * FROM expenses
            WHERE strftime('%Y', purchase_date) = ? AND strftime('%m', purchase_date) = ?
            ORDER BY purchase_date DESC
        '''

        df = pd.read_sql_query(query, conn, params=(str(year), f"{month:02d}"))
        conn.close()

        if len(df) > 0:
            df['purchase_date'] = pd.to_datetime(df['purchase_date'])

        return df

    def get_monthly_income(self, year: int, month: int) -> Optional[float]:
        """Get income for a specific month"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT income_amount FROM monthly_income WHERE year = ? AND month = ?',
                      (year, month))
        result = cursor.fetchone()

        conn.close()
        return result[0] if result else None

    def get_additional_expenses(self, year: int, month: int) -> List[Dict]:
        """Get additional expenses for a specific month"""
        conn = self.get_connection()
        df = pd.read_sql_query(
            'SELECT * FROM additional_expenses WHERE year = ? AND month = ?',
            conn, params=(year, month)
        )
        conn.close()

        return df.to_dict('records') if len(df) > 0 else []

    def get_available_months(self) -> List[tuple]:
        """Get list of months with data"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT DISTINCT
                strftime('%Y', purchase_date) as year,
                strftime('%m', purchase_date) as month
            FROM expenses
            ORDER BY year DESC, month DESC
        ''')

        results = [(int(row[0]), int(row[1])) for row in cursor.fetchall()]
        conn.close()

        return results

    # User Settings Methods
    def get_setting(self, key: str, default=None):
        """Get a user setting value"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT value FROM user_settings WHERE key = ?', (key,))
        result = cursor.fetchone()

        conn.close()
        return result[0] if result else default

    def set_setting(self, key: str, value: str):
        """Set a user setting value"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT OR REPLACE INTO user_settings (key, value, updated_date)
            VALUES (?, ?, ?)
        ''', (key, value, datetime.now()))

        conn.commit()
        conn.close()

    def is_onboarding_complete(self) -> bool:
        """Check if user has completed onboarding"""
        return self.get_setting('onboarding_complete', 'false') == 'true'

    def mark_onboarding_complete(self):
        """Mark onboarding as complete"""
        self.set_setting('onboarding_complete', 'true')

    # Fixed Expenses Methods
    def add_fixed_expense(self, description: str, amount: float, category: str, expense_type: str):
        """Add a fixed expense (like rent, utilities, etc.)"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT OR REPLACE INTO fixed_expenses (description, amount, category, expense_type, created_date)
            VALUES (?, ?, ?, ?, ?)
        ''', (description, amount, category, expense_type, datetime.now()))

        conn.commit()
        conn.close()

    def get_all_fixed_expenses(self) -> List[Dict]:
        """Get all fixed expenses"""
        conn = self.get_connection()
        df = pd.read_sql_query('SELECT * FROM fixed_expenses ORDER BY expense_type, category', conn)
        conn.close()

        return df.to_dict('records') if len(df) > 0 else []

    def delete_fixed_expense(self, expense_id: int):
        """Delete a fixed expense"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('DELETE FROM fixed_expenses WHERE id = ?', (expense_id,))

        conn.commit()
        conn.close()

    def get_total_fixed_expenses(self) -> float:
        """Get total amount of all fixed expenses"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT SUM(amount) FROM fixed_expenses')
        result = cursor.fetchone()

        conn.close()
        return result[0] if result and result[0] else 0.0

    def get_fixed_expenses_by_type(self) -> Dict:
        """Get fixed expenses grouped by expense type (needs, wants, invest)"""
        conn = self.get_connection()
        df = pd.read_sql_query('''
            SELECT expense_type, category, SUM(amount) as total
            FROM fixed_expenses
            GROUP BY expense_type, category
        ''', conn)
        conn.close()

        result = {'needs': {}, 'wants': {}, 'invest': {}}
        for _, row in df.iterrows():
            exp_type = row['expense_type']
            category = row['category']
            total = row['total']
            if exp_type not in result:
                result[exp_type] = {}
            result[exp_type][category] = total

        return result

    def update_expense_category(self, expense_id: int, new_category: str):
        """Update an expense's category and mark as manually edited"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE expenses
            SET category = ?, manually_edited = 1
            WHERE id = ?
        ''', (new_category, expense_id))

        conn.commit()
        conn.close()

    def get_expense_by_id(self, expense_id: int) -> Optional[Dict]:
        """Get a single expense by ID"""
        conn = self.get_connection()
        df = pd.read_sql_query('SELECT * FROM expenses WHERE id = ?', conn, params=(expense_id,))
        conn.close()

        if len(df) > 0:
            return df.iloc[0].to_dict()
        return None
