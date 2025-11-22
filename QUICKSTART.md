# Quick Start Guide - תחילת עבודה מהירה

## Setup (פעם אחת בלבד)

### 1. Install Python Dependencies
```bash
pip install -r requirements.txt
```

That's it! The system is ready to use.

---

## Monthly Workflow (זרימת עבודה חודשית)

### Step 1: Download Your Credit Card Statements

Download Excel files from your credit card company:
- Go to your credit card website
- Download transactions for the month
- Save the Excel file

### Step 2: Place Files in Input Folder

```bash
# Copy your Excel files to:
input_files/
```

Example:
```
input_files/
  ├── leumi_card_november_2024.xlsx
  ├── isracard_november_2024.xlsx
  └── cal_november_2024.xlsx
```

### Step 3: Run the Tracker

```bash
python main.py
```

Choose option `1` to process new files.

### Step 4: Set Monthly Income

In the interactive menu, choose option `2`:
- Enter year: `2024`
- Enter month: `11`
- Enter income amount: `15000`
- Notes: `Monthly salary`

### Step 5: Add Additional Expenses (Optional)

If you have cash expenses or bank transfers, choose option `3`:
- Enter year: `2024`
- Enter month: `11`
- Description: `Rent payment`
- Amount: `4500`
- Category: `חשבונות וחיובים`

### Step 6: Generate Report

Choose option `4` in the menu, or:

```bash
python main.py report
```

### Step 7: View Your Report

Open the HTML file in your browser:
```
reports/report_2024_11.html
```

You'll see:
- Beautiful dashboard with your spending
- Category breakdown with charts
- Top 10 expenses
- Savings calculation
- Statistics and insights

---

## Quick Command Reference

```bash
# Process new files only
python main.py process

# Generate report for current month
python main.py report

# Generate report for specific month
python main.py report 2024 11

# List all available months
python main.py list

# Interactive menu (recommended for beginners)
python main.py
```

---

## First Time Users

1. **Test with sample data**: Create a simple Excel file with a few transactions
2. **Check categorization**: Look at [config.json](config.json) and add your frequent stores
3. **Run a test**: Process one file and generate a report
4. **Adjust categories**: Update config.json based on "אחר" (Other) category items

---

## Pro Tips

### Customize Categories

Edit [config.json](config.json):

```json
{
  "categories": {
    "Your Category": ["keyword1", "keyword2", "partial name"]
  }
}
```

The system searches for these keywords in the business name.

### Monthly Routine

Set a reminder at the end of each month:
1. Download credit card statements
2. Place in `input_files/`
3. Run `python main.py`
4. Choose `1` (process), then `2` (set income), then `4` (generate report)
5. Review your spending in the HTML report

### Track Trends

Keep all monthly HTML reports and compare:
- Which categories are growing?
- Where can you save money?
- Are you meeting savings goals?

---

## Need Help?

Check [README.md](README.md) for detailed documentation.

Common issues:
- **"Missing columns"**: Make sure Excel has Hebrew column names
- **"Already processed"**: File was already added - this is normal
- **Category "אחר" too much**: Add more keywords to config.json

---

Enjoy tracking your expenses! 🎉
