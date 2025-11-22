"""
Dashboard Generator - Creates a comprehensive multi-month HTML dashboard
"""
from jinja2 import Template
from datetime import datetime
from typing import Dict, List
from database import ExpenseDatabase
from report_generator import ReportGenerator


class DashboardGenerator:
    def __init__(self, db: ExpenseDatabase, report_gen: ReportGenerator):
        self.db = db
        self.report_gen = report_gen

    def generate_dashboard(self, output_path: str, fixed_income: float = 11747, fixed_expenses: float = 4400):
        """
        Generate comprehensive dashboard with all months
        """
        # Get all available months
        available_months = self.db.get_available_months()

        if not available_months:
            print("No data available to generate dashboard")
            return

        # Generate reports for all months
        monthly_reports = []
        total_income = 0
        total_expenses = 0
        total_savings = 0

        for year, month in available_months:
            report = self.report_gen.generate_monthly_report(year, month)
            if report['has_data']:
                # Add fixed income/expenses
                monthly_income = report['income'] or fixed_income
                monthly_expenses = report['total_expenses'] + fixed_expenses
                monthly_savings = monthly_income - monthly_expenses

                report['fixed_income'] = fixed_income
                report['fixed_expenses'] = fixed_expenses
                report['total_income_with_fixed'] = monthly_income
                report['total_expenses_with_fixed'] = monthly_expenses
                report['savings_with_fixed'] = monthly_savings
                report['savings_rate_with_fixed'] = (monthly_savings / monthly_income * 100) if monthly_income > 0 else 0

                monthly_reports.append(report)
                total_income += monthly_income
                total_expenses += monthly_expenses
                total_savings += monthly_savings

        # Calculate overall summary
        summary = {
            'total_income': total_income,
            'total_expenses': total_expenses,
            'total_savings': total_savings,
            'average_monthly_income': total_income / len(monthly_reports) if monthly_reports else 0,
            'average_monthly_expenses': total_expenses / len(monthly_reports) if monthly_reports else 0,
            'average_savings_rate': (total_savings / total_income * 100) if total_income > 0 else 0,
            'months_count': len(monthly_reports),
            'fixed_income': fixed_income,
            'fixed_expenses': fixed_expenses
        }

        # Generate HTML
        template = self._get_template()

        # Add custom filter for number formatting with commas
        def format_currency(value):
            """Format number with thousand separators"""
            return "{:,.2f}".format(float(value))

        template.globals['format_currency'] = format_currency

        html_content = template.render(
            monthly_reports=monthly_reports,
            summary=summary,
            generated_date=datetime.now()
        )

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"✓ Dashboard generated: {output_path}")
        print(f"  - {len(monthly_reports)} months included")
        print(f"  - Total income: ₪{total_income:,.2f}")
        print(f"  - Total expenses: ₪{total_expenses:,.2f}")
        print(f"  - Total savings: ₪{total_savings:,.2f} ({summary['average_savings_rate']:.1f}%)")

    def _get_template(self) -> Template:
        """Get Jinja2 template for dashboard"""
        template_str = '''
<!DOCTYPE html>
<html dir="rtl" lang="he">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>דשבורד הוצאות - סקירה כללית</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            min-height: 100vh;
        }

        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
            position: sticky;
            top: 0;
            z-index: 100;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }

        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }

        .nav-tabs {
            display: flex;
            justify-content: center;
            flex-wrap: wrap;
            gap: 10px;
            margin-top: 20px;
            padding: 0 20px;
        }

        .nav-tab {
            background: rgba(255,255,255,0.2);
            color: white;
            border: 2px solid rgba(255,255,255,0.3);
            padding: 10px 20px;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s;
            font-weight: 600;
        }

        .nav-tab:hover {
            background: rgba(255,255,255,0.3);
            transform: translateY(-2px);
        }

        .nav-tab.active {
            background: white;
            color: #667eea;
            border-color: white;
        }

        .content {
            padding: 30px;
        }

        .month-section {
            display: none;
        }

        .month-section.active {
            display: block;
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

        .positive-amount {
            color: #4caf50;
        }

        .negative-amount {
            color: #f44336;
        }

        .bar-chart {
            display: flex;
            flex-direction: column;
            gap: 15px;
            margin: 20px 0;
            padding: 20px;
            background: #f5f7fa;
            border-radius: 10px;
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

        .overview-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }

        .overview-card {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }

        .month-comparison {
            width: 100%;
            margin: 20px 0;
        }

        .comparison-bar {
            display: flex;
            height: 40px;
            margin: 10px 0;
            border-radius: 8px;
            overflow: hidden;
        }

        .comparison-income {
            background: linear-gradient(90deg, #a8edea 0%, #fed6e3 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            color: #333;
            font-weight: bold;
        }

        .comparison-expenses {
            background: linear-gradient(90deg, #ffecd2 0%, #fcb69f 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            color: #333;
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

        .chart-container {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            margin-bottom: 30px;
            max-height: 400px;
        }

        .chart-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }

        .chart-container canvas {
            max-height: 350px;
        }

        @media print {
            body {
                background: white;
            }
            .nav-tabs {
                display: none;
            }
            .month-section {
                display: block !important;
                page-break-after: always;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>דשבורד הוצאות - סקירה כללית</h1>
            <p>מעקב פיננסי מלא</p>

            <div class="nav-tabs">
                <button class="nav-tab active" onclick="showSection('overview')">סקירה כללית</button>
                {% for report in monthly_reports %}
                <button class="nav-tab" onclick="showSection('month-{{ loop.index }}')">
                    {{ report.month_name }} {{ report.year }}
                </button>
                {% endfor %}
            </div>
        </div>

        <div class="content">
            <!-- Overview Section -->
            <div id="overview" class="month-section active">
                <h2 class="section-title">סיכום כולל - {{ summary.months_count }} חודשים</h2>

                <div class="summary-cards">
                    <div class="card income">
                        <div class="card-label">סך הכנסות</div>
                        <div class="card-value">₪{{ format_currency(summary.total_income) }}</div>
                    </div>

                    <div class="card expenses">
                        <div class="card-label">סך הוצאות</div>
                        <div class="card-value">₪{{ format_currency(summary.total_expenses) }}</div>
                    </div>

                    <div class="card {{ 'positive' if summary.total_savings > 0 else 'negative' }}">
                        <div class="card-label">סך חיסכון</div>
                        <div class="card-value">₪{{ format_currency(summary.total_savings) }}</div>
                        <div style="font-size: 0.9em; margin-top: 5px;">{{ "%.1f"|format(summary.average_savings_rate) }}%</div>
                    </div>

                    <div class="card">
                        <div class="card-label">ממוצע חודשי</div>
                        <div class="card-value">₪{{ format_currency(summary.average_monthly_expenses) }}</div>
                    </div>
                </div>

                <!-- Fixed Monthly Amounts -->
                <div class="section">
                    <h3 class="section-title">הוצאות קבועות חודשיות</h3>
                    <div class="summary-cards">
                        <div class="card income">
                            <div class="card-label">הכנסה קבועה</div>
                            <div class="card-value">₪{{ format_currency(summary.fixed_income) }}</div>
                        </div>
                        <div class="card expenses">
                            <div class="card-label">הוצאות קבועות</div>
                            <div class="card-value">₪{{ format_currency(summary.fixed_expenses) }}</div>
                        </div>
                    </div>
                </div>

                <!-- Monthly Comparison -->
                <div class="section">
                    <h3 class="section-title">השוואה בין חודשים</h3>
                    <table>
                        <thead>
                            <tr>
                                <th>חודש</th>
                                <th>הכנסות</th>
                                <th>הוצאות</th>
                                <th>חיסכון</th>
                                <th>% חיסכון</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for report in monthly_reports %}
                            <tr>
                                <td><strong>{{ report.month_name }} {{ report.year }}</strong></td>
                                <td class="amount">₪{{ format_currency(report.total_income_with_fixed) }}</td>
                                <td class="amount">₪{{ format_currency(report.total_expenses_with_fixed) }}</td>
                                <td class="amount {{ 'positive-amount' if report.savings_with_fixed > 0 else 'negative-amount' }}">
                                    ₪{{ format_currency(report.savings_with_fixed) }}
                                </td>
                                <td>{{ "%.1f"|format(report.savings_rate_with_fixed) }}%</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>

                <!-- Charts -->
                <div class="section">
                    <h3 class="section-title">גרפים</h3>

                    <div class="chart-container">
                        <canvas id="monthlyTrendChart"></canvas>
                    </div>

                    <div class="chart-grid">
                        <div class="chart-container">
                            <canvas id="categoryPieChart"></canvas>
                        </div>
                        <div class="chart-container">
                            <canvas id="categoryBarChart"></canvas>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Individual Month Sections -->
            {% for report in monthly_reports %}
            <div id="month-{{ loop.index }}" class="month-section">
                <h2 class="section-title">{{ report.month_name }} {{ report.year }}</h2>

                <div class="summary-cards">
                    <div class="card income">
                        <div class="card-label">הכנסות</div>
                        <div class="card-value">₪{{ format_currency(report.total_income_with_fixed) }}</div>
                        <div style="font-size: 0.8em; margin-top: 5px;">קבוע: ₪{{ format_currency(report.fixed_income) }}</div>
                    </div>

                    <div class="card expenses">
                        <div class="card-label">הוצאות</div>
                        <div class="card-value">₪{{ format_currency(report.total_expenses_with_fixed) }}</div>
                        <div style="font-size: 0.8em; margin-top: 5px;">כ.אשראי: ₪{{ format_currency(report.total_cc_expenses) }} | קבוע: ₪{{ format_currency(report.fixed_expenses) }}</div>
                    </div>

                    <div class="card {{ 'positive' if report.savings_with_fixed > 0 else 'negative' }}">
                        <div class="card-label">חיסכון</div>
                        <div class="card-value">₪{{ format_currency(report.savings_with_fixed) }}</div>
                        <div style="font-size: 0.9em; margin-top: 5px;">{{ "%.1f"|format(report.savings_rate_with_fixed) }}%</div>
                    </div>

                    <div class="card">
                        <div class="card-label">עסקאות</div>
                        <div class="card-value">{{ report.stats.total_transactions }}</div>
                    </div>
                </div>

                <!-- Category Charts -->
                <div class="section">
                    <h3 class="section-title">התפלגות הוצאות</h3>
                    <div class="chart-grid">
                        <div class="chart-container">
                            <canvas id="monthPieChart-{{ loop.index }}"></canvas>
                        </div>
                        <div class="chart-container">
                            <canvas id="monthBarChart-{{ loop.index }}"></canvas>
                        </div>
                    </div>
                </div>

                <!-- Category Breakdown -->
                <div class="section">
                    <h3 class="section-title">פילוח לפי קטגוריות</h3>
                    <div class="bar-chart">
                        {% set max_amount = report.category_summary.values()|map(attribute='סכום')|max %}
                        {% for category, data in report.category_summary.items() %}
                        <div class="bar-item">
                            <div class="bar-label">{{ category }}</div>
                            <div class="bar-container">
                                <div class="bar-fill" style="width: {{ (data['סכום'] / max_amount * 100)|round }}%">
                                    ₪{{ format_currency(data['סכום']) }}
                                </div>
                            </div>
                        </div>
                        {% endfor %}
                    </div>
                </div>

                <!-- Statistics -->
                <div class="section">
                    <h3 class="section-title">סטטיסטיקות</h3>
                    <div class="stats-grid">
                        <div class="stat-item">
                            <div class="stat-label">ממוצע לעסקה</div>
                            <div class="stat-value">₪{{ format_currency(report.stats.average_transaction) }}</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-label">הוצאה מקסימלית</div>
                            <div class="stat-value">₪{{ format_currency(report.stats.max_transaction) }}</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-label">ימים עם הוצאות</div>
                            <div class="stat-value">{{ report.stats.days_with_spending }}</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-label">ממוצע יומי</div>
                            <div class="stat-value">₪{{ format_currency(report.stats.average_daily_spending) }}</div>
                        </div>
                    </div>
                </div>

                <!-- Top Expenses -->
                {% if report.top_expenses %}
                <div class="section">
                    <h3 class="section-title">10 ההוצאות הגדולות</h3>
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
                                <td class="amount">₪{{ format_currency(expense.billing_amount) }}</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
                {% endif %}

                <!-- All Transactions -->
                {% if report.all_transactions %}
                <div class="section">
                    <h3 class="section-title">כל ההוצאות ({{ report.all_transactions|length }} עסקאות)</h3>
                    <div style="margin-bottom: 15px;">
                        <input type="text" id="search-{{ loop.index }}" placeholder="חפש בית עסק או קטגוריה..."
                               style="width: 100%; padding: 10px; border: 2px solid #667eea; border-radius: 5px; font-size: 1em;"
                               onkeyup="filterTable({{ loop.index }})">
                    </div>
                    <div style="max-height: 500px; overflow-y: auto;">
                        <table id="table-{{ loop.index }}">
                            <thead style="position: sticky; top: 0;">
                                <tr>
                                    <th>תאריך</th>
                                    <th>בית עסק</th>
                                    <th>קטגוריה</th>
                                    <th>סכום</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for expense in report.all_transactions %}
                                <tr>
                                    <td>{{ expense.purchase_date.strftime('%d/%m/%Y') if expense.purchase_date.strftime else expense.purchase_date }}</td>
                                    <td>{{ expense.business_name }}</td>
                                    <td>{{ expense.category }}</td>
                                    <td class="amount">₪{{ format_currency(expense.billing_amount) }}</td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                </div>
                {% endif %}
            </div>
            {% endfor %}
        </div>

        <div style="text-align: center; padding: 20px; background: #f5f7fa; color: #666; font-size: 0.9em;">
            נוצר בתאריך: {{ generated_date.strftime('%d/%m/%Y %H:%M') }}
        </div>
    </div>

    <script>
        function showSection(sectionId) {
            // Hide all sections
            document.querySelectorAll('.month-section').forEach(section => {
                section.classList.remove('active');
            });

            // Remove active class from all tabs
            document.querySelectorAll('.nav-tab').forEach(tab => {
                tab.classList.remove('active');
            });

            // Show selected section
            document.getElementById(sectionId).classList.add('active');

            // Activate clicked tab
            event.target.classList.add('active');

            // Scroll to top
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }

        function filterTable(monthIndex) {
            const input = document.getElementById('search-' + monthIndex);
            const filter = input.value.toLowerCase();
            const table = document.getElementById('table-' + monthIndex);
            const rows = table.getElementsByTagName('tbody')[0].getElementsByTagName('tr');

            for (let row of rows) {
                const businessName = row.cells[1].textContent.toLowerCase();
                const category = row.cells[2].textContent.toLowerCase();

                if (businessName.includes(filter) || category.includes(filter)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            }
        }

        // Initialize charts when page loads
        document.addEventListener('DOMContentLoaded', function() {
            initializeCharts();
        });

        function initializeCharts() {
            // Prepare data
            const monthLabels = [{% for report in monthly_reports %}'{{ report.month_name }} {{ report.year }}'{{ ', ' if not loop.last else '' }}{% endfor %}];
            const incomeData = [{% for report in monthly_reports %}{{ report.total_income_with_fixed }}{{ ', ' if not loop.last else '' }}{% endfor %}];
            const expenseData = [{% for report in monthly_reports %}{{ report.total_expenses_with_fixed }}{{ ', ' if not loop.last else '' }}{% endfor %}];
            const savingsData = [{% for report in monthly_reports %}{{ report.savings_with_fixed }}{{ ', ' if not loop.last else '' }}{% endfor %}];

            // Aggregate category data across all months
            const categoryTotals = {};
            {% for report in monthly_reports %}
                {% for category, data in report.category_summary.items() %}
                    if (!categoryTotals['{{ category }}']) {
                        categoryTotals['{{ category }}'] = 0;
                    }
                    categoryTotals['{{ category }}'] += {{ data['סכום'] }};
                {% endfor %}
            {% endfor %}

            const categoryLabels = Object.keys(categoryTotals);
            const categoryValues = Object.values(categoryTotals);

            // Color palette
            const colors = [
                '#667eea', '#764ba2', '#f093fb', '#4facfe',
                '#43e97b', '#fa709a', '#fee140', '#30cfd0',
                '#a8edea', '#fed6e3', '#ff6b6b', '#4ecdc4'
            ];

            // 1. Monthly Trend Chart (Line)
            const trendCtx = document.getElementById('monthlyTrendChart').getContext('2d');
            new Chart(trendCtx, {
                type: 'line',
                data: {
                    labels: monthLabels,
                    datasets: [
                        {
                            label: 'הכנסות',
                            data: incomeData,
                            borderColor: '#43e97b',
                            backgroundColor: 'rgba(67, 233, 123, 0.1)',
                            tension: 0.4,
                            fill: true
                        },
                        {
                            label: 'הוצאות',
                            data: expenseData,
                            borderColor: '#fa709a',
                            backgroundColor: 'rgba(250, 112, 154, 0.1)',
                            tension: 0.4,
                            fill: true
                        },
                        {
                            label: 'חיסכון',
                            data: savingsData,
                            borderColor: '#667eea',
                            backgroundColor: 'rgba(102, 126, 234, 0.1)',
                            tension: 0.4,
                            fill: true
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        title: {
                            display: true,
                            text: 'מגמות חודשיות - הכנסות, הוצאות וחיסכון',
                            font: { size: 16 }
                        },
                        legend: {
                            position: 'top',
                            rtl: true
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                callback: function(value) {
                                    return '₪' + value.toLocaleString();
                                }
                            }
                        }
                    }
                }
            });

            // 2. Category Pie Chart
            const pieCtx = document.getElementById('categoryPieChart').getContext('2d');
            new Chart(pieCtx, {
                type: 'pie',
                data: {
                    labels: categoryLabels,
                    datasets: [{
                        data: categoryValues,
                        backgroundColor: colors.slice(0, categoryLabels.length)
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        title: {
                            display: true,
                            text: 'התפלגות הוצאות לפי קטגוריות',
                            font: { size: 14 }
                        },
                        legend: {
                            position: 'right',
                            rtl: true,
                            labels: {
                                font: { size: 11 }
                            }
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const label = context.label || '';
                                    const value = context.parsed || 0;
                                    const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                    const percentage = ((value / total) * 100).toFixed(1);
                                    return label + ': ₪' + value.toLocaleString() + ' (' + percentage + '%)';
                                }
                            }
                        }
                    }
                }
            });

            // 3. Category Bar Chart
            const barCtx = document.getElementById('categoryBarChart').getContext('2d');
            new Chart(barCtx, {
                type: 'bar',
                data: {
                    labels: categoryLabels,
                    datasets: [{
                        label: 'סכום הוצאות',
                        data: categoryValues,
                        backgroundColor: colors.slice(0, categoryLabels.length)
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        title: {
                            display: true,
                            text: 'הוצאות לפי קטגוריות',
                            font: { size: 14 }
                        },
                        legend: {
                            display: false
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                callback: function(value) {
                                    return '₪' + value.toLocaleString();
                                }
                            }
                        }
                    }
                }
            });

            // 4. Individual Month Pie Charts
            {% for report in monthly_reports %}
            const monthCategories{{ loop.index }} = [{% for category, data in report.category_summary.items() %}'{{ category }}'{{ ', ' if not loop.last else '' }}{% endfor %}];
            const monthValues{{ loop.index }} = [{% for category, data in report.category_summary.items() %}{{ data['סכום'] }}{{ ', ' if not loop.last else '' }}{% endfor %}];

            const monthPieCtx{{ loop.index }} = document.getElementById('monthPieChart-{{ loop.index }}').getContext('2d');
            new Chart(monthPieCtx{{ loop.index }}, {
                type: 'pie',
                data: {
                    labels: monthCategories{{ loop.index }},
                    datasets: [{
                        data: monthValues{{ loop.index }},
                        backgroundColor: colors.slice(0, monthCategories{{ loop.index }}.length)
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        title: {
                            display: true,
                            text: 'התפלגות הוצאות - {{ report.month_name }} {{ report.year }}',
                            font: { size: 14 }
                        },
                        legend: {
                            position: 'right',
                            rtl: true,
                            labels: {
                                font: { size: 11 }
                            }
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const label = context.label || '';
                                    const value = context.parsed || 0;
                                    const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                    const percentage = ((value / total) * 100).toFixed(1);
                                    return label + ': ₪' + value.toLocaleString() + ' (' + percentage + '%)';
                                }
                            }
                        }
                    }
                }
            });

            // Monthly Bar Chart for month {{ loop.index }}
            const monthBarCtx{{ loop.index }} = document.getElementById('monthBarChart-{{ loop.index }}').getContext('2d');
            new Chart(monthBarCtx{{ loop.index }}, {
                type: 'bar',
                data: {
                    labels: monthCategories{{ loop.index }},
                    datasets: [{
                        label: 'סכום הוצאות',
                        data: monthValues{{ loop.index }},
                        backgroundColor: colors.slice(0, monthCategories{{ loop.index }}.length)
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        title: {
                            display: true,
                            text: 'הוצאות לפי קטגוריות - {{ report.month_name }} {{ report.year }}',
                            font: { size: 14 }
                        },
                        legend: {
                            display: false
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                callback: function(value) {
                                    return '₪' + value.toLocaleString();
                                }
                            }
                        }
                    }
                }
            });
            {% endfor %}
        }
    </script>
</body>
</html>
        '''
        return Template(template_str)
