"""
Flask web application for MoneyMate - AI-powered expense tracker
"""
import sys
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

import os
import json
import logging
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session, g
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# PERFORMANCE: Import optimization utilities
try:
    from performance_utils import PerformanceMonitor, RequestCache, memoize_for_request
except ImportError:
    # Fallback if file doesn't exist yet
    class PerformanceMonitor:
        @staticmethod
        def measure(func):
            return func
    class RequestCache:
        @staticmethod
        def cached():
            def decorator(func):
                return func
            return decorator
    def memoize_for_request(func):
        return func

# Import authentication and Supabase
from auth import auth, login_required, guest_only
from supabase_db import SupabaseDatabase
from database import ExpenseDatabase

from expense_processor import ExpenseProcessor
from report_generator import ReportGenerator
from ai_categorizer import AICategorizer
from financial_analyzer import FinancialAnalyzer
from i18n import i18n

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-change-this-in-production')
app.config['UPLOAD_FOLDER'] = 'input_files'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size
ALLOWED_EXTENSIONS = {'xlsx', 'xls'}

# Load config
with open('config_ai.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

# Initialize components (database will be set per user)
processor = ExpenseProcessor()
ai_categorizer = AICategorizer()
financial_analyzer = FinancialAnalyzer()


# Register i18n context processor to make 't' function available in all templates
@app.context_processor
def inject_i18n():
    """Make i18n functions available in all templates"""
    return {
        't': i18n.t,
        'current_language': i18n.get_language(),
        'get_direction': i18n.get_direction
    }


def get_db():
    """
    Get database instance for current user.
    OPTIMIZED: Uses request-scoped caching to reuse the same connection within a request.
    """
    # Check if we already have a DB instance for this request
    if hasattr(g, '_database'):
        return g._database

    if auth.is_authenticated():
        # Use Supabase for authenticated users
        db = SupabaseDatabase()
        user_info = auth.get_current_user()
        if user_info:
            db.set_user(user_info['id'])
        g._database = db  # Cache for this request
        return db
    else:
        # Fallback to local SQLite for development (should not happen in production)
        db = ExpenseDatabase(config['database_file'])
        g._database = db  # Cache for this request
        return db


@app.teardown_appcontext
def teardown_db(exception):
    """Clean up database connection at end of request"""
    db = g.pop('_database', None)
    if db is not None:
        # Clear any request-scoped caches
        if hasattr(db, 'clear_cache'):
            pass  # Don't clear - caches are instance-level

ALLOWED_EXTENSIONS = {'xlsx', 'xls'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ============================================
# AUTHENTICATION ROUTES
# ============================================

@app.route('/login', methods=['GET', 'POST'])
@guest_only
def login():
    """User login page"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if not email or not password:
            flash('נא למלא את כל השדות', 'error')
            return render_template('login.html')

        # Attempt login
        success, message, session_data = auth.sign_in(email, password)

        if success:
            flash('התחברת בהצלחה!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page if next_page else url_for('index'))
        else:
            flash(message, 'error')
            return render_template('login.html')

    return render_template('login.html')


@app.route('/signup', methods=['GET', 'POST'])
@guest_only
def signup():
    """User registration page"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        password_confirm = request.form.get('password_confirm')

        if not email or not password or not password_confirm:
            flash('נא למלא את כל השדות', 'error')
            return render_template('signup.html')

        if password != password_confirm:
            flash('הסיסמאות אינן תואמות', 'error')
            return render_template('signup.html')

        if len(password) < 6:
            flash('הסיסמה חייבת להכיל לפחות 6 תווים', 'error')
            return render_template('signup.html')

        # Attempt signup
        success, message, user_data = auth.sign_up(email, password)

        if success:
            flash('נרשמת בהצלחה! נא להתחבר', 'success')
            return redirect(url_for('login'))
        else:
            flash(message, 'error')
            return render_template('signup.html')

    return render_template('signup.html')


@app.route('/logout')
@login_required
def logout():
    """User logout"""
    success, message = auth.sign_out()
    flash('התנתקת בהצלחה', 'success')
    return redirect(url_for('login'))


@app.route('/switch-language/<lang>')
def switch_language(lang):
    """Switch language between Hebrew and English"""
    if lang in ['he', 'en']:
        i18n.set_language(lang)
    # Redirect back to the previous page or home
    return redirect(request.referrer or url_for('index'))


@app.route('/reset-password', methods=['GET', 'POST'])
@guest_only
def reset_password():
    """Password reset page"""
    if request.method == 'POST':
        email = request.form.get('email')

        if not email:
            flash('נא להזין כתובת אימייל', 'error')
            return render_template('reset_password.html')

        success, message = auth.reset_password_request(email)

        if success:
            flash('נשלח אימייל לאיפוס סיסמה', 'success')
            return redirect(url_for('login'))
        else:
            flash(message, 'error')
            return render_template('reset_password.html')

    return render_template('reset_password.html')


# ============================================
# MAIN APPLICATION ROUTES
# ============================================

@app.route('/')
@login_required
@PerformanceMonitor.measure
def index():
    """Home page - Dashboard overview of ALL months - OPTIMIZED"""
    db = get_db()
    report_gen = ReportGenerator(db)

    # Check if onboarding is complete
    if not db.is_onboarding_complete():
        return redirect(url_for('onboarding'))

    # Get available months
    months = db.get_available_months()

    if not months:
        return render_template('welcome.html')

    # Get user settings from database
    monthly_income = float(db.get_setting('monthly_income', '0'))
    fixed_expenses_total = db.get_total_fixed_expenses()
    fixed_expenses_by_type = db.get_fixed_expenses_by_type()

    # Generate reports for ALL months
    monthly_reports = []
    total_income_all = 0
    total_expenses_all = 0
    total_savings_all = 0

    # Aggregate category data across all months
    all_categories = {}

    for year, month in months:
        # OPTIMIZED: Use fast summary instead of full report (10x faster!)
        report = report_gen.generate_monthly_summary_fast(year, month)
        if report['has_data']:
            # Calculate totals for this month
            # Note: report.get('income') already includes monthly_income from settings
            month_income = report.get('income') or 0
            month_expenses = report['total_cc_expenses'] + fixed_expenses_total
            month_savings = month_income - month_expenses

            # Add to overall totals
            total_income_all += month_income
            total_expenses_all += month_expenses
            total_savings_all += month_savings

            # Aggregate categories
            for category, data in report['category_summary'].items():
                if category not in all_categories:
                    all_categories[category] = {'סכום': 0, 'כמות עסקאות': 0}
                all_categories[category]['סכום'] += data['סכום']
                all_categories[category]['כמות עסקאות'] += data.get('כמות עסקאות', 0)

            monthly_reports.append({
                'year': year,
                'month': month,
                'month_name': report['month_name'],
                'income': month_income,
                'expenses': month_expenses,
                'savings': month_savings,
                'savings_rate': (month_savings / month_income * 100) if month_income > 0 else 0
            })

    # Add fixed expenses to category aggregation (multiply by number of months)
    num_months = len(months)
    for expense in db.get_all_fixed_expenses():
        category = expense['category']
        amount = expense['amount'] * num_months  # Total for all months

        if category not in all_categories:
            all_categories[category] = {'סכום': 0, 'כמות עסקאות': 0}
        all_categories[category]['סכום'] += amount
        all_categories[category]['כמות עסקאות'] += num_months  # One per month

    # Perform financial analysis on aggregated data
    # IMPORTANT: Pass total_income so percentages are calculated correctly!
    spending_analysis = financial_analyzer.analyze_spending(all_categories, total_income_all)

    investment_analysis = financial_analyzer.calculate_investment_potential(
        total_income_all,
        spending_analysis['needs']['amount'],
        spending_analysis['wants']['amount']
    )

    recommendations = financial_analyzer.generate_recommendations(
        spending_analysis,
        all_categories,
        total_income_all
    )

    # Summary stats
    summary = {
        'total_income': total_income_all,
        'total_expenses': total_expenses_all,
        'total_savings': total_savings_all,
        'savings_rate': (total_savings_all / total_income_all * 100) if total_income_all > 0 else 0,
        'months_count': len(monthly_reports),
        'avg_monthly_income': total_income_all / len(monthly_reports) if monthly_reports else 0,
        'avg_monthly_expenses': total_expenses_all / len(monthly_reports) if monthly_reports else 0,
        'avg_monthly_savings': total_savings_all / len(monthly_reports) if monthly_reports else 0
    }

    return render_template('dashboard.html',
                         summary=summary,
                         monthly_reports=monthly_reports,
                         all_categories=all_categories,
                         spending_analysis=spending_analysis,
                         investment_analysis=investment_analysis,
                         recommendations=recommendations,
                         months=months)


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_file():
    """Process uploaded credit card files"""
    db = get_db()

    if request.method == 'POST':
        # Check if files were uploaded
        if 'files' not in request.files:
            flash('לא נבחרו קבצים', 'error')
            return redirect(request.url)

        files = request.files.getlist('files')

        if not files or files[0].filename == '':
            flash('לא נבחרו קבצים', 'error')
            return redirect(request.url)

        # Create temporary directory for uploads
        import tempfile
        temp_dir = tempfile.mkdtemp()

        try:
            # Check if AI is available
            use_ai = ai_categorizer.check_ollama_available()
            processed_count = 0
            skipped_count = 0
            error_count = 0
            total_transactions = 0

            for file in files:
                if file and allowed_file(file.filename):
                    filename = file.filename

                    # Check if already processed
                    if db.is_file_processed(filename):
                        skipped_count += 1
                        continue

                    # Save file temporarily
                    filepath = os.path.join(temp_dir, filename)
                    file.save(filepath)

                    try:
                        # Process the file
                        df = processor.process_file(filepath)

                        # Apply AI categorization if enabled
                        if use_ai:
                            for idx in df.index:
                                business_name = df.at[idx, 'business_name']
                                amount = df.at[idx, 'billing_amount']
                                category, confidence, method, reason = ai_categorizer.categorize(business_name, amount)
                                df.at[idx, 'category'] = category
                                df.at[idx, 'classification_method'] = method
                                df.at[idx, 'classification_confidence'] = confidence
                                df.at[idx, 'classification_reason'] = reason

                        # Add to database
                        new_records = db.add_expenses(df)
                        db.mark_file_processed(filename, len(df))

                        processed_count += 1
                        total_transactions += new_records

                    except Exception as e:
                        error_count += 1
                        flash(f'שגיאה בקובץ {filename}: {str(e)}', 'error')
                    finally:
                        # Clean up temp file
                        if os.path.exists(filepath):
                            os.remove(filepath)
                else:
                    flash(f'סוג קובץ לא נתמך: {file.filename}', 'warning')

            # Show summary
            if processed_count > 0:
                flash(f'✅ עובדו בהצלחה {processed_count} קבצים עם {total_transactions} עסקאות', 'success')
                if use_ai:
                    flash('🤖 סיווג AI הופעל', 'info')

            if skipped_count > 0:
                flash(f'⊘ דולגו {skipped_count} קבצים שכבר עובדו', 'warning')

            if error_count > 0:
                flash(f'❌ {error_count} קבצים נכשלו', 'error')

            if processed_count == 0 and skipped_count == 0 and error_count == 0:
                flash('לא נמצאו קבצי Excel תקינים', 'warning')

        finally:
            # Clean up temp directory
            import shutil
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

        return redirect(url_for('index'))

    # Check if Ollama is available
    ollama_available = ai_categorizer.check_ollama_available()

    return render_template('upload.html', ollama_available=ollama_available)


@app.route('/savings-dashboard')
@login_required
def savings_dashboard():
    """Savings tracking dashboard with historical graph"""
    db = get_db()
    report_gen = ReportGenerator(db)
    months = db.get_available_months()

    # Get fixed expenses total and monthly income
    fixed_expenses_total = db.get_total_fixed_expenses()
    monthly_income = float(db.get_setting('monthly_income', 0))

    # Prepare data for chart
    savings_data = []
    month_labels = []

    month_names_he = {
        1: 'ינואר', 2: 'פברואר', 3: 'מרץ', 4: 'אפריל',
        5: 'מאי', 6: 'יוני', 7: 'יולי', 8: 'אוגוסט',
        9: 'ספטמבר', 10: 'אוקטובר', 11: 'נובמבר', 12: 'דצמבר'
    }

    for year, month in sorted(months):  # Sort chronologically
        # Get report data
        report = report_gen.generate_monthly_report(year, month)

        if report['has_data']:
            # Calculate income and expenses properly
            # Note: report.get('income') already includes monthly_income from settings
            total_income = report.get('income') or 0
            total_expenses = report.get('total_cc_expenses', 0) + fixed_expenses_total
            savings = total_income - total_expenses
            savings_percentage = (savings / total_income * 100) if total_income > 0 else 0

            # Add to data
            month_label = f"{month_names_he.get(month, str(month))} {year}"
            month_labels.append(month_label)
            savings_data.append({
                'amount': float(savings),
                'percentage': float(savings_percentage),
                'income': float(total_income),
                'expenses': float(total_expenses),
                'year': year,
                'month': month
            })

    # Calculate summary stats
    if savings_data:
        total_savings = sum(d['amount'] for d in savings_data)
        avg_savings = total_savings / len(savings_data)
        avg_percentage = sum(d['percentage'] for d in savings_data) / len(savings_data)
        best_month = max(savings_data, key=lambda x: x['amount'])
        worst_month = min(savings_data, key=lambda x: x['amount'])

        summary = {
            'total_savings': total_savings,
            'avg_savings': avg_savings,
            'avg_percentage': avg_percentage,
            'best_month': best_month,
            'worst_month': worst_month,
            'months_tracked': len(savings_data)
        }
    else:
        summary = None

    return render_template('savings_dashboard.html',
                         savings_data=savings_data,
                         month_labels=month_labels,
                         summary=summary)


@app.route('/reports')
@login_required
def reports():
    """View all monthly reports"""
    db = get_db()
    report_gen = ReportGenerator(db)
    months = db.get_available_months()

    reports_data = []
    for year, month in months:
        report = report_gen.generate_monthly_report(year, month)
        if report['has_data']:
            reports_data.append(report)

    return render_template('reports.html', reports=reports_data)


@app.route('/report/<int:year>/<int:month>')
@login_required
def view_report(year, month):
    """View specific month report"""
    db = get_db()
    report_gen = ReportGenerator(db)
    report = report_gen.generate_monthly_report(year, month)

    if not report['has_data']:
        flash('No data available for this month', 'error')
        return redirect(url_for('reports'))

    # Get user settings from database
    monthly_income = float(db.get_setting('monthly_income', '0'))
    fixed_expenses_total = db.get_total_fixed_expenses()

    # Fix: Handle None income
    # Note: report.get('income') already includes monthly_income from settings
    total_income = report.get('income') or 0
    total_expenses = report['total_cc_expenses'] + fixed_expenses_total

    # Add fixed expenses to category summary for this month
    category_summary_with_fixed = report['category_summary'].copy()
    for expense in db.get_all_fixed_expenses():
        category = expense['category']
        amount = expense['amount']

        if category not in category_summary_with_fixed:
            category_summary_with_fixed[category] = {'סכום': 0, 'כמות עסקאות': 0}
        category_summary_with_fixed[category]['סכום'] += amount
        category_summary_with_fixed[category]['כמות עסקאות'] += 1

    # Add financial analysis - pass total_income for correct percentage calculation!
    spending_analysis = financial_analyzer.analyze_spending(category_summary_with_fixed, total_income)

    investment_analysis = financial_analyzer.calculate_investment_potential(
        total_income,
        spending_analysis['needs']['amount'],
        spending_analysis['wants']['amount']
    )

    recommendations = financial_analyzer.generate_recommendations(
        spending_analysis,
        category_summary_with_fixed,
        total_income
    )

    return render_template('report_detail.html',
                         report=report,
                         spending_analysis=spending_analysis,
                         investment_analysis=investment_analysis,
                         recommendations=recommendations,
                         total_income=total_income,
                         total_expenses=total_expenses)


@app.route('/onboarding', methods=['GET', 'POST'])
@login_required
def onboarding():
    """Onboarding page for new users"""
    db = get_db()
    report_gen = ReportGenerator(db)
    # If already completed, redirect to home
    if db.is_onboarding_complete() and request.method == 'GET':
        return redirect(url_for('index'))

    if request.method == 'POST':
        try:
            # Get monthly income
            monthly_income = float(request.form.get('monthly_income', 0))
            db.set_setting('monthly_income', str(monthly_income))

            # Get fixed expenses
            descriptions = request.form.getlist('expense_description[]')
            amounts = request.form.getlist('expense_amount[]')
            categories = request.form.getlist('expense_category[]')
            expense_types = request.form.getlist('expense_type[]')

            # Add each fixed expense
            for i in range(len(descriptions)):
                desc = descriptions[i].strip()
                if desc and amounts[i]:  # Only add if description and amount are provided
                    amount = float(amounts[i])
                    if amount > 0:  # Only add positive amounts
                        category = categories[i]
                        exp_type = expense_types[i]
                        db.add_fixed_expense(desc, amount, category, exp_type)

            # Mark onboarding as complete
            db.mark_onboarding_complete()

            flash('🎉 ברוך הבא ל-MoneyMate! ההגדרות נשמרו בהצלחה', 'success')
            return redirect(url_for('index'))

        except Exception as e:
            flash(f'שגיאה בשמירת ההגדרות: {str(e)}', 'error')
            return redirect(request.url)

    return render_template('onboarding.html')


@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """Application settings"""
    global ai_categorizer
    db = get_db()

    if request.method == 'POST':
        # Handle monthly income update
        if 'monthly_income' in request.form:
            try:
                monthly_income = float(request.form.get('monthly_income'))
                db.set_setting('monthly_income', str(monthly_income))
                flash('הכנסה חודשית עודכנה בהצלחה', 'success')
            except:
                flash('שגיאה בעדכון הכנסה חודשית', 'error')

        # Handle billing cycle day update
        if 'billing_cycle_day' in request.form:
            try:
                billing_cycle_day = int(request.form.get('billing_cycle_day'))
                if 1 <= billing_cycle_day <= 28:
                    db.set_setting('billing_cycle_day', str(billing_cycle_day))
                    flash('יום מחזור חיוב עודכן בהצלחה', 'success')
                else:
                    flash('יום מחזור חיוב חייב להיות בין 1 ל-28', 'error')
            except Exception as e:
                logger.error(f'Error updating billing cycle day: {str(e)}')
                flash('שגיאה בעדכון יום מחזור חיוב', 'error')

        # Handle fixed expense deletion
        if 'delete_expense_id' in request.form:
            try:
                expense_id = request.form.get('delete_expense_id')
                result = db.delete_fixed_expense(expense_id)
                flash('הוצאה נמחקה בהצלחה', 'success')
            except Exception as e:
                logger.error(f'Error deleting fixed expense: {str(e)}')
                flash(f'שגיאה במחיקת הוצאה: {str(e)}', 'error')

        # Handle adding new fixed expense
        if 'new_expense_description' in request.form:
            try:
                desc = request.form.get('new_expense_description').strip()
                amount = float(request.form.get('new_expense_amount'))
                category = request.form.get('new_expense_category')
                exp_type = request.form.get('new_expense_type')
                if desc and amount > 0:
                    db.add_fixed_expense(desc, amount, category, exp_type)
                    flash('הוצאה נוספה בהצלחה', 'success')
            except:
                flash('שגיאה בהוספת הוצאה', 'error')

        # Handle AI settings update
        if 'ai_enabled' in request.form:
            try:
                ai_enabled = request.form.get('ai_enabled') == 'on'
                db.set_setting('ai_classification_enabled', str(ai_enabled).lower())
                flash('הגדרות AI עודכנו בהצלחה', 'success')
            except:
                flash('שגיאה בעדכון הגדרות AI', 'error')

        if 'confidence_threshold' in request.form:
            try:
                threshold = float(request.form.get('confidence_threshold'))
                if 0 <= threshold <= 1:
                    db.set_setting('confidence_threshold', str(threshold))
                    # Update config_ai.json
                    config['ai']['confidence_threshold'] = threshold
                    with open('config_ai.json', 'w', encoding='utf-8') as f:
                        json.dump(config, f, ensure_ascii=False, indent=2)
                    flash('רף ביטחון עודכן בהצלחה', 'success')
            except:
                flash('שגיאה בעדכון רף ביטחון', 'error')

        # Handle keyword updates
        if 'category_for_keywords' in request.form:
            try:
                category = request.form.get('category_for_keywords')
                keywords_str = request.form.get('keywords', '')
                keywords = [k.strip() for k in keywords_str.split(',') if k.strip()]

                config['categories'][category] = keywords
                with open('config_ai.json', 'w', encoding='utf-8') as f:
                    json.dump(config, f, ensure_ascii=False, indent=2)
                flash(f'מילות מפתח לקטגוריה "{category}" עודכנו בהצלחה', 'success')
            except:
                flash('שגיאה בעדכון מילות מפתח', 'error')

        # Handle adding new category
        if 'new_category_name' in request.form:
            try:
                category_name = request.form.get('new_category_name').strip()
                keywords_str = request.form.get('new_category_keywords', '')
                keywords = [k.strip() for k in keywords_str.split(',') if k.strip()]

                if category_name:
                    # Check if category already exists
                    if category_name in config['categories']:
                        flash(f'הקטגוריה "{category_name}" כבר קיימת', 'error')
                    else:
                        # Add new category to config
                        config['categories'][category_name] = keywords
                        with open('config_ai.json', 'w', encoding='utf-8') as f:
                            json.dump(config, f, ensure_ascii=False, indent=2)

                        # Reload AI categorizer to pick up new category
                        ai_categorizer = AICategorizer('config_ai.json')

                        flash(f'קטגוריה "{category_name}" נוספה בהצלחה', 'success')
            except Exception as e:
                flash(f'שגיאה בהוספת קטגוריה: {str(e)}', 'error')

        # Handle deleting category
        if 'delete_category' in request.form:
            try:
                category_to_delete = request.form.get('delete_category')

                # Don't allow deleting "אחר" category as it's the default
                if category_to_delete == 'אחר':
                    flash('לא ניתן למחוק את הקטגוריה "אחר"', 'error')
                elif category_to_delete in config['categories']:
                    # Update all expenses with this category to "אחר"
                    conn = db.get_connection()
                    cursor = conn.cursor()
                    cursor.execute('UPDATE expenses SET category = ? WHERE category = ?',
                                 ('אחר', category_to_delete))
                    affected_rows = cursor.rowcount
                    conn.commit()
                    conn.close()

                    # Remove from config
                    del config['categories'][category_to_delete]
                    with open('config_ai.json', 'w', encoding='utf-8') as f:
                        json.dump(config, f, ensure_ascii=False, indent=2)

                    # Reload AI categorizer
                    ai_categorizer = AICategorizer('config_ai.json')

                    flash(f'קטגוריה "{category_to_delete}" נמחקה. {affected_rows} הוצאות עודכנו ל"אחר"', 'success')
            except Exception as e:
                flash(f'שגיאה במחיקת קטגוריה: {str(e)}', 'error')

        # Handle clearing all data
        if 'clear_all_data' in request.form:
            confirmation = request.form.get('clear_data_confirmation', '').strip()
            if confirmation == 'DELETE':
                try:
                    db.delete_all_user_data()
                    flash('✅ כל הנתונים נמחקו בהצלחה. תוכל להעלות קבצים מחדש כעת.', 'success')
                except Exception as e:
                    flash(f'שגיאה במחיקת נתונים: {str(e)}', 'error')
            else:
                flash('אישור שגוי - הקלד DELETE בדיוק כדי למחוק', 'error')

        return redirect(url_for('settings'))

    # Get current settings
    monthly_income = float(db.get_setting('monthly_income', '0'))
    billing_cycle_day = int(db.get_setting('billing_cycle_day', '9'))
    fixed_expenses = db.get_all_fixed_expenses()
    ai_enabled = db.get_setting('ai_classification_enabled', 'true') == 'true'
    confidence_threshold = float(db.get_setting('confidence_threshold', str(config['ai']['confidence_threshold'])))

    return render_template('settings.html',
                         config=config,
                         monthly_income=monthly_income,
                         billing_cycle_day=billing_cycle_day,
                         fixed_expenses=fixed_expenses,
                         ai_enabled=ai_enabled,
                         confidence_threshold=confidence_threshold,
                         ollama_available=ai_categorizer.check_ollama_available())


@app.route('/api/categorize', methods=['POST'])
@login_required
def api_categorize():
    """API endpoint for manual categorization"""
    db = get_db()
    report_gen = ReportGenerator(db)
    data = request.json
    business_name = data.get('business_name')
    category = data.get('category')

    if business_name and category:
        # Save correction
        ai_categorizer._save_correction(business_name, category)
        return jsonify({'success': True})

    return jsonify({'success': False, 'error': 'Missing parameters'}), 400


@app.route('/api/update_expense_category', methods=['POST'])
@login_required
def update_expense_category():
    """Update an expense's category"""
    db = get_db()
    data = request.json
    expense_id = data.get('expense_id')
    new_category = data.get('category')

    if expense_id and new_category:
        try:
            # Get the expense first to save correction
            expense = db.get_expense_by_id(expense_id)
            if expense:
                # Update database
                db.update_expense_category(expense_id, new_category)

                # Save as user correction for future
                ai_categorizer._save_correction(expense['business_name'], new_category)

                return jsonify({'success': True})
            return jsonify({'success': False, 'error': 'Expense not found'}), 404
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    return jsonify({'success': False, 'error': 'Missing parameters'}), 400


@app.route('/expenses/<int:year>/<int:month>')
@login_required
def view_expenses(year, month):
    """View all expenses for a specific month"""
    db = get_db()

    # Get expenses directly from Supabase (not pandas) for proper structure
    start_date, end_date = db.get_billing_cycle_dates(year, month)

    result = db.client.table('expenses')\
        .select('*')\
        .eq('user_id', session['user_id'])\
        .gte('purchase_date', start_date)\
        .lt('purchase_date', end_date)\
        .order('purchase_date', desc=True)\
        .execute()

    expenses = result.data if result.data else []

    if not expenses:
        flash('אין נתונים לחודש זה', 'warning')
        return redirect(url_for('reports'))

    # Convert date strings to datetime objects for template
    from datetime import datetime
    for expense in expenses:
        if expense.get('purchase_date'):
            date_str = expense['purchase_date']
            if 'T' in date_str:
                expense['purchase_date'] = datetime.fromisoformat(date_str.split('T')[0])
            else:
                expense['purchase_date'] = datetime.fromisoformat(date_str)

    # Get all categories for the dropdown
    categories = list(config['categories'].keys())

    # Get month name
    month_names_he = {
        1: 'ינואר', 2: 'פברואר', 3: 'מרץ', 4: 'אפריל',
        5: 'מאי', 6: 'יוני', 7: 'יולי', 8: 'אוגוסט',
        9: 'ספטמבר', 10: 'אוקטובר', 11: 'נובמבר', 12: 'דצמבר'
    }
    month_name = month_names_he.get(month, str(month))

    return render_template('expenses.html',
                         expenses=expenses,
                         categories=categories,
                         year=year,
                         month=month,
                         month_name=month_name)


@app.route('/category_view')
@login_required
def category_view():
    """View expenses by category across all months"""
    db = get_db()

    # Get selected category from query parameter
    selected_category = request.args.get('category')

    # Get all available months
    months = db.get_available_months()

    # Get all categories
    categories = list(config['categories'].keys())

    # If no category selected, default to first one
    if not selected_category and categories:
        selected_category = categories[0]

    # Build monthly data for selected category
    monthly_data = []

    if selected_category:
        for year, month in sorted(months):
            # Get billing cycle dates
            start_date, end_date = db.get_billing_cycle_dates(year, month)

            # Get expenses for this billing cycle (with full transaction details)
            result = db.client.table('expenses')\
                .select('*')\
                .eq('user_id', session['user_id'])\
                .eq('category', selected_category)\
                .gte('purchase_date', start_date)\
                .lt('purchase_date', end_date)\
                .order('purchase_date', desc=True)\
                .execute()

            expenses = result.data if result.data else []
            total = sum(exp['billing_amount'] for exp in expenses)
            count = len(expenses)

            # Get month name
            month_names_he = {
                1: 'ינואר', 2: 'פברואר', 3: 'מרץ', 4: 'אפריל',
                5: 'מאי', 6: 'יוני', 7: 'יולי', 8: 'אוגוסט',
                9: 'ספטמבר', 10: 'אוקטובר', 11: 'נובמבר', 12: 'דצמבר'
            }
            month_name = month_names_he.get(month, str(month))

            # Format transactions for display
            transactions_list = []
            for expense in expenses:
                transactions_list.append({
                    'date': expense['purchase_date'],
                    'business_name': expense['business_name'],
                    'amount': expense['billing_amount'],
                    'classification_method': expense.get('classification_method', 'N/A'),
                    'manually_edited': expense.get('manually_edited', False)
                })

            monthly_data.append({
                'year': year,
                'month': month,
                'month_name': month_name,
                'month_label': f'{month_name} {year}',
                'total': total,
                'count': count,
                'transactions': transactions_list
            })

    # Calculate summary statistics
    if monthly_data:
        total_all_months = sum(m['total'] for m in monthly_data)
        avg_monthly = total_all_months / len(monthly_data)
        max_month = max(monthly_data, key=lambda x: x['total'])
        min_month = min(monthly_data, key=lambda x: x['total'])

        summary = {
            'total': total_all_months,
            'average': avg_monthly,
            'months_count': len(monthly_data),
            'max_month': max_month,
            'min_month': min_month
        }
    else:
        summary = None

    return render_template('category_view.html',
                         categories=categories,
                         selected_category=selected_category,
                         monthly_data=monthly_data,
                         summary=summary)


@app.route('/review_transactions')
@login_required
def review_transactions():
    """Review and manually edit transaction categories"""
    db = get_db()

    # Get filter parameters
    confidence_filter = request.args.get('confidence')
    category_filter = request.args.get('category')
    edited_filter = request.args.get('edited')
    month_filter = request.args.get('month')  # Format: "YYYY-MM"

    # Build query
    query = db.client.table('expenses')\
        .select('*')\
        .eq('user_id', session['user_id'])\
        .order('purchase_date', desc=True)

    if category_filter:
        query = query.eq('category', category_filter)

    if edited_filter == 'true':
        query = query.eq('manually_edited', True)
    elif edited_filter == 'false':
        query = query.eq('manually_edited', False)

    # Add month filter using billing cycle dates
    if month_filter:
        try:
            year, month = map(int, month_filter.split('-'))
            start_date, end_date = db.get_billing_cycle_dates(year, month)
            query = query.gte('purchase_date', start_date).lt('purchase_date', end_date)
        except (ValueError, AttributeError):
            pass  # Invalid month format, ignore filter

    result = query.limit(500).execute()  # Increased limit for month views
    transactions = result.data if result.data else []

    # Calculate confidence levels for display
    for txn in transactions:
        score = txn.get('classification_confidence', 0)
        if score >= 0.8:
            txn['confidence_level'] = 'high'
        elif score >= 0.5:
            txn['confidence_level'] = 'medium'
        elif score >= 0.3:
            txn['confidence_level'] = 'low'
        else:
            txn['confidence_level'] = 'uncertain'

        # Parse date
        txn['purchase_date'] = datetime.strptime(txn['purchase_date'], '%Y-%m-%d')
        # Store original for revert
        txn['original_category'] = txn['category']
        # Store confidence score for display
        txn['confidence_score'] = score

    # Filter by confidence level if specified (client-side filtering done server-side)
    if confidence_filter:
        transactions = [t for t in transactions if t['confidence_level'] == confidence_filter]

    # Get all categories
    categories = list(config['categories'].keys())

    # Get available months for filter dropdown
    available_months = db.get_available_months()

    # Calculate stats
    stats = {
        'total': len(transactions),
        'high_confidence': sum(1 for t in transactions if t['confidence_level'] == 'high'),
        'medium_confidence': sum(1 for t in transactions if t['confidence_level'] == 'medium'),
        'low_confidence': sum(1 for t in transactions if t['confidence_level'] == 'low'),
        'uncertain': sum(1 for t in transactions if t['confidence_level'] == 'uncertain'),
    }

    return render_template('review_transactions.html',
                           transactions=transactions,
                           categories=categories,
                           stats=stats,
                           available_months=available_months,
                           current_month_filter=month_filter)


@app.route('/update_transaction_category', methods=['POST'])
@login_required
def update_transaction_category():
    """Update a single transaction's category"""
    global ai_categorizer
    db = get_db()
    data = request.json

    txn_id = data.get('id')
    new_category = data.get('category')

    if not txn_id or not new_category:
        return jsonify({'error': 'Missing parameters'}), 400

    try:
        # Get the transaction first to extract business name for learning
        user_id = db.get_user_id()
        txn_result = db.client.table('expenses')\
            .select('business_name')\
            .eq('id', txn_id)\
            .eq('user_id', user_id)\
            .maybe_single()\
            .execute()

        if not txn_result.data:
            return jsonify({'error': 'Transaction not found'}), 404

        business_name = txn_result.data.get('business_name')

        # Update the transaction
        result = db.client.table('expenses')\
            .update({
                'category': new_category,
                'manually_edited': True,
                'classification_method': 'manual'
            })\
            .eq('id', txn_id)\
            .eq('user_id', user_id)\
            .execute()

        # Save to AI categorizer for future learning
        learned_keywords = []
        if business_name:
            learned_keywords = ai_categorizer._save_correction(business_name, new_category)
            logger.info(f"Saved correction: {business_name} -> {new_category}, learned: {learned_keywords}")

        return jsonify({
            'success': True,
            'learned_keywords': learned_keywords,
            'message': f'Category updated! Learned {len(learned_keywords)} new keyword(s).' if learned_keywords else 'Category updated!'
        })

    except Exception as e:
        logger.error(f"Error updating transaction category: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/bulk_update_categories', methods=['POST'])
@login_required
def bulk_update_categories():
    """Bulk update multiple transactions' categories"""
    global ai_categorizer
    db = get_db()
    data = request.json

    txn_ids = data.get('ids', [])
    new_category = data.get('category')

    if not txn_ids or not new_category:
        return jsonify({'error': 'Missing parameters'}), 400

    try:
        user_id = db.get_user_id()

        # Update all selected transactions
        for txn_id in txn_ids:
            # Get business name for learning
            txn_result = db.client.table('expenses')\
                .select('business_name')\
                .eq('id', txn_id)\
                .eq('user_id', user_id)\
                .maybe_single()\
                .execute()

            if txn_result.data:
                business_name = txn_result.data.get('business_name')

                # Update transaction
                db.client.table('expenses')\
                    .update({
                        'category': new_category,
                        'manually_edited': True,
                        'classification_method': 'manual'
                    })\
                    .eq('id', txn_id)\
                    .eq('user_id', user_id)\
                    .execute()

                # Save correction for learning
                all_learned_keywords = []
                if business_name:
                    learned = ai_categorizer._save_correction(business_name, new_category)
                    all_learned_keywords.extend(learned)

        return jsonify({
            'success': True,
            'updated': len(txn_ids),
            'total_learned_keywords': len(all_learned_keywords),
            'message': f'Updated {len(txn_ids)} transactions! Learned {len(all_learned_keywords)} new keyword(s).' if all_learned_keywords else f'Updated {len(txn_ids)} transactions!'
        })

    except Exception as e:
        logger.error(f"Error in bulk update: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/recategorize_with_ai', methods=['POST'])
@login_required
def recategorize_with_ai():
    """Recategorize selected transactions using AI"""
    db = get_db()
    data = request.json

    txn_ids = data.get('ids', [])

    if not txn_ids:
        return jsonify({'error': 'No transactions selected'}), 400

    # Get transactions
    result = db.client.table('expenses')\
        .select('id, business_name')\
        .in_('id', txn_ids)\
        .eq('user_id', session['user_id'])\
        .execute()

    transactions = result.data if result.data else []

    # Try to use AI categorizer
    try:
        if not ai_categorizer.check_ollama_available():
            return jsonify({'error': 'Ollama is not running'}), 503

        # Recategorize each transaction
        updated = 0
        for txn in transactions:
            business_name = txn['business_name']
            # Get AI categorization
            new_category, confidence, method, reason = ai_categorizer.categorize(business_name, 0)

            if new_category:
                db.client.table('expenses')\
                    .update({
                        'category': new_category,
                        'classification_method': method,
                        'classification_confidence': confidence,
                        'classification_reason': reason,
                        'manually_edited': False
                    })\
                    .eq('id', txn['id'])\
                    .eq('user_id', session['user_id'])\
                    .execute()
                updated += 1

        return jsonify({'success': True, 'updated': updated})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.template_filter('currency')
def currency_filter(value):
    """Format currency with comma separators"""
    try:
        return "{:,.2f}".format(float(value))
    except:
        return value


if __name__ == '__main__':
    # Ensure upload folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Run the app
    app.run(debug=True, host='127.0.0.1', port=5000)
