"""
Flask web application for MoneyMate - AI-powered expense tracker.
app.py keeps: auth routes, the root dashboard, app factory, shared middleware.
Feature routes live in blueprints/ .
"""
import sys
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

import os
import logging
from urllib.parse import urlparse

from flask import (Flask, render_template, request, jsonify,
                   redirect, url_for, flash, session, g)
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import authentication
from auth import auth, login_required, guest_only

# Initialise extensions (singletons: config, processor, ai_categorizer, financial_analyzer)
import extensions
extensions.init_extensions()

from extensions import config, financial_analyzer, MONTH_NAMES_HE
from db_utils import get_db
from i18n import i18n
from report_generator import ReportGenerator

# ── App creation ────────────────────────────────────────────────────────────

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'change-this-default-in-production')
app.config['UPLOAD_FOLDER'] = 'input_files'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50 MB

# ── Register blueprints ─────────────────────────────────────────────────────

from blueprints.uploads import bp as uploads_bp
from blueprints.reports import bp as reports_bp
from blueprints.expenses import bp as expenses_bp
from blueprints.admin import bp as admin_bp

app.register_blueprint(uploads_bp)
app.register_blueprint(reports_bp)
app.register_blueprint(expenses_bp)
app.register_blueprint(admin_bp)

# ── Request / teardown hooks ────────────────────────────────────────────────

@app.teardown_appcontext
def teardown_db(exception):
    g.pop('_database', None)


@app.context_processor
def inject_i18n():
    return {
        't': i18n.t,
        'current_language': i18n.get_language(),
        'get_direction': i18n.get_direction,
    }


@app.template_filter('currency')
def currency_filter(value):
    try:
        return '{:,.2f}'.format(float(value))
    except (TypeError, ValueError):
        return value


# ── Authentication routes (kept here to preserve url_for('login') / 'index') ─

@app.route('/login', methods=['GET', 'POST'])
@guest_only
def login():
    """User login page."""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if not email or not password:
            flash('נא למלא את כל השדות', 'error')
            return render_template('login.html')

        success, message, session_data = auth.sign_in(email, password)
        if success:
            flash('התחברת בהצלחה!', 'success')
            # SECURITY: validate next_page is a relative path to prevent open redirect
            next_page = request.args.get('next', '')
            if next_page and next_page.startswith('/') and not next_page.startswith('//'):
                return redirect(next_page)
            return redirect(url_for('index'))

        flash(message, 'error')
        return render_template('login.html')

    return render_template('login.html')


@app.route('/signup', methods=['GET', 'POST'])
@guest_only
def signup():
    """User registration page."""
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

        success, message, user_data = auth.sign_up(email, password)
        if success:
            flash('נרשמת בהצלחה! נא להתחבר', 'success')
            return redirect(url_for('login'))

        flash(message, 'error')
        return render_template('signup.html')

    return render_template('signup.html')


@app.route('/logout')
@login_required
def logout():
    """User logout."""
    auth.sign_out()
    flash('התנתקת בהצלחה', 'success')
    return redirect(url_for('login'))


@app.route('/reset-password', methods=['GET', 'POST'])
@guest_only
def reset_password():
    """Password reset page."""
    if request.method == 'POST':
        email = request.form.get('email')
        if not email:
            flash('נא להזין כתובת אימייל', 'error')
            return render_template('reset_password.html')

        success, message = auth.reset_password_request(email)
        if success:
            flash('נשלח אימייל לאיפוס סיסמה', 'success')
            return redirect(url_for('login'))

        flash(message, 'error')
        return render_template('reset_password.html')

    return render_template('reset_password.html')


@app.route('/switch-language/<lang>')
def switch_language(lang):
    """Switch language between Hebrew and English."""
    if lang in ['he', 'en']:
        i18n.set_language(lang)
    # SECURITY: validate referrer is same-origin to prevent open redirect
    referrer = request.referrer
    if referrer:
        parsed = urlparse(referrer)
        if not parsed.netloc or parsed.netloc == request.host:
            return redirect(referrer)
    return redirect(url_for('index'))


# ── Dashboard (kept here so url_for('index') resolves correctly for auth.py decorators) ─

@app.route('/')
@login_required
def index():
    """Home page — Dashboard overview of ALL months."""
    db = get_db()
    report_gen = ReportGenerator(db)

    if not db.is_onboarding_complete():
        return redirect(url_for('admin.onboarding'))

    months = db.get_available_months()
    if not months:
        return render_template('welcome.html')

    monthly_income_setting = float(db.get_setting('monthly_income', '0'))
    fixed_expenses_total = db.get_total_fixed_expenses()
    fixed_expenses_by_type = db.get_fixed_expenses_by_type()

    monthly_reports = []
    total_income_all = total_expenses_all = total_savings_all = 0
    all_categories = {}

    for year, month in months:
        report = report_gen.generate_monthly_summary_fast(year, month)
        if not report['has_data']:
            continue

        month_income = report.get('income') or 0
        month_expenses = report['total_cc_expenses'] + fixed_expenses_total
        month_savings = month_income - month_expenses

        total_income_all += month_income
        total_expenses_all += month_expenses
        total_savings_all += month_savings

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
            'savings_rate': (month_savings / month_income * 100) if month_income > 0 else 0,
        })

    num_months = len(months)
    for expense in db.get_all_fixed_expenses():
        cat = expense['category']
        amount = expense['amount'] * num_months
        if cat not in all_categories:
            all_categories[cat] = {'סכום': 0, 'כמות עסקאות': 0}
        all_categories[cat]['סכום'] += amount
        all_categories[cat]['כמות עסקאות'] += num_months

    spending_analysis = financial_analyzer.analyze_spending(all_categories, total_income_all)
    investment_analysis = financial_analyzer.calculate_investment_potential(
        total_income_all,
        spending_analysis['needs']['amount'],
        spending_analysis['wants']['amount'],
    )
    recommendations = financial_analyzer.generate_recommendations(
        spending_analysis, all_categories, total_income_all
    )

    n = len(monthly_reports)
    summary = {
        'total_income': total_income_all,
        'total_expenses': total_expenses_all,
        'total_savings': total_savings_all,
        'savings_rate': (total_savings_all / total_income_all * 100) if total_income_all > 0 else 0,
        'months_count': n,
        'avg_monthly_income': total_income_all / n if n else 0,
        'avg_monthly_expenses': total_expenses_all / n if n else 0,
        'avg_monthly_savings': total_savings_all / n if n else 0,
    }

    return render_template('dashboard.html',
                           summary=summary,
                           monthly_reports=monthly_reports,
                           all_categories=all_categories,
                           spending_analysis=spending_analysis,
                           investment_analysis=investment_analysis,
                           recommendations=recommendations,
                           months=months)


# ── Entry point ─────────────────────────────────────────────────────────────

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True, host='127.0.0.1', port=5000)
