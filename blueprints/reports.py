"""
Reports blueprint — monthly reports, savings dashboard, category view.
"""
import logging

from flask import Blueprint, render_template, request, redirect, url_for, flash, session

from auth import login_required
from db_utils import get_db
from extensions import MONTH_NAMES_HE, config, financial_analyzer

logger = logging.getLogger(__name__)

bp = Blueprint('reports', __name__)


@bp.route('/savings-dashboard')
@login_required
def savings_dashboard():
    """Savings tracking dashboard with historical graph."""
    db = get_db()
    from report_generator import ReportGenerator
    report_gen = ReportGenerator(db)
    months = db.get_available_months()

    fixed_expenses_total = db.get_total_fixed_expenses()
    monthly_income = float(db.get_setting('monthly_income', 0))

    savings_data = []
    month_labels = []

    for year, month in sorted(months):
        report = report_gen.generate_monthly_report(year, month)
        if not report['has_data']:
            continue

        total_income = report.get('income') or 0
        total_expenses = report.get('total_cc_expenses', 0) + fixed_expenses_total
        savings = total_income - total_expenses
        savings_pct = (savings / total_income * 100) if total_income > 0 else 0

        month_label = f"{MONTH_NAMES_HE.get(month, str(month))} {year}"
        month_labels.append(month_label)
        savings_data.append({
            'amount': float(savings),
            'percentage': float(savings_pct),
            'income': float(total_income),
            'expenses': float(total_expenses),
            'year': year,
            'month': month,
        })

    summary = None
    if savings_data:
        total_savings = sum(d['amount'] for d in savings_data)
        summary = {
            'total_savings': total_savings,
            'avg_savings': total_savings / len(savings_data),
            'avg_percentage': sum(d['percentage'] for d in savings_data) / len(savings_data),
            'best_month': max(savings_data, key=lambda x: x['amount']),
            'worst_month': min(savings_data, key=lambda x: x['amount']),
            'months_tracked': len(savings_data),
        }

    return render_template('savings_dashboard.html',
                           savings_data=savings_data,
                           month_labels=month_labels,
                           summary=summary)


@bp.route('/reports')
@login_required
def reports():
    """View all monthly reports."""
    db = get_db()
    from report_generator import ReportGenerator
    report_gen = ReportGenerator(db)
    months = db.get_available_months()

    reports_data = []
    for year, month in months:
        report = report_gen.generate_monthly_report(year, month)
        if report['has_data']:
            reports_data.append(report)

    return render_template('reports.html', reports=reports_data)


@bp.route('/report/<int:year>/<int:month>')
@login_required
def view_report(year, month):
    """View specific month report."""
    db = get_db()
    from report_generator import ReportGenerator
    report_gen = ReportGenerator(db)
    report = report_gen.generate_monthly_report(year, month)

    if not report['has_data']:
        flash('No data available for this month', 'error')
        return redirect(url_for('reports.reports'))

    fixed_expenses_total = db.get_total_fixed_expenses()
    total_income = report.get('income') or 0
    total_expenses = report['total_cc_expenses'] + fixed_expenses_total

    category_summary_with_fixed = report['category_summary'].copy()
    for expense in db.get_all_fixed_expenses():
        cat = expense['category']
        if cat not in category_summary_with_fixed:
            category_summary_with_fixed[cat] = {'סכום': 0, 'כמות עסקאות': 0}
        category_summary_with_fixed[cat]['סכום'] += expense['amount']
        category_summary_with_fixed[cat]['כמות עסקאות'] += 1

    spending_analysis = financial_analyzer.analyze_spending(category_summary_with_fixed, total_income)
    investment_analysis = financial_analyzer.calculate_investment_potential(
        total_income,
        spending_analysis['needs']['amount'],
        spending_analysis['wants']['amount'],
    )
    recommendations = financial_analyzer.generate_recommendations(
        spending_analysis, category_summary_with_fixed, total_income
    )

    return render_template('report_detail.html',
                           report=report,
                           spending_analysis=spending_analysis,
                           investment_analysis=investment_analysis,
                           recommendations=recommendations,
                           total_income=total_income,
                           total_expenses=total_expenses)


@bp.route('/category_view')
@login_required
def category_view():
    """View expenses by category across all months."""
    db = get_db()
    selected_category = request.args.get('category')
    months = db.get_available_months()
    categories = list(config['categories'].keys())

    if not selected_category and categories:
        selected_category = categories[0]

    monthly_data = []
    if selected_category:
        for year, month in sorted(months):
            start_date, end_date = db.get_billing_cycle_dates(year, month)

            result = db.client.table('expenses') \
                .select('*') \
                .eq('user_id', session['user_id']) \
                .eq('category', selected_category) \
                .gte('purchase_date', start_date) \
                .lt('purchase_date', end_date) \
                .order('purchase_date', desc=True) \
                .execute()

            expenses = result.data or []
            total = sum(exp['billing_amount'] for exp in expenses)
            month_name = MONTH_NAMES_HE.get(month, str(month))

            transactions_list = [{
                'date': exp['purchase_date'],
                'business_name': exp['business_name'],
                'amount': exp['billing_amount'],
                'classification_method': exp.get('classification_method', 'N/A'),
                'manually_edited': exp.get('manually_edited', False),
            } for exp in expenses]

            monthly_data.append({
                'year': year,
                'month': month,
                'month_name': month_name,
                'month_label': f'{month_name} {year}',
                'total': total,
                'count': len(expenses),
                'transactions': transactions_list,
            })

    summary = None
    if monthly_data:
        total_all = sum(m['total'] for m in monthly_data)
        summary = {
            'total': total_all,
            'average': total_all / len(monthly_data),
            'months_count': len(monthly_data),
            'max_month': max(monthly_data, key=lambda x: x['total']),
            'min_month': min(monthly_data, key=lambda x: x['total']),
        }

    return render_template('category_view.html',
                           categories=categories,
                           selected_category=selected_category,
                           monthly_data=monthly_data,
                           summary=summary)
