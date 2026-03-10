"""
Supabase Database Manager - Multi-user PostgreSQL database with Row-Level Security
Replaces the SQLite database.py for production use
"""
import os
from datetime import datetime
from typing import Optional, List, Dict, Tuple
import pandas as pd
from supabase import create_client, Client
from dotenv import load_dotenv
import secrets
import logging

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class SupabaseDatabase:
    def __init__(self):
        """Initialize Supabase client"""
        supabase_url = os.getenv('SUPABASE_URL')
        # Use SERVICE_ROLE key for backend operations (bypasses RLS)
        # We manually filter by user_id in all queries for security
        supabase_key = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_ANON_KEY')

        if not supabase_url or not supabase_key:
            raise ValueError(
                "Missing Supabase credentials! "
                "Please set SUPABASE_URL and SUPABASE_SERVICE_KEY in .env file"
            )

        self.client: Client = create_client(supabase_url, supabase_key)
        self.current_user_id = None

    def set_user(self, user_id: str, access_token: str = None):
        """Set the current user ID for all operations"""
        self.current_user_id = user_id
        # Note: We use service role key which bypasses RLS,
        # but we manually filter by user_id in every query for security

    def get_user_id(self) -> str:
        """Get current user ID, raise error if not set"""
        if not self.current_user_id:
            raise ValueError("No user set! Call set_user() first")
        return self.current_user_id

    # ============================================
    # USER SETTINGS
    # ============================================

    def get_user_settings(self, use_cache: bool = True) -> Optional[Dict]:
        """Get user settings, create if doesn't exist. OPTIMIZED with caching."""
        user_id = self.get_user_id()

        # Use cache if available (reduces DB calls)
        cache_key = f'user_settings_{user_id}'
        if use_cache and hasattr(self, '_settings_cache') and cache_key in self._settings_cache:
            return self._settings_cache[cache_key]

        try:
            result = self.client.table('user_settings')\
                .select('*')\
                .eq('user_id', user_id)\
                .execute()

            # If no data, create default settings
            settings = None
            if not result.data or len(result.data) == 0:
                logger.info(f"Creating default settings for user {user_id}")
                settings = self.create_user_settings()
            else:
                settings = result.data[0]

            # Cache the settings
            if settings:
                if not hasattr(self, '_settings_cache'):
                    self._settings_cache = {}
                self._settings_cache[cache_key] = settings

            return settings
        except Exception as e:
            logger.error(f"Error getting user settings: {str(e)}")
            # Try to create settings on error
            try:
                return self.create_user_settings()
            except:
                return None

    def clear_cache(self):
        """Clear all caches when settings are updated"""
        if hasattr(self, '_settings_cache'):
            self._settings_cache.clear()
        if hasattr(self, '_months_cache'):
            self._months_cache.clear()
        if hasattr(self, '_fixed_expenses_cache'):
            self._fixed_expenses_cache.clear()

    def create_user_settings(self, monthly_income: float = 0, language: str = 'he', billing_cycle_day: int = 9) -> Dict:
        """Create initial user settings"""
        user_id = self.get_user_id()
        data = {
            'user_id': user_id,
            'monthly_income': monthly_income,
            'onboarding_complete': False,
            'default_language': language,
            'billing_cycle_day': billing_cycle_day
        }

        try:
            # Use upsert to handle duplicate user_id
            result = self.client.table('user_settings')\
                .upsert(data, on_conflict='user_id')\
                .execute()
            return result.data[0] if result.data else data
        except Exception as e:
            logger.error(f"Error creating user settings: {str(e)}")
            # Return the data we tried to insert
            return data

    def is_onboarding_complete(self) -> bool:
        """Check if user completed onboarding"""
        settings = self.get_user_settings()
        if not settings:
            return False
        return settings.get('onboarding_complete', False)

    def mark_onboarding_complete(self):
        """Mark onboarding as complete"""
        user_id = self.get_user_id()

        try:
            # Ensure settings exist first
            settings = self.get_user_settings()
            if not settings:
                self.create_user_settings()

            self.client.table('user_settings')\
                .update({'onboarding_complete': True})\
                .eq('user_id', user_id)\
                .execute()
        except Exception as e:
            logger.error(f"Error marking onboarding complete: {str(e)}")

    def get_setting(self, key: str, default: str = '') -> str:
        """Get a specific setting value"""
        settings = self.get_user_settings()
        if not settings:
            return default

        # Map old SQLite keys to new schema
        key_map = {
            'monthly_income': 'monthly_income',
            'language': 'default_language',
        }

        actual_key = key_map.get(key, key)
        value = settings.get(actual_key, default)
        return str(value) if value is not None else default

    def set_setting(self, key: str, value: str):
        """Set a specific setting value"""
        user_id = self.get_user_id()

        # Map old SQLite keys to new schema
        key_map = {
            'monthly_income': 'monthly_income',
            'language': 'default_language',
            'billing_cycle_day': 'billing_cycle_day',
        }

        actual_key = key_map.get(key, key)

        try:
            # Ensure settings exist
            settings = self.get_user_settings()
            if not settings:
                # Create default settings first
                self.create_user_settings()

            # Update the setting
            self.client.table('user_settings')\
                .update({actual_key: value})\
                .eq('user_id', user_id)\
                .execute()

            # Clear cache after updating settings
            self.clear_cache()
        except Exception as e:
            logger.error(f"Error setting {key} to {value}: {str(e)}")

    def get_billing_cycle_dates(self, year: int, month: int) -> Tuple[str, str]:
        """
        Calculate billing cycle start and end dates based on user's billing cycle day.

        For example, if billing_cycle_day is 9:
        - Month 10 (October) billing cycle: 2024-09-09 to 2024-10-08
        - Month 11 (November) billing cycle: 2024-10-09 to 2024-11-08

        Args:
            year: The year
            month: The month (1-12)

        Returns:
            Tuple of (start_date, end_date) as ISO format strings
        """
        from datetime import datetime, timedelta
        import calendar as cal

        settings = self.get_user_settings()
        billing_day = int(settings.get('billing_cycle_day', 9)) if settings else 9

        # Billing cycle starts on billing_day of previous month
        # and ends on (billing_day - 1) of current month
        if month == 1:
            start_year = year - 1
            start_month = 12
        else:
            start_year = year
            start_month = month - 1

        # Start date is billing_day of previous month
        start_date = datetime(start_year, start_month, billing_day)

        # End date is (billing_day - 1) of current month
        # If billing_day is 9, then end is 8th
        end_day = billing_day - 1 if billing_day > 1 else cal.monthrange(year, month)[1]
        end_date = datetime(year, month, end_day)

        # Add one day to end_date to make it exclusive (for < comparison in SQL)
        end_date = end_date + timedelta(days=1)

        return start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')

    # ============================================
    # EXPENSES
    # ============================================

    def add_expenses(self, df: pd.DataFrame) -> int:
        """
        Add expenses from DataFrame

        Args:
            df: DataFrame with expense data

        Returns:
            Number of new records added
        """
        user_id = self.get_user_id()
        records = []

        # Replace all NaN values with None to prevent JSON serialization errors
        df = df.replace({pd.NA: None, pd.NaT: None})
        # Also handle numpy NaN
        import numpy as np
        df = df.replace({np.nan: None})

        for _, row in df.iterrows():
            # Skip rows with missing required fields
            billing_amount = row.get('billing_amount')
            if billing_amount is None or (isinstance(billing_amount, float) and pd.isna(billing_amount)):
                logger.warning(f"Skipping row with missing billing_amount: {row.get('business_name')}")
                continue

            # Helper function to safely convert to float or None
            def safe_float(value):
                if value is None:
                    return None
                try:
                    if pd.notna(value):
                        return float(value)
                except (ValueError, TypeError):
                    pass
                return None

            # Helper function to safely get string or None
            def safe_str(value):
                if value is None or (isinstance(value, float) and pd.isna(value)):
                    return None
                return str(value) if value else None

            # Helper function to safely get int or None
            def safe_int(value):
                if value is None or (isinstance(value, float) and pd.isna(value)):
                    return None
                try:
                    return int(value) if value else None
                except (ValueError, TypeError):
                    return None

            record = {
                'user_id': user_id,
                'purchase_date': row.get('purchase_date').strftime('%Y-%m-%d') if pd.notna(row.get('purchase_date')) else None,
                'business_name': safe_str(row.get('business_name')),
                'transaction_amount': safe_float(row.get('transaction_amount')),
                'transaction_currency': safe_str(row.get('transaction_currency')),
                'billing_amount': float(billing_amount),
                'billing_currency': safe_str(row.get('billing_currency')),
                'voucher_number': safe_str(row.get('voucher_number')),
                'additional_details': safe_str(row.get('additional_details')),
                'category': safe_str(row.get('category')) or 'אחר',
                'source_file': safe_str(row.get('source_file')),
                'classification_method': safe_str(row.get('classification_method')),
                'classification_confidence': safe_float(row.get('classification_confidence')),
                'classification_reason': safe_str(row.get('classification_reason')),
                'manually_edited': bool(row.get('manually_edited', False)),
                # Installment fields
                'is_installment': bool(row.get('is_installment', False)),
                'installment_number': safe_int(row.get('installment_number')),
                'total_installments': safe_int(row.get('total_installments'))
            }
            records.append(record)

        if not records:
            logger.warning("No valid records to insert")
            return 0

        # Use upsert to handle duplicates
        result = self.client.table('expenses')\
            .upsert(records, on_conflict='user_id,purchase_date,business_name,billing_amount,voucher_number')\
            .execute()

        return len(result.data) if result.data else 0

    def get_monthly_expenses(self, year: int, month: int) -> pd.DataFrame:
        """
        Get all expenses for a specific billing cycle month.

        Uses the user's billing_cycle_day setting to determine the date range.
        For example, if billing_cycle_day is 9:
        - Month 10 includes expenses from Sept 9 to Oct 8
        """
        user_id = self.get_user_id()

        # Get billing cycle dates
        start_date, end_date = self.get_billing_cycle_dates(year, month)

        result = self.client.table('expenses')\
            .select('*')\
            .eq('user_id', user_id)\
            .gte('purchase_date', start_date)\
            .lt('purchase_date', end_date)\
            .execute()

        if not result.data:
            return pd.DataFrame()

        df = pd.DataFrame(result.data)

        # Convert purchase_date to datetime if it exists
        if 'purchase_date' in df.columns and len(df) > 0:
            df['purchase_date'] = pd.to_datetime(df['purchase_date'])

        return df

    def get_available_months(self, use_cache: bool = True) -> List[Tuple[int, int]]:
        """
        Get list of (year, month) tuples with expense data.

        OPTIMIZED: Uses PostgreSQL date_trunc for fast aggregation.
        Groups expenses by billing cycle instead of calendar month.
        """
        user_id = self.get_user_id()

        try:
            # Simple cache to avoid recalculating on every page load
            cache_key = f'available_months_{user_id}'
            if use_cache and hasattr(self, '_months_cache') and cache_key in self._months_cache:
                return self._months_cache[cache_key]

            # Get min and max dates - much faster than fetching all rows
            result = self.client.table('expenses')\
                .select('purchase_date')\
                .eq('user_id', user_id)\
                .order('purchase_date', desc=False)\
                .limit(1)\
                .execute()

            if not result.data:
                return []

            min_date_str = result.data[0]['purchase_date']

            result = self.client.table('expenses')\
                .select('purchase_date')\
                .eq('user_id', user_id)\
                .order('purchase_date', desc=True)\
                .limit(1)\
                .execute()

            max_date_str = result.data[0]['purchase_date']

            # Parse dates
            min_date = datetime.fromisoformat(min_date_str.split('T')[0] if 'T' in min_date_str else min_date_str)
            max_date = datetime.fromisoformat(max_date_str.split('T')[0] if 'T' in max_date_str else max_date_str)

            settings = self.get_user_settings()
            billing_day = int(settings.get('billing_cycle_day', 9)) if settings else 9

            # Generate all possible months between min and max
            months_set = set()
            current = min_date
            while current <= max_date:
                # Determine billing month
                if current.day >= billing_day:
                    if current.month == 12:
                        billing_month = 1
                        billing_year = current.year + 1
                    else:
                        billing_month = current.month + 1
                        billing_year = current.year
                else:
                    billing_month = current.month
                    billing_year = current.year

                months_set.add((billing_year, billing_month))

                # Move to next month
                if current.month == 12:
                    current = current.replace(year=current.year + 1, month=1)
                else:
                    current = current.replace(month=current.month + 1)

            result_list = sorted(list(months_set), reverse=True)

            # Cache the result
            if not hasattr(self, '_months_cache'):
                self._months_cache = {}
            self._months_cache[cache_key] = result_list

            return result_list

        except Exception as e:
            logger.error(f"Error getting available months: {str(e)}")
            return []

    def get_expense_by_id(self, expense_id: str) -> Optional[Dict]:
        """Get a single expense by ID"""
        user_id = self.get_user_id()

        result = self.client.table('expenses')\
            .select('*')\
            .eq('id', expense_id)\
            .eq('user_id', user_id)\
            .maybe_single()\
            .execute()

        return result.data

    def update_expense_category(self, expense_id: str, category: str):
        """Update expense category and mark as manually edited"""
        user_id = self.get_user_id()

        self.client.table('expenses')\
            .update({
                'category': category,
                'manually_edited': True,
                'classification_method': 'manual'
            })\
            .eq('id', expense_id)\
            .eq('user_id', user_id)\
            .execute()

    # ============================================
    # FIXED EXPENSES
    # ============================================

    def add_fixed_expense(self, description: str, amount: float, category: str, expense_type: str):
        """Add a fixed expense"""
        user_id = self.get_user_id()

        data = {
            'user_id': user_id,
            'description': description,
            'amount': amount,
            'category': category,
            'expense_type': expense_type
        }

        self.client.table('fixed_expenses').insert(data).execute()

    def get_all_fixed_expenses(self, use_cache: bool = True) -> List[Dict]:
        """
        Get all fixed expenses for user.
        OPTIMIZED: Cached to avoid multiple DB calls in same request.
        """
        user_id = self.get_user_id()

        # Use cache if available
        cache_key = f'fixed_expenses_{user_id}'
        if use_cache and hasattr(self, '_fixed_expenses_cache') and cache_key in self._fixed_expenses_cache:
            return self._fixed_expenses_cache[cache_key]

        result = self.client.table('fixed_expenses')\
            .select('*')\
            .eq('user_id', user_id)\
            .execute()

        expenses = result.data if result.data else []

        # Cache the result
        if use_cache:
            if not hasattr(self, '_fixed_expenses_cache'):
                self._fixed_expenses_cache = {}
            self._fixed_expenses_cache[cache_key] = expenses

        return expenses

    def get_total_fixed_expenses(self) -> float:
        """
        Get total amount of fixed expenses.
        OPTIMIZED: Reuses cached data from get_all_fixed_expenses.
        """
        expenses = self.get_all_fixed_expenses()
        return sum(expense['amount'] for expense in expenses)

    def get_fixed_expenses_by_type(self) -> Dict[str, float]:
        """
        Get fixed expenses grouped by type.
        OPTIMIZED: Reuses cached data from get_all_fixed_expenses.
        """
        expenses = self.get_all_fixed_expenses()
        by_type = {'need': 0, 'want': 0}

        for expense in expenses:
            exp_type = expense.get('expense_type', 'need')
            by_type[exp_type] = by_type.get(exp_type, 0) + expense['amount']

        return by_type

    def delete_fixed_expense(self, expense_id):
        """Delete a fixed expense"""
        user_id = self.get_user_id()

        result = self.client.table('fixed_expenses')\
            .delete()\
            .eq('id', expense_id)\
            .eq('user_id', user_id)\
            .execute()

        logger.info(f"Deleted fixed expense {expense_id} for user {user_id}")
        return result

    # ============================================
    # MONTHLY INCOME & ADDITIONAL EXPENSES
    # ============================================

    def get_monthly_income(self, year: int, month: int) -> Optional[float]:
        """
        Get monthly income for a specific month.
        In Supabase, we use the user's default monthly_income from settings.
        """
        settings = self.get_user_settings()
        if not settings:
            return None

        income = settings.get('monthly_income')
        return float(income) if income is not None else None

    def get_additional_expenses(self, year: int, month: int) -> List[Dict]:
        """
        Get additional expenses for a specific month.
        Currently returns empty list as this feature is not yet implemented in Supabase.
        TODO: Create additional_expenses table in Supabase if needed.
        """
        return []

    # ============================================
    # PROCESSED FILES
    # ============================================

    def is_file_processed(self, filename: str) -> bool:
        """Check if file has been processed before"""
        user_id = self.get_user_id()

        try:
            result = self.client.table('processed_files')\
                .select('id')\
                .eq('user_id', user_id)\
                .eq('filename', filename)\
                .execute()

            return result.data is not None and len(result.data) > 0
        except Exception as e:
            logger.error(f"Error checking if file processed: {str(e)}")
            return False

    def mark_file_processed(self, filename: str, record_count: int, file_hash: str = None):
        """Mark a file as processed"""
        user_id = self.get_user_id()

        data = {
            'user_id': user_id,
            'filename': filename,
            'record_count': record_count,
            'file_hash': file_hash
        }

        try:
            self.client.table('processed_files').insert(data).execute()
        except Exception as e:
            logger.error(f"Error marking file as processed: {str(e)}")
            # Don't raise - this is not critical

    def get_processed_files(self) -> List[Dict]:
        """Get all processed files for user"""
        user_id = self.get_user_id()

        result = self.client.table('processed_files')\
            .select('*')\
            .eq('user_id', user_id)\
            .order('processed_date', desc=True)\
            .execute()

        return result.data if result.data else []

    # ============================================
    # SHARED DASHBOARDS
    # ============================================

    def create_shared_dashboard(self, year: int = None, month: int = None,
                                share_all: bool = False, expires_days: int = None) -> str:
        """
        Create a shareable dashboard link

        Args:
            year: Specific year (if not sharing all)
            month: Specific month (if not sharing all)
            share_all: Share all months
            expires_days: Days until expiration (None = never expires)

        Returns:
            Share token
        """
        user_id = self.get_user_id()
        share_token = secrets.token_urlsafe(32)

        data = {
            'user_id': user_id,
            'share_token': share_token,
            'year': year,
            'month': month,
            'share_all_months': share_all,
            'is_active': True
        }

        if expires_days:
            from datetime import timedelta
            expires_at = datetime.now() + timedelta(days=expires_days)
            data['expires_at'] = expires_at.isoformat()

        self.client.table('shared_dashboards').insert(data).execute()

        return share_token

    def get_shared_dashboard(self, share_token: str) -> Optional[Dict]:
        """Get shared dashboard by token (public access)"""
        result = self.client.table('shared_dashboards')\
            .select('*')\
            .eq('share_token', share_token)\
            .eq('is_active', True)\
            .maybe_single()\
            .execute()

        if not result.data:
            return None

        # Check expiration
        dashboard = result.data
        if dashboard.get('expires_at'):
            expires = datetime.fromisoformat(dashboard['expires_at'])
            if datetime.now() > expires:
                return None

        # Increment view count
        self.client.table('shared_dashboards')\
            .update({
                'view_count': dashboard.get('view_count', 0) + 1,
                'last_viewed_at': datetime.now().isoformat()
            })\
            .eq('share_token', share_token)\
            .execute()

        return dashboard

    def deactivate_shared_dashboard(self, share_token: str):
        """Deactivate a shared dashboard"""
        user_id = self.get_user_id()

        self.client.table('shared_dashboards')\
            .update({'is_active': False})\
            .eq('share_token', share_token)\
            .eq('user_id', user_id)\
            .execute()

    def get_user_shared_dashboards(self) -> List[Dict]:
        """Get all shared dashboards for current user"""
        user_id = self.get_user_id()

        result = self.client.table('shared_dashboards')\
            .select('*')\
            .eq('user_id', user_id)\
            .order('created_at', desc=True)\
            .execute()

        return result.data if result.data else []

    # ============================================
    # DATA EXPORT (GDPR COMPLIANCE)
    # ============================================

    def export_all_user_data(self) -> Dict:
        """Export all user data for GDPR compliance"""
        user_id = self.get_user_id()

        # Get all data
        settings = self.get_user_settings()
        expenses = self.client.table('expenses')\
            .select('*')\
            .eq('user_id', user_id)\
            .execute()
        fixed_expenses = self.get_all_fixed_expenses()
        processed_files = self.get_processed_files()
        shared_dashboards = self.get_user_shared_dashboards()

        return {
            'user_id': user_id,
            'exported_at': datetime.now().isoformat(),
            'settings': settings,
            'expenses': expenses.data if expenses.data else [],
            'fixed_expenses': fixed_expenses,
            'processed_files': processed_files,
            'shared_dashboards': shared_dashboards
        }

    def delete_all_user_data(self):
        """
        Delete all user data (GDPR right to deletion)
        WARNING: This is irreversible!
        """
        user_id = self.get_user_id()

        # Delete in reverse order of dependencies
        self.client.table('shared_dashboards').delete().eq('user_id', user_id).execute()
        self.client.table('processed_files').delete().eq('user_id', user_id).execute()
        self.client.table('fixed_expenses').delete().eq('user_id', user_id).execute()
        self.client.table('expenses').delete().eq('user_id', user_id).execute()
        self.client.table('user_settings').delete().eq('user_id', user_id).execute()

        logger.info(f"Deleted all data for user {user_id}")
