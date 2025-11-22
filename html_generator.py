"""
HTML Report Generator - Creates interactive HTML dashboard
"""
from jinja2 import Template
from datetime import datetime
from typing import Dict
import os


class HTMLGenerator:
    def __init__(self):
        self.template = self._get_template()

    def generate_html_report(self, report: Dict, output_path: str):
        """
        Generate HTML report from monthly report data
        """
        html_content = self.template.render(report=report, generated_date=datetime.now())

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"HTML report generated: {output_path}")

    def _get_template(self) -> Template:
        """
        Get Jinja2 template for HTML report
        """
        template_str = '''
<!DOCTYPE html>
<html dir="rtl" lang="he">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>סיכום חודשי - {{ report.month_name }} {{ report.year }}</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            color: #333;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            overflow: hidden;
        }

        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }

        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }

        .header p {
            font-size: 1.2em;
            opacity: 0.9;
        }

        .content {
            padding: 30px;
        }

        .summary-cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }

        .card {
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: transform 0.3s;
        }

        .card:hover {
            transform: translateY(-5px);
        }

        .card.income {
            background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
        }

        .card.expenses {
            background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
        }

        .card.savings {
            background: linear-gradient(135deg, #d299c2 0%, #fef9d7 100%);
        }

        .card.positive {
            background: linear-gradient(135deg, #a8e6cf 0%, #dcedc8 100%);
        }

        .card.negative {
            background: linear-gradient(135deg, #ffccbc 0%, #ffab91 100%);
        }

        .card-label {
            font-size: 0.9em;
            color: #555;
            margin-bottom: 10px;
            font-weight: 600;
        }

        .card-value {
            font-size: 2em;
            font-weight: bold;
            color: #333;
        }

        .section {
            margin-bottom: 40px;
        }

        .section-title {
            font-size: 1.8em;
            color: #667eea;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #667eea;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
            background: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border-radius: 8px;
            overflow: hidden;
        }

        th {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px;
            text-align: right;
            font-weight: 600;
        }

        td {
            padding: 12px 15px;
            border-bottom: 1px solid #eee;
            text-align: right;
        }

        tr:hover {
            background-color: #f5f7fa;
        }

        .amount {
            font-weight: bold;
            color: #667eea;
        }

        .chart-container {
            margin: 20px 0;
            padding: 20px;
            background: #f5f7fa;
            border-radius: 10px;
        }

        .bar-chart {
            display: flex;
            flex-direction: column;
            gap: 15px;
        }

        .bar-item {
            display: flex;
            align-items: center;
            gap: 15px;
        }

        .bar-label {
            min-width: 150px;
            font-weight: 600;
            color: #555;
        }

        .bar-container {
            flex: 1;
            background: #e0e0e0;
            border-radius: 10px;
            height: 30px;
            position: relative;
            overflow: hidden;
        }

        .bar-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            border-radius: 10px;
            transition: width 0.5s ease;
            display: flex;
            align-items: center;
            justify-content: flex-end;
            padding: 0 10px;
            color: white;
            font-weight: bold;
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }

        .stat-item {
            background: #f5f7fa;
            padding: 15px;
            border-radius: 8px;
            border-right: 4px solid #667eea;
        }

        .stat-label {
            font-size: 0.9em;
            color: #666;
            margin-bottom: 5px;
        }

        .stat-value {
            font-size: 1.3em;
            font-weight: bold;
            color: #333;
        }

        .footer {
            text-align: center;
            padding: 20px;
            background: #f5f7fa;
            color: #666;
            font-size: 0.9em;
        }

        .no-data {
            text-align: center;
            padding: 60px 20px;
            color: #999;
            font-size: 1.3em;
        }

        @media print {
            body {
                background: white;
                padding: 0;
            }
            .container {
                box-shadow: none;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>דוח הוצאות חודשי</h1>
            <p>{{ report.month_name }} {{ report.year }}</p>
        </div>

        <div class="content">
            {% if report.has_data %}
                <!-- Summary Cards -->
                <div class="summary-cards">
                    {% if report.income %}
                    <div class="card income">
                        <div class="card-label">הכנסות</div>
                        <div class="card-value">₪{{ "%.2f"|format(report.income) }}</div>
                    </div>
                    {% endif %}

                    <div class="card expenses">
                        <div class="card-label">הוצאות</div>
                        <div class="card-value">₪{{ "%.2f"|format(report.total_expenses) }}</div>
                    </div>

                    {% if report.savings is not none %}
                    <div class="card {{ 'positive' if report.savings > 0 else 'negative' }}">
                        <div class="card-label">חיסכון</div>
                        <div class="card-value">₪{{ "%.2f"|format(report.savings) }}</div>
                        {% if report.savings_rate %}
                        <div style="font-size: 0.9em; margin-top: 5px;">{{ "%.1f"|format(report.savings_rate) }}%</div>
                        {% endif %}
                    </div>
                    {% endif %}

                    <div class="card">
                        <div class="card-label">עסקאות</div>
                        <div class="card-value">{{ report.stats.total_transactions }}</div>
                    </div>
                </div>

                <!-- Category Breakdown -->
                <div class="section">
                    <h2 class="section-title">פילוח לפי קטגוריות</h2>
                    <div class="chart-container">
                        <div class="bar-chart">
                            {% set max_amount = report.category_summary.values()|map(attribute='סכום')|max %}
                            {% for category, data in report.category_summary.items() %}
                            <div class="bar-item">
                                <div class="bar-label">{{ category }}</div>
                                <div class="bar-container">
                                    <div class="bar-fill" style="width: {{ (data['סכום'] / max_amount * 100)|round }}%">
                                        ₪{{ "%.2f"|format(data['סכום']) }}
                                    </div>
                                </div>
                            </div>
                            {% endfor %}
                        </div>
                    </div>

                    <table>
                        <thead>
                            <tr>
                                <th>קטגוריה</th>
                                <th>סכום</th>
                                <th>מספר עסקאות</th>
                                <th>ממוצע לעסקה</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for category, data in report.category_summary.items() %}
                            <tr>
                                <td>{{ category }}</td>
                                <td class="amount">₪{{ "%.2f"|format(data['סכום']) }}</td>
                                <td>{{ data['כמות עסקאות'] }}</td>
                                <td>₪{{ "%.2f"|format(data['סכום'] / data['כמות עסקאות']) }}</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>

                <!-- Statistics -->
                <div class="section">
                    <h2 class="section-title">סטטיסטיקות</h2>
                    <div class="stats-grid">
                        <div class="stat-item">
                            <div class="stat-label">ממוצע לעסקה</div>
                            <div class="stat-value">₪{{ "%.2f"|format(report.stats.average_transaction) }}</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-label">חציון</div>
                            <div class="stat-value">₪{{ "%.2f"|format(report.stats.median_transaction) }}</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-label">הוצאה מקסימלית</div>
                            <div class="stat-value">₪{{ "%.2f"|format(report.stats.max_transaction) }}</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-label">הוצאה מינימלית</div>
                            <div class="stat-value">₪{{ "%.2f"|format(report.stats.min_transaction) }}</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-label">ימים עם הוצאות</div>
                            <div class="stat-value">{{ report.stats.days_with_spending }}</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-label">ממוצע יומי</div>
                            <div class="stat-value">₪{{ "%.2f"|format(report.stats.average_daily_spending) }}</div>
                        </div>
                    </div>
                </div>

                <!-- Top Expenses -->
                {% if report.top_expenses %}
                <div class="section">
                    <h2 class="section-title">10 ההוצאות הגדולות ביותר</h2>
                    <table>
                        <thead>
                            <tr>
                                <th>תאריך</th>
                                <th>בית עסק</th>
                                <th>קטגוריה</th>
                                <th>סכום</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for expense in report.top_expenses %}
                            <tr>
                                <td>{{ expense.purchase_date.strftime('%d/%m/%Y') if expense.purchase_date.strftime else expense.purchase_date }}</td>
                                <td>{{ expense.business_name }}</td>
                                <td>{{ expense.category }}</td>
                                <td class="amount">₪{{ "%.2f"|format(expense.billing_amount) }}</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
                {% endif %}

                <!-- Additional Expenses -->
                {% if report.additional_expenses %}
                <div class="section">
                    <h2 class="section-title">הוצאות נוספות</h2>
                    <table>
                        <thead>
                            <tr>
                                <th>תיאור</th>
                                <th>קטגוריה</th>
                                <th>סכום</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for expense in report.additional_expenses %}
                            <tr>
                                <td>{{ expense.description }}</td>
                                <td>{{ expense.category }}</td>
                                <td class="amount">₪{{ "%.2f"|format(expense.amount) }}</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
                {% endif %}

            {% else %}
                <div class="no-data">
                    אין נתונים עבור {{ report.month_name }} {{ report.year }}
                </div>
            {% endif %}
        </div>

        <div class="footer">
            נוצר בתאריך: {{ generated_date.strftime('%d/%m/%Y %H:%M') }}
        </div>
    </div>
</body>
</html>
        '''

        return Template(template_str)
