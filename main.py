"""
Main Expense Tracker - Process credit card files and generate reports
"""
import os
import sys
import json
from datetime import datetime
from expense_processor import ExpenseProcessor
from database import ExpenseDatabase
from report_generator import ReportGenerator
from html_generator import HTMLGenerator
from dashboard_generator import DashboardGenerator

# Fix Windows console encoding for Hebrew text
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')


class ExpenseTracker:
    def __init__(self):
        # Load configuration
        with open('config.json', 'r', encoding='utf-8') as f:
            self.config = json.load(f)

        self.processor = ExpenseProcessor()
        self.db = ExpenseDatabase(self.config['database_file'])
        self.report_gen = ReportGenerator(self.db)
        self.html_gen = HTMLGenerator()
        self.dashboard_gen = DashboardGenerator(self.db, self.report_gen)

    def process_new_files(self):
        """
        Process new files from input folder
        """
        input_folder = self.config['input_folder']

        if not os.path.exists(input_folder):
            print(f"Input folder '{input_folder}' does not exist!")
            return

        print("\n" + "="*60)
        print("Processing Credit Card Files")
        print("="*60 + "\n")

        new_files_processed = 0
        skipped_files = 0

        for filename in os.listdir(input_folder):
            if filename.endswith(('.xlsx', '.xls')) and not filename.startswith('~'):
                file_path = os.path.join(input_folder, filename)

                # Check if already processed
                if self.db.is_file_processed(filename):
                    print(f"⊘ {filename} - Already processed, skipping")
                    skipped_files += 1
                    continue

                try:
                    print(f"\nProcessing: {filename}")
                    print("-" * 60)

                    # Process the file
                    df = self.processor.process_file(file_path)
                    print(f"  ✓ Read {len(df)} transactions")

                    # Add to database
                    new_records = self.db.add_expenses(df)
                    print(f"  ✓ Added {new_records} new records to database")

                    # Mark file as processed
                    self.db.mark_file_processed(filename, len(df))

                    new_files_processed += 1

                except Exception as e:
                    print(f"  ✗ Error: {str(e)}")

        print("\n" + "="*60)
        print(f"Summary: {new_files_processed} new files processed, {skipped_files} skipped")
        print("="*60 + "\n")

    def set_monthly_income(self, year: int, month: int, amount: float, notes: str = ""):
        """
        Set monthly income
        """
        self.db.set_monthly_income(year, month, amount, notes)
        print(f"✓ Set income for {month}/{year}: ₪{amount:,.2f}")

    def add_additional_expense(self, year: int, month: int, description: str,
                              amount: float, category: str = "אחר"):
        """
        Add additional expense (not from credit card)
        """
        self.db.add_additional_expense(year, month, description, amount, category)
        print(f"✓ Added expense: {description} - ₪{amount:,.2f}")

    def generate_monthly_report(self, year: int = None, month: int = None):
        """
        Generate report for a specific month (defaults to current month)
        """
        if year is None or month is None:
            now = datetime.now()
            year = year or now.year
            month = month or now.month

        print(f"\nGenerating report for {month}/{year}...")

        # Generate report data
        report = self.report_gen.generate_monthly_report(year, month)

        if not report['has_data']:
            print(f"No data available for {month}/{year}")
            return

        # Create reports folder if it doesn't exist
        output_folder = self.config['output_folder']
        os.makedirs(output_folder, exist_ok=True)

        # Generate HTML report
        html_filename = f"report_{year}_{month:02d}.html"
        html_path = os.path.join(output_folder, html_filename)
        self.html_gen.generate_html_report(report, html_path)

        # Generate Excel report
        excel_filename = f"report_{year}_{month:02d}.xlsx"
        excel_path = os.path.join(output_folder, excel_filename)
        self.report_gen.export_to_excel(year, month, excel_path)

        # Print summary
        print("\n" + "="*60)
        print(f"Monthly Report - {report['month_name']} {year}")
        print("="*60)

        if report['income']:
            print(f"הכנסות:           ₪{report['income']:,.2f}")
        print(f"הוצאות כרטיס אשראי: ₪{report['total_cc_expenses']:,.2f}")
        if report['total_additional_expenses'] > 0:
            print(f"הוצאות נוספות:     ₪{report['total_additional_expenses']:,.2f}")
        print(f"סך הכל הוצאות:     ₪{report['total_expenses']:,.2f}")

        if report['savings'] is not None:
            savings_symbol = "+" if report['savings'] > 0 else ""
            print(f"חיסכון:            {savings_symbol}₪{report['savings']:,.2f} ({report['savings_rate']:.1f}%)")

        print("\nפילוח לפי קטגוריות:")
        print("-" * 60)
        for category, data in sorted(report['category_summary'].items(),
                                     key=lambda x: x[1]['סכום'], reverse=True):
            print(f"  {category:20s} ₪{data['סכום']:>10,.2f}  ({int(data['כמות עסקאות'])} עסקאות)")

        print("\n" + "="*60)
        print(f"Reports saved:")
        print(f"  - HTML: {html_path}")
        print(f"  - Excel: {excel_path}")
        print("="*60 + "\n")

    def list_available_months(self):
        """
        List all months with data
        """
        months = self.db.get_available_months()

        if not months:
            print("No data available yet.")
            return

        print("\nAvailable months with data:")
        print("-" * 40)
        for year, month in months:
            month_name = self.report_gen._get_hebrew_month(month)
            print(f"  {month_name} {year} ({month}/{year})")

    def interactive_menu(self):
        """
        Interactive menu for user
        """
        while True:
            print("\n" + "="*60)
            print("מערכת מעקב הוצאות - Expense Tracker")
            print("="*60)
            print("1. Process new credit card files")
            print("2. Set monthly income")
            print("3. Add additional expense")
            print("4. Generate monthly report")
            print("5. Generate full dashboard (all months)")
            print("6. List available months")
            print("7. Exit")
            print("="*60)

            choice = input("\nEnter choice (1-7): ").strip()

            if choice == '1':
                self.process_new_files()

            elif choice == '2':
                try:
                    year = int(input("Enter year (e.g., 2024): "))
                    month = int(input("Enter month (1-12): "))
                    amount = float(input("Enter income amount: "))
                    notes = input("Notes (optional): ")
                    self.set_monthly_income(year, month, amount, notes)
                except ValueError:
                    print("Invalid input!")

            elif choice == '3':
                try:
                    year = int(input("Enter year (e.g., 2024): "))
                    month = int(input("Enter month (1-12): "))
                    description = input("Description: ")
                    amount = float(input("Amount: "))
                    category = input("Category (or press Enter for 'אחר'): ") or "אחר"
                    self.add_additional_expense(year, month, description, amount, category)
                except ValueError:
                    print("Invalid input!")

            elif choice == '4':
                try:
                    print("\nPress Enter to use current month or specify:")
                    year_input = input("Year (e.g., 2024): ").strip()
                    month_input = input("Month (1-12): ").strip()

                    year = int(year_input) if year_input else None
                    month = int(month_input) if month_input else None

                    self.generate_monthly_report(year, month)
                except ValueError:
                    print("Invalid input!")

            elif choice == '5':
                try:
                    print("\nGenerating full dashboard...")
                    print("Enter fixed monthly amounts:")
                    income_input = input("Fixed monthly income (default 11747): ").strip()
                    expense_input = input("Fixed monthly expenses (default 4400): ").strip()

                    fixed_income = float(income_input) if income_input else 11747
                    fixed_expenses = float(expense_input) if expense_input else 4400

                    output_folder = self.config['output_folder']
                    os.makedirs(output_folder, exist_ok=True)
                    output_path = os.path.join(output_folder, 'dashboard.html')

                    self.dashboard_gen.generate_dashboard(output_path, fixed_income, fixed_expenses)
                    print(f"\n✓ Dashboard ready! Open: {output_path}")
                except ValueError:
                    print("Invalid input!")

            elif choice == '6':
                self.list_available_months()

            elif choice == '7':
                print("\nGoodbye!")
                break

            else:
                print("Invalid choice!")


def main():
    """
    Main entry point
    """
    tracker = ExpenseTracker()

    # Check if there are command line arguments
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == 'process':
            tracker.process_new_files()

        elif command == 'report':
            year = int(sys.argv[2]) if len(sys.argv) > 2 else None
            month = int(sys.argv[3]) if len(sys.argv) > 3 else None
            tracker.generate_monthly_report(year, month)

        elif command == 'list':
            tracker.list_available_months()

        elif command == 'dashboard':
            fixed_income = float(sys.argv[2]) if len(sys.argv) > 2 else 11747
            fixed_expenses = float(sys.argv[3]) if len(sys.argv) > 3 else 4400
            output_folder = tracker.config['output_folder']
            os.makedirs(output_folder, exist_ok=True)
            output_path = os.path.join(output_folder, 'dashboard.html')
            tracker.dashboard_gen.generate_dashboard(output_path, fixed_income, fixed_expenses)

        else:
            print("Unknown command. Available commands: process, report, list, dashboard")

    else:
        # Interactive mode
        tracker.interactive_menu()


if __name__ == "__main__":
    main()
