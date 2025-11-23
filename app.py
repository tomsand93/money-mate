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
    """Home page - Dashboard overview of ALL months"""
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
        report = report_gen.generate_monthly_report(year, month)
        if report['has_data']:
            # Calculate totals for this month
            income_value = report.get('income') or 0
            month_income = income_value + monthly_income
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


@app.route('/savings-dashboard')
def savings_dashboard():
    """Savings tracking dashboard with historical graph"""
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
            income_value = report.get('income') or 0
            total_income = income_value + monthly_income
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

    # Get user settings from database
    monthly_income = float(db.get_setting('monthly_income', '0'))
    fixed_expenses_total = db.get_total_fixed_expenses()

    # Fix: Handle None income
    income_value = report.get('income') or 0
    total_income = income_value + monthly_income
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
def onboarding():
    """Onboarding page for new users"""
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
def settings():
    """Application settings"""
    global ai_categorizer

    if request.method == 'POST':
        # Handle monthly income update
        if 'monthly_income' in request.form:
            try:
                monthly_income = float(request.form.get('monthly_income'))
                db.set_setting('monthly_income', str(monthly_income))
                flash('הכנסה חודשית עודכנה בהצלחה', 'success')
            except:
                flash('שגיאה בעדכון הכנסה חודשית', 'error')

        # Handle fixed expense deletion
        if 'delete_expense_id' in request.form:
            try:
                expense_id = int(request.form.get('delete_expense_id'))
                db.delete_fixed_expense(expense_id)
                flash('הוצאה נמחקה בהצלחה', 'success')
            except:
                flash('שגיאה במחיקת הוצאה', 'error')

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

        return redirect(url_for('settings'))

    # Get current settings
    monthly_income = float(db.get_setting('monthly_income', '0'))
    fixed_expenses = db.get_all_fixed_expenses()
    ai_enabled = db.get_setting('ai_classification_enabled', 'true') == 'true'
    confidence_threshold = float(db.get_setting('confidence_threshold', str(config['ai']['confidence_threshold'])))

    return render_template('settings.html',
                         config=config,
                         monthly_income=monthly_income,
                         fixed_expenses=fixed_expenses,
                         ai_enabled=ai_enabled,
                         confidence_threshold=confidence_threshold,
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


@app.route('/api/update_expense_category', methods=['POST'])
def update_expense_category():
    """Update an expense's category"""
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
def view_expenses(year, month):
    """View all expenses for a specific month"""
    expenses_df = db.get_monthly_expenses(year, month)

    if len(expenses_df) == 0:
        flash('אין נתונים לחודש זה', 'warning')
        return redirect(url_for('reports'))

    # Convert to list of dicts
    expenses = expenses_df.to_dict('records')

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
