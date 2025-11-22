"""
Report Generator - Creates monthly summaries and statistics
"""
import pandas as pd
from datetime import datetime
from typing import Dict, List
from database import ExpenseDatabase
import calendar


class ReportGenerator:
    def __init__(self, db: ExpenseDatabase):
        self.db = db

    def generate_monthly_report(self, year: int, month: int) -> Dict:
        """
        Generate comprehensive monthly report
        """
        # Get expenses from database
        expenses_df = self.db.get_monthly_expenses(year, month)

        if len(expenses_df) == 0:
            return {
                'year': year,
                'month': month,
                'month_name': self._get_hebrew_month(month),
                'has_data': False
            }

        # Calculate total credit card expenses
        total_cc_expenses = float(expenses_df['billing_amount'].sum())

        # Get category breakdown
        category_summary = expenses_df.groupby('category')['billing_amount'].agg(['sum', 'count']).round(2)
        category_summary = category_summary.sort_values('sum', ascending=False)
        category_summary.columns = ['סכום', 'כמות עסקאות']

        # Get additional expenses
        additional_expenses = self.db.get_additional_expenses(year, month)
        total_additional = sum(exp['amount'] for exp in additional_expenses)

        # Total expenses
        total_expenses = total_cc_expenses + total_additional

        # Get income
        income = self.db.get_monthly_income(year, month)

        # Calculate savings
        savings = income - total_expenses if income else None
        savings_rate = (savings / income * 100) if income and income > 0 else None

        # Top 10 expenses
        top_expenses = expenses_df.nlargest(10, 'billing_amount')[
            ['purchase_date', 'business_name', 'billing_amount', 'category']
        ].to_dict('records')

        # Daily spending
        expenses_df['day'] = expenses_df['purchase_date'].dt.day
        daily_summary = expenses_df.groupby('day')['billing_amount'].sum().round(2)

        # Statistics
        stats = {
            'average_transaction': float(expenses_df['billing_amount'].mean()),
            'median_transaction': float(expenses_df['billing_amount'].median()),
            'max_transaction': float(expenses_df['billing_amount'].max()),
            'min_transaction': float(expenses_df['billing_amount'].min()),
            'total_transactions': len(expenses_df),
            'days_with_spending': len(daily_summary),
            'average_daily_spending': float(daily_summary.mean()) if len(daily_summary) > 0 else 0
        }

        # All transactions sorted by date
        all_transactions = expenses_df.sort_values('purchase_date', ascending=False)[
            ['purchase_date', 'business_name', 'billing_amount', 'category']
        ].to_dict('records')

        report = {
            'year': year,
            'month': month,
            'month_name': self._get_hebrew_month(month),
            'has_data': True,
            'income': income,
            'total_cc_expenses': round(total_cc_expenses, 2),
            'total_additional_expenses': round(total_additional, 2),
            'total_expenses': round(total_expenses, 2),
            'savings': round(savings, 2) if savings is not None else None,
            'savings_rate': round(savings_rate, 2) if savings_rate is not None else None,
            'category_summary': category_summary.to_dict('index'),
            'additional_expenses': additional_expenses,
            'top_expenses': top_expenses,
            'all_transactions': all_transactions,
            'daily_summary': daily_summary.to_dict(),
            'stats': stats
        }

        return report

    def get_year_comparison(self, year: int) -> Dict:
        """
        Get year-to-date comparison across months
        """
        months_data = []

        for month in range(1, 13):
            report = self.generate_monthly_report(year, month)
            if report['has_data']:
                months_data.append({
                    'month': month,
                    'month_name': report['month_name'],
                    'income': report['income'],
                    'expenses': report['total_expenses'],
                    'savings': report['savings']
                })

        return {
            'year': year,
            'months': months_data,
            'total_income': sum(m['income'] for m in months_data if m['income']),
            'total_expenses': sum(m['expenses'] for m in months_data),
            'total_savings': sum(m['savings'] for m in months_data if m['savings'])
        }

    def get_category_trends(self, months: int = 6) -> Dict:
        """
        Get category spending trends over last N months
        """
        available_months = self.db.get_available_months()
        recent_months = available_months[:months]

        trends = {}

        for year, month in recent_months:
            expenses_df = self.db.get_monthly_expenses(year, month)
            if len(expenses_df) > 0:
                category_totals = expenses_df.groupby('category')['billing_amount'].sum()

                month_key = f"{year}-{month:02d}"
                for category, amount in category_totals.items():
                    if category not in trends:
                        trends[category] = {}
                    trends[category][month_key] = float(amount)

        return trends

    def _get_hebrew_month(self, month: int) -> str:
        """Get Hebrew month name"""
        hebrew_months = {
            1: 'ינואר', 2: 'פברואר', 3: 'מרץ', 4: 'אפריל',
            5: 'מאי', 6: 'יוני', 7: 'יולי', 8: 'אוגוסט',
            9: 'סספטמבר', 10: 'אוקטובר', 11: 'נובמבר', 12: 'דצמבר'
        }
        return hebrew_months.get(month, str(month))

    def export_to_excel(self, year: int, month: int, output_path: str):
        """
        Export monthly report to Excel file
        """
        report = self.generate_monthly_report(year, month)

        if not report['has_data']:
            print(f"No data for {month}/{year}")
            return

        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # Summary sheet
            summary_data = {
                'פרט': ['הכנסות', 'הוצאות כרטיס אשראי', 'הוצאות נוספות', 'סך הכל הוצאות', 'חיסכון', 'אחוז חיסכון'],
                'סכום': [
                    report['income'],
                    report['total_cc_expenses'],
                    report['total_additional_expenses'],
                    report['total_expenses'],
                    report['savings'],
                    f"{report['savings_rate']}%" if report['savings_rate'] else None
                ]
            }
            pd.DataFrame(summary_data).to_excel(writer, sheet_name='סיכום', index=False)

            # Category breakdown
            category_df = pd.DataFrame.from_dict(report['category_summary'], orient='index')
            category_df.to_excel(writer, sheet_name='לפי קטגוריה')

            # Top expenses
            if report['top_expenses']:
                top_df = pd.DataFrame(report['top_expenses'])
                top_df.to_excel(writer, sheet_name='הוצאות מובילות', index=False)

            # All expenses
            expenses_df = self.db.get_monthly_expenses(year, month)
            expenses_df.to_excel(writer, sheet_name='כל ההוצאות', index=False)

        print(f"Report exported to {output_path}")
