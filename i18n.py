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
                'tagline': 'AI-Powered Expense Tracking',
                'footer_tagline': 'Smart Expense Management',
                'nav_dashboard': 'Dashboard',
                'nav_upload': 'Upload',
                'nav_savings': 'Savings',
                'nav_reports': 'Reports',
                'nav_settings': 'Settings',
                'nav_logout': 'Logout',
                'nav_login': 'Login',
                'nav_signup': 'Sign Up',
                'nav_account': 'Account',

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
                'dashboard_recommendations': 'Savings Recommendations',
                'dashboard_503020_analysis': '50/30/20 Rule Analysis',
                'dashboard_503020_description': 'The 50/30/20 rule recommends: 50% needs, 30% wants, 20% savings and investments',
                'dashboard_monthly_comparison': 'Monthly Comparison',
                'dashboard_category_breakdown': 'Breakdown by Categories (All Months)',
                'dashboard_expense_distribution': 'Expense Distribution - Needs, Wants, Savings',
                'dashboard_expense_by_category': 'Expense Distribution by Categories',
                'dashboard_expenses_by_category': 'Expenses by Categories',
                'dashboard_month': 'Month',
                'dashboard_income': 'Income',
                'dashboard_expenses': 'Expenses',
                'dashboard_savings': 'Savings',
                'dashboard_savings_percent': 'Savings %',
                'dashboard_amount': 'Amount',
                'dashboard_investment': 'Savings & Investments',

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

                # Savings Dashboard
                'savings_tracking': 'Savings Tracking',
                'savings_total_saved': 'Total Saved',
                'savings_in_months': 'in {count} months',
                'savings_average': 'Average Savings',
                'savings_of_income': 'of income',
                'savings_best_month': 'Best Month',
                'savings_worst_month': 'Worst Month',
                'savings_trend_chart': 'Savings Trend Over Time',
                'savings_percentage_chart': 'Savings Percentage by Month',
                'savings_recommended_target': 'Recommended target: 20% savings from monthly income',
                'savings_monthly_breakdown': 'Monthly Breakdown',
                'savings_status': 'Status',
                'savings_status_excellent': 'Excellent',
                'savings_status_good': 'Good',
                'savings_status_fair': 'Fair',
                'savings_status_low': 'Low',

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
                'msg_no_data_description': 'Upload credit card files and enter monthly income to track your savings',
                'msg_upload_file': 'Upload File',

                # Buttons
                'btn_save': 'Save',
                'btn_cancel': 'Cancel',
                'btn_delete': 'Delete',
                'btn_edit': 'Edit',
                'btn_add': 'Add',
                'btn_remove': 'Remove',
                'btn_confirm': 'Confirm',
                'btn_close': 'Close',

                # Review Transactions
                'nav_review_transactions': 'Review & Edit',
                'review_transactions_title': 'Review & Edit Categories',
                'review_transactions_subtitle': 'Review automated classifications and manually edit as needed',
                'total_transactions': 'Total',
                'high_confidence': 'High Confidence',
                'medium_confidence': 'Medium',
                'low_confidence': 'Low',
                'uncertain': 'Uncertain',
                'filter_confidence': 'Filter by Confidence',
                'filter_category': 'Filter by Category',
                'filter_edited': 'Filter by Status',
                'all': 'All',
                'manually_edited_only': 'Manually Edited Only',
                'auto_classified_only': 'Auto-Classified Only',
                'apply_filters': 'Apply',
                'clear_filters': 'Clear',
                'select_all': 'Select All',
                'deselect_all': 'Deselect All',
                'bulk_change_category': 'Change Category To...',
                'apply_to_selected': 'Apply to Selected',
                'recategorize_with_ai': 'Recategorize with AI',
                'date': 'Date',
                'business_name': 'Business',
                'amount': 'Amount',
                'category': 'Category',
                'confidence': 'Confidence',
                'matched_keywords': 'Matched Keywords',
                'actions': 'Actions',
                'save': 'Save',
                'revert': 'Revert',
                'no_transactions_found': 'No transactions found',
                'category_updated': 'Category updated successfully',
                'error_updating': 'Error updating category',

                # Category View
                'category_view_title': 'Category View',
                'category_view_subtitle': 'View expenses for each month by category',
                'select_category': 'Select Category',
                'total_spent': 'Total Spent',
                'monthly_average': 'Monthly Average',
                'per_month': 'Per Month',
                'highest_month': 'Highest Month',
                'lowest_month': 'Lowest Month',
                'monthly_trend': 'Monthly Trend',
                'total_amount': 'Total Amount',
                'transaction_count': 'Transaction Count',
                'average_per_transaction': 'Average per Transaction',
                'no_data_for_category': 'No Data Available',
                'no_data_for_category_desc': 'No expenses found for this category. Upload files or select a different category.',
                'please_select_category': 'Please select a category',
                'please_select_transactions': 'Please select at least one transaction',
                'bulk_update_confirm': 'Update category for',
                'transactions': 'transactions',
                'recategorize_ai_confirm': 'Recategorize using AI for',
                'error_recategorizing': 'Error recategorizing. Make sure Ollama is running.',

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
                'tagline': 'מעקב הוצאות חכם עם בינה מלאכותית',
                'footer_tagline': 'ניהול הוצאות חכם',
                'nav_dashboard': 'לוח בקרה',
                'nav_upload': 'העלאת קבצים',
                'nav_savings': 'חיסכון',
                'nav_reports': 'דוחות',
                'nav_settings': 'הגדרות',
                'nav_logout': 'התנתק',
                'nav_login': 'התחבר',
                'nav_account': 'חשבון',
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
                'dashboard_recommendations': 'המלצות לחיסכון',
                'dashboard_503020_analysis': 'ניתוח כלל 50/30/20',
                'dashboard_503020_description': 'כלל 50/30/20 ממליץ: 50% צרכים, 30% רצונות, 20% חיסכון והשקעות',
                'dashboard_monthly_comparison': 'השוואה בין חודשים',
                'dashboard_category_breakdown': 'פילוח לפי קטגוריות (כל החודשים)',
                'dashboard_expense_distribution': 'התפלגות הוצאות - צרכים, רצונות וחיסכון',
                'dashboard_expense_by_category': 'התפלגות הוצאות לפי קטגוריות',
                'dashboard_expenses_by_category': 'הוצאות לפי קטגוריות',
                'dashboard_month': 'חודש',
                'dashboard_income': 'הכנסות',
                'dashboard_expenses': 'הוצאות',
                'dashboard_savings': 'חיסכון',
                'dashboard_savings_percent': '% חיסכון',
                'dashboard_amount': 'סכום',
                'dashboard_investment': 'חיסכון והשקעות',

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

                # Savings Dashboard
                'savings_tracking': 'מעקב חיסכון',
                'savings_total_saved': 'סך הכל נחסך',
                'savings_in_months': 'ב-{count} חודשים',
                'savings_average': 'חיסכון ממוצע',
                'savings_of_income': 'מההכנסה',
                'savings_best_month': 'החודש הטוב ביותר',
                'savings_worst_month': 'החודש החלש ביותר',
                'savings_trend_chart': 'מגמת חיסכון לאורך זמן',
                'savings_percentage_chart': 'אחוז חיסכון לפי חודש',
                'savings_recommended_target': 'יעד מומלץ: 20% חיסכון מהכנסה חודשית',
                'savings_monthly_breakdown': 'פירוט חודשי',
                'savings_status': 'סטטוס',
                'savings_status_excellent': 'מצוין',
                'savings_status_good': 'טוב',
                'savings_status_fair': 'סביר',
                'savings_status_low': 'נמוך',

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
                'msg_no_data_description': 'העלה קובצי כרטיס אשראי והזן הכנסות חודשיות כדי לעקוב אחר החיסכון שלך',
                'msg_upload_file': 'העלה קובץ',

                # Buttons
                'btn_save': 'שמור',
                'btn_cancel': 'ביטול',
                'btn_delete': 'מחק',
                'btn_edit': 'ערוך',
                'btn_add': 'הוסף',
                'btn_remove': 'הסר',
                'btn_confirm': 'אישור',
                'btn_close': 'סגור',

                # Review Transactions
                'nav_review_transactions': 'סקירה ועריכה',
                'review_transactions_title': 'סקירה ועריכת קטגוריות',
                'review_transactions_subtitle': 'סקור סיווג אוטומטי וערוך ידנית לפי הצורך',
                'total_transactions': 'סה"כ',
                'high_confidence': 'ביטחון גבוה',
                'medium_confidence': 'ביטחון בינוני',
                'low_confidence': 'ביטחון נמוך',
                'uncertain': 'לא וודאי',
                'filter_confidence': 'סנן לפי ביטחון',
                'filter_category': 'סנן לפי קטגוריה',
                'filter_edited': 'סנן לפי סטטוס',
                'all': 'הכל',
                'manually_edited_only': 'נערך ידנית בלבד',
                'auto_classified_only': 'סווג אוטומטית בלבד',
                'apply_filters': 'החל',
                'clear_filters': 'נקה',
                'select_all': 'בחר הכל',
                'deselect_all': 'בטל בחירה',
                'bulk_change_category': 'שנה קטגוריה ל...',
                'apply_to_selected': 'החל על הנבחרים',
                'recategorize_with_ai': 'סווג מחדש עם AI',
                'date': 'תאריך',
                'business_name': 'שם בית עסק',
                'amount': 'סכום',
                'category': 'קטגוריה',
                'confidence': 'ביטחון',
                'matched_keywords': 'מילות מפתח',
                'actions': 'פעולות',
                'save': 'שמור',
                'revert': 'שחזר',
                'no_transactions_found': 'לא נמצאו עסקאות',
                'category_updated': 'הקטגוריה עודכנה בהצלחה',
                'error_updating': 'שגיאה בעדכון קטגוריה',

                # Category View
                'category_view_title': 'תצוגת קטגוריות',
                'category_view_subtitle': 'צפה בהוצאות לפי חודש עבור קטגוריה מסוימת',
                'select_category': 'בחר קטגוריה',
                'total_spent': 'סה"כ הוצאו',
                'monthly_average': 'ממוצע חודשי',
                'per_month': 'לחודש',
                'highest_month': 'חודש הגבוה ביותר',
                'lowest_month': 'חודש הנמוך ביותר',
                'monthly_trend': 'מגמה חודשית',
                'total_amount': 'סכום כולל',
                'transaction_count': 'מספר עסקאות',
                'average_per_transaction': 'ממוצע לעסקה',
                'no_data_for_category': 'אין נתונים זמינים',
                'no_data_for_category_desc': 'לא נמצאו הוצאות עבור קטגוריה זו. העלה קבצים או בחר קטגוריה אחרת.',
                'please_select_category': 'נא לבחור קטגוריה',
                'please_select_transactions': 'נא לבחור לפחות עסקה אחת',
                'bulk_update_confirm': 'עדכן קטגוריה עבור',
                'transactions': 'עסקאות',
                'recategorize_ai_confirm': 'סווג מחדש עם AI עבור',
                'error_recategorizing': 'שגיאה בסיווג מחדש. ודא ש-Ollama פועל.',

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
