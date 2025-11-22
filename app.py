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
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from datetime import datetime
from pathlib import Path

from database import ExpenseDatabase
from expense_processor import ExpenseProcessor
from report_generator import ReportGenerator
from ai_categorizer import AICategorizer
from financial_analyzer import FinancialAnalyzer

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'  # Change in production
app.config['UPLOAD_FOLDER'] = 'input_files'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Load config
with open('config_ai.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

# Initialize components
db = ExpenseDatabase(config['database_file'])
processor = ExpenseProcessor()
report_gen = ReportGenerator(db)
ai_categorizer = AICategorizer()
financial_analyzer = FinancialAnalyzer()

ALLOWED_EXTENSIONS = {'xlsx', 'xls'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    """Home page - Dashboard overview"""
    # Get available months
    months = db.get_available_months()

    if not months:
        return render_template('welcome.html')

    # Get latest month data
    latest_year, latest_month = months[-1]
    report = report_gen.generate_monthly_report(latest_year, latest_month)

    # Add financial analysis
    if report['has_data']:
        spending_analysis = financial_analyzer.analyze_spending(report['category_summary'])

        # Calculate investment potential (using fixed amounts from config)
        fixed_income = 11747
        fixed_expenses = 4400
        # Fix: Handle None income
        income_value = report.get('income') or 0
        total_income = income_value + fixed_income
        total_expenses = report['total_cc_expenses'] + fixed_expenses

        investment_analysis = financial_analyzer.calculate_investment_potential(
            total_income,
            spending_analysis['needs']['amount'],
            spending_analysis['wants']['amount']
        )

        recommendations = financial_analyzer.generate_recommendations(
            spending_analysis,
            report['category_summary'],
            total_income
        )

        return render_template('dashboard.html',
                             report=report,
                             spending_analysis=spending_analysis,
                             investment_analysis=investment_analysis,
                             recommendations=recommendations,
                             total_income=total_income,
                             months=months)

    return render_template('welcome.html')


@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    """Process all credit card files from a folder"""
    if request.method == 'POST':
        folder_path = request.form.get('folder_path', '').strip()

        if not folder_path:
            flash('נא להזין נתיב לתיקייה', 'error')
            return redirect(request.url)

        if not os.path.exists(folder_path):
            flash(f'התיקייה לא נמצאה: {folder_path}', 'error')
            return redirect(request.url)

        if not os.path.isdir(folder_path):
            flash('הנתיב שהוזן אינו תיקייה', 'error')
            return redirect(request.url)

        # Process all Excel files in the folder
        use_ai = ai_categorizer.check_ollama_available()
        processed_count = 0
        skipped_count = 0
        error_count = 0
        total_transactions = 0

        for filename in os.listdir(folder_path):
            if not (filename.endswith(('.xlsx', '.xls')) and not filename.startswith('~')):
                continue

            # Check if already processed
            if db.is_file_processed(filename):
                skipped_count += 1
                continue

            filepath = os.path.join(folder_path, filename)

            try:
                df = processor.process_file(filepath)

                # Apply AI categorization if enabled
                if use_ai:
                    for idx in df.index:
                        business_name = df.at[idx, 'business_name']
                        amount = df.at[idx, 'billing_amount']
                        category, confidence = ai_categorizer.categorize(business_name, amount)
                        df.at[idx, 'category'] = category

                # Add to database
                new_records = db.add_expenses(df)
                db.mark_file_processed(filename, len(df))

                processed_count += 1
                total_transactions += new_records

            except Exception as e:
                error_count += 1
                flash(f'שגיאה בקובץ {filename}: {str(e)}', 'error')

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
            flash('לא נמצאו קבצי Excel בתיקייה', 'warning')

        return redirect(url_for('index'))

    # Check if Ollama is available
    ollama_available = ai_categorizer.check_ollama_available()

    return render_template('upload.html', ollama_available=ollama_available)


@app.route('/reports')
def reports():
    """View all monthly reports"""
    months = db.get_available_months()

    reports_data = []
    for year, month in months:
        report = report_gen.generate_monthly_report(year, month)
        if report['has_data']:
            reports_data.append(report)

    return render_template('reports.html', reports=reports_data)


@app.route('/report/<int:year>/<int:month>')
def view_report(year, month):
    """View specific month report"""
    report = report_gen.generate_monthly_report(year, month)

    if not report['has_data']:
        flash('No data available for this month', 'error')
        return redirect(url_for('reports'))

    # Add financial analysis
    spending_analysis = financial_analyzer.analyze_spending(report['category_summary'])

    fixed_income = 11747
    fixed_expenses = 4400
    # Fix: Handle None income
    income_value = report.get('income') or 0
    total_income = income_value + fixed_income
    total_expenses = report['total_cc_expenses'] + fixed_expenses

    investment_analysis = financial_analyzer.calculate_investment_potential(
        total_income,
        spending_analysis['needs']['amount'],
        spending_analysis['wants']['amount']
    )

    recommendations = financial_analyzer.generate_recommendations(
        spending_analysis,
        report['category_summary'],
        total_income
    )

    return render_template('report_detail.html',
                         report=report,
                         spending_analysis=spending_analysis,
                         investment_analysis=investment_analysis,
                         recommendations=recommendations,
                         total_income=total_income)


@app.route('/settings', methods=['GET', 'POST'])
def settings():
    """Application settings"""
    if request.method == 'POST':
        # Handle settings update
        pass

    return render_template('settings.html',
                         config=config,
                         ollama_available=ai_categorizer.check_ollama_available())


@app.route('/api/categorize', methods=['POST'])
def api_categorize():
    """API endpoint for manual categorization"""
    data = request.json
    business_name = data.get('business_name')
    category = data.get('category')

    if business_name and category:
        # Save correction
        ai_categorizer._save_correction(business_name, category)
        return jsonify({'success': True})

    return jsonify({'success': False, 'error': 'Missing parameters'}), 400


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
