"""
Internationalization (i18n) module for MoneyMate
Supports Hebrew (he) and English (en)
"""
from flask import session, request
from typing import Dict

class I18n:
    def __init__(self, default_language='he'):
        self.default_language = default_language
        self.translations = self._load_translations()

    def _load_translations(self) -> Dict[str, Dict[str, str]]:
        """Load all translations"""
        return {
            'en': {
                # Navigation
                'app_name': 'MoneyMate',
                'nav_dashboard': 'Dashboard',
                'nav_upload': 'Upload',
                'nav_savings': 'Savings',
                'nav_reports': 'Reports',
                'nav_settings': 'Settings',
                'nav_logout': 'Logout',
                'nav_login': 'Login',
                'nav_signup': 'Sign Up',

                # Authentication
                'auth_email': 'Email',
                'auth_password': 'Password',
                'auth_confirm_password': 'Confirm Password',
                'auth_login_button': 'Login',
                'auth_signup_button': 'Create Account',
                'auth_forgot_password': 'Forgot Password?',
                'auth_no_account': "Don't have an account?",
                'auth_have_account': 'Already have an account?',
                'auth_reset_password': 'Reset Password',

                # Dashboard
                'dashboard_title': 'Financial Overview',
                'dashboard_total_income': 'Total Income',
                'dashboard_total_expenses': 'Total Expenses',
                'dashboard_total_savings': 'Total Savings',
                'dashboard_savings_rate': 'Savings Rate',
                'dashboard_months_tracked': 'Months Tracked',
                'dashboard_avg_monthly': 'Avg Monthly',

                # Categories
                'cat_climbing_sports': 'Climbing & Sports',
                'cat_transportation': 'Transportation',
                'cat_eating_out': 'Eating Out',
                'cat_supermarket': 'Supermarket',
                'cat_travel': 'Travel & Trips',
                'cat_entertainment': 'Entertainment',
                'cat_health': 'Health',
                'cat_clothing': 'Clothing & Shoes',
                'cat_online_shopping': 'Online Shopping',
                'cat_personal_care': 'Personal Care',
                'cat_bills_subscriptions': 'Bills & Subscriptions',
                'cat_other': 'Other',

                # 50/30/20 Analysis
                'analysis_needs': 'Needs',
                'analysis_wants': 'Wants',
                'analysis_savings': 'Savings',
                'analysis_target': 'Target',
                'analysis_actual': 'Actual',
                'analysis_status_good': 'On Track',
                'analysis_status_over': 'Over Budget',

                # Upload
                'upload_title': 'Upload Expenses',
                'upload_folder_path': 'Folder Path',
                'upload_browse': 'Browse',
                'upload_or_drag': 'or drag Excel files here',
                'upload_button': 'Process Files',
                'upload_supported_formats': 'Supported formats: .xlsx, .xls',
                'upload_max_size': 'Max file size: 16 MB',

                # Onboarding
                'onboarding_welcome': 'Welcome to MoneyMate!',
                'onboarding_step1': 'Step 1: Monthly Income',
                'onboarding_step2': 'Step 2: Fixed Expenses',
                'onboarding_step3': 'All Set!',
                'onboarding_monthly_income': 'Monthly Income',
                'onboarding_optional': '(Optional - you can add this later)',
                'onboarding_add_expense': 'Add Fixed Expense',
                'onboarding_expense_description': 'Description',
                'onboarding_expense_amount': 'Amount',
                'onboarding_expense_category': 'Category',
                'onboarding_expense_type': 'Type',
                'onboarding_type_need': 'Need',
                'onboarding_type_want': 'Want',
                'onboarding_complete': 'Complete Setup',
                'onboarding_skip': 'Skip for now',

                # Settings
                'settings_title': 'Settings',
                'settings_account': 'Account',
                'settings_preferences': 'Preferences',
                'settings_data': 'Data Management',
                'settings_language': 'Language',
                'settings_monthly_income': 'Monthly Income',
                'settings_fixed_expenses': 'Fixed Expenses',
                'settings_export_data': 'Export All Data',
                'settings_delete_account': 'Delete Account',
                'settings_delete_warning': 'This will permanently delete all your data!',
                'settings_save': 'Save Changes',

                # Share Dashboard
                'share_title': 'Share Dashboard',
                'share_create_link': 'Create Share Link',
                'share_copy_link': 'Copy Link',
                'share_link_copied': 'Link copied!',
                'share_expires': 'Expires',
                'share_never': 'Never',
                'share_active': 'Active',
                'share_deactivate': 'Deactivate',

                # Messages
                'msg_success': 'Success!',
                'msg_error': 'Error',
                'msg_warning': 'Warning',
                'msg_info': 'Info',
                'msg_login_required': 'Please login to continue',
                'msg_file_uploaded': 'Files processed successfully',
                'msg_settings_saved': 'Settings saved',
                'msg_no_data': 'No data available',

                # Buttons
                'btn_save': 'Save',
                'btn_cancel': 'Cancel',
                'btn_delete': 'Delete',
                'btn_edit': 'Edit',
                'btn_add': 'Add',
                'btn_remove': 'Remove',
                'btn_confirm': 'Confirm',
                'btn_close': 'Close',

                # Time
                'month_01': 'January',
                'month_02': 'February',
                'month_03': 'March',
                'month_04': 'April',
                'month_05': 'May',
                'month_06': 'June',
                'month_07': 'July',
                'month_08': 'August',
                'month_09': 'September',
                'month_10': 'October',
                'month_11': 'November',
                'month_12': 'December',
            },
            'he': {
                # Navigation
                'app_name': 'MoneyMate',
                'nav_dashboard': 'לוח בקרה',
                'nav_upload': 'העלאת קבצים',
                'nav_savings': 'חיסכון',
                'nav_reports': 'דוחות',
                'nav_settings': 'הגדרות',
                'nav_logout': 'התנתק',
                'nav_login': 'התחבר',
                'nav_signup': 'הרשמה',

                # Authentication
                'auth_email': 'אימייל',
                'auth_password': 'סיסמה',
                'auth_confirm_password': 'אימות סיסמה',
                'auth_login_button': 'התחבר',
                'auth_signup_button': 'צור חשבון',
                'auth_forgot_password': 'שכחת סיסמה?',
                'auth_no_account': 'אין לך חשבון?',
                'auth_have_account': 'כבר יש לך חשבון?',
                'auth_reset_password': 'איפוס סיסמה',

                # Dashboard
                'dashboard_title': 'סקירה פיננסית',
                'dashboard_total_income': 'סך הכנסות',
                'dashboard_total_expenses': 'סך הוצאות',
                'dashboard_total_savings': 'סך חיסכון',
                'dashboard_savings_rate': 'אחוז חיסכון',
                'dashboard_months_tracked': 'חודשים במעקב',
                'dashboard_avg_monthly': 'ממוצע חודשי',

                # Categories
                'cat_climbing_sports': 'טיפוס וספורט',
                'cat_transportation': 'תחבורה',
                'cat_eating_out': 'אוכל בחוץ',
                'cat_supermarket': 'סופרמרקט',
                'cat_travel': 'נסיעות וטיולים',
                'cat_entertainment': 'בילויים',
                'cat_health': 'בריאות',
                'cat_clothing': 'ביגוד והנעלה',
                'cat_online_shopping': 'קניות אונליין',
                'cat_personal_care': 'טיפוח אישי',
                'cat_bills_subscriptions': 'חשבונות ומנויים',
                'cat_other': 'אחר',

                # 50/30/20 Analysis
                'analysis_needs': 'צרכים',
                'analysis_wants': 'רצונות',
                'analysis_savings': 'חיסכון',
                'analysis_target': 'יעד',
                'analysis_actual': 'בפועל',
                'analysis_status_good': 'במסלול',
                'analysis_status_over': 'מעל התקציב',

                # Upload
                'upload_title': 'העלאת הוצאות',
                'upload_folder_path': 'נתיב תיקייה',
                'upload_browse': 'עיון',
                'upload_or_drag': 'או גרור קבצי Excel לכאן',
                'upload_button': 'עבד קבצים',
                'upload_supported_formats': 'פורמטים נתמכים: .xlsx, .xls',
                'upload_max_size': 'גודל קובץ מקסימלי: 16 MB',

                # Onboarding
                'onboarding_welcome': 'ברוך הבא ל-MoneyMate!',
                'onboarding_step1': 'שלב 1: הכנסה חודשית',
                'onboarding_step2': 'שלב 2: הוצאות קבועות',
                'onboarding_step3': 'הכל מוכן!',
                'onboarding_monthly_income': 'הכנסה חודשית',
                'onboarding_optional': '(אופציונלי - ניתן להוסיף מאוחר יותר)',
                'onboarding_add_expense': 'הוסף הוצאה קבועה',
                'onboarding_expense_description': 'תיאור',
                'onboarding_expense_amount': 'סכום',
                'onboarding_expense_category': 'קטגוריה',
                'onboarding_expense_type': 'סוג',
                'onboarding_type_need': 'צורך',
                'onboarding_type_want': 'רצון',
                'onboarding_complete': 'השלם הגדרה',
                'onboarding_skip': 'דלג לעכשיו',

                # Settings
                'settings_title': 'הגדרות',
                'settings_account': 'חשבון',
                'settings_preferences': 'העדפות',
                'settings_data': 'ניהול נתונים',
                'settings_language': 'שפה',
                'settings_monthly_income': 'הכנסה חודשית',
                'settings_fixed_expenses': 'הוצאות קבועות',
                'settings_export_data': 'ייצוא כל הנתונים',
                'settings_delete_account': 'מחק חשבון',
                'settings_delete_warning': 'פעולה זו תמחק לצמיתות את כל הנתונים שלך!',
                'settings_save': 'שמור שינויים',

                # Share Dashboard
                'share_title': 'שתף לוח בקרה',
                'share_create_link': 'צור קישור שיתוף',
                'share_copy_link': 'העתק קישור',
                'share_link_copied': 'הקישור הועתק!',
                'share_expires': 'פג תוקף',
                'share_active': 'פעיל',
                'share_never': 'לעולם לא',
                'share_deactivate': 'השבת',

                # Messages
                'msg_success': 'הצלחה!',
                'msg_error': 'שגיאה',
                'msg_warning': 'אזהרה',
                'msg_info': 'מידע',
                'msg_login_required': 'נא להתחבר כדי להמשיך',
                'msg_file_uploaded': 'הקבצים עובדו בהצלחה',
                'msg_settings_saved': 'ההגדרות נשמרו',
                'msg_no_data': 'אין נתונים זמינים',

                # Buttons
                'btn_save': 'שמור',
                'btn_cancel': 'ביטול',
                'btn_delete': 'מחק',
                'btn_edit': 'ערוך',
                'btn_add': 'הוסף',
                'btn_remove': 'הסר',
                'btn_confirm': 'אישור',
                'btn_close': 'סגור',

                # Time
                'month_01': 'ינואר',
                'month_02': 'פברואר',
                'month_03': 'מרץ',
                'month_04': 'אפריל',
                'month_05': 'מאי',
                'month_06': 'יוני',
                'month_07': 'יולי',
                'month_08': 'אוגוסט',
                'month_09': 'ספטמבר',
                'month_10': 'אוקטובר',
                'month_11': 'נובמבר',
                'month_12': 'דצמבר',
            }
        }

    def get_language(self) -> str:
        """Get current language from session or use default"""
        return session.get('language', self.default_language)

    def set_language(self, language: str):
        """Set language in session"""
        if language in ['he', 'en']:
            session['language'] = language

    def translate(self, key: str, lang: str = None) -> str:
        """
        Translate a key to the current or specified language

        Args:
            key: Translation key
            lang: Optional language override

        Returns:
            Translated string or key if not found
        """
        if lang is None:
            lang = self.get_language()

        return self.translations.get(lang, {}).get(key, key)

    def t(self, key: str, lang: str = None) -> str:
        """Shorthand for translate()"""
        return self.translate(key, lang)

    def get_all_translations(self, lang: str = None) -> Dict[str, str]:
        """Get all translations for a language"""
        if lang is None:
            lang = self.get_language()
        return self.translations.get(lang, {})

    def get_direction(self, lang: str = None) -> str:
        """Get text direction for language (rtl for Hebrew, ltr for English)"""
        if lang is None:
            lang = self.get_language()
        return 'rtl' if lang == 'he' else 'ltr'


# Global instance
i18n = I18n()

# Template helper function
def get_translation(key: str) -> str:
    """Helper function for use in templates"""
    return i18n.translate(key)
