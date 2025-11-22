# Dashboard Guide - מדריך לוח המחוונים

## 🎉 New Feature: Interactive Multi-Month Dashboard!

Instead of separate HTML files for each month, you now have a **single interactive dashboard** where you can navigate between all months and see an overall summary!

## 📊 What's Included

### Overview Tab (סקירה כללית)
- **Total Summary**: Income, expenses, and savings across ALL months
- **Fixed Monthly Amounts**: Your fixed income (₪11,747) and fixed expenses (₪4,400)
- **Month Comparison Table**: Side-by-side comparison of all months
- **Average Savings Rate**: Track your financial progress

### Individual Month Tabs
- Click any month to see detailed breakdown
- Category spending with visual charts
- Top 10 biggest expenses
- Statistics (average, max, days with spending)
- All the same info as before, but in one place!

## 🚀 How to Generate Dashboard

### Method 1: Command Line (Quick)
```bash
python main.py dashboard
```

Uses default values:
- Fixed income: ₪11,747
- Fixed expenses: ₪4,400

### Method 2: Command Line (Custom Values)
```bash
python main.py dashboard [income] [expenses]
```

Example:
```bash
python main.py dashboard 12000 5000
```

### Method 3: Interactive Menu
```bash
python main.py
# Choose option 5
# Enter your fixed income and expenses
```

## 📁 Output Location

The dashboard is saved as:
```
reports/dashboard.html
```

Open it in any modern web browser (Chrome, Firefox, Edge, Safari)

## 💡 Features

### Navigation
- **Tabs at the top**: Click to switch between overview and individual months
- **Sticky header**: Navigation stays visible as you scroll
- **Smooth transitions**: Professional animations

### Overview Summary Shows:
- ✅ Total income across all months
- ✅ Total expenses (credit card + fixed)
- ✅ Total savings and savings rate %
- ✅ Average monthly spending
- ✅ Month-by-month comparison table

### Each Month Shows:
- Income (with fixed income breakdown)
- Expenses (credit card + fixed, separated)
- Savings with percentage
- Category breakdown with colorful bar charts
- Statistics (average, max, days with spending, daily average)
- Top 10 biggest expenses

## 📈 Your Current Summary

Based on your data (11 months):
- **Total Income**: ₪129,217
- **Total Expenses**: ₪63,772
- **Total Savings**: ₪65,445 (50.6%)
- **Average Monthly Expenses**: ₪5,797

That's amazing! You're saving over 50% of your income! 🎊

## 🔄 Updating the Dashboard

Every time you:
1. Process new credit card files
2. Add additional expenses
3. Update income

Run the dashboard generator again to see updated numbers:
```bash
python main.py dashboard
```

The file will be overwritten with the latest data.

## 🎨 Visual Features

- **Color-coded cards**: Green for savings, blue for income, orange for expenses
- **Interactive bar charts**: Visual category spending
- **Responsive design**: Works on desktop, tablet, and mobile
- **Print-friendly**: Use browser print to create PDF reports

## 💰 About Fixed Amounts

### Fixed Income (₪11,747)
This is your regular monthly income that gets added to each month automatically.

### Fixed Expenses (₪4,400)
These are expenses not captured by credit card:
- Rent
- Cash payments
- Bank transfers
- Other regular monthly costs

The dashboard calculates:
- **Total Income** = Credit card tracked + Fixed income
- **Total Expenses** = Credit card expenses + Fixed expenses
- **Savings** = Total Income - Total Expenses

## 🔧 Customization

You can change the fixed amounts anytime:

**Via Command Line:**
```bash
python main.py dashboard 12000 5000
```

**Via Interactive Menu:**
```bash
python main.py
# Option 5
# Enter your amounts
```

## 📊 Example Use Cases

### Monthly Review
1. Generate dashboard at end of month
2. Check savings rate
3. Look for spending trends
4. Identify high-expense months

### Budget Planning
1. Compare months to see patterns
2. Identify categories to reduce
3. Set goals based on best months

### Annual Review
1. See full year summary
2. Calculate total savings
3. Plan for next year

---

**Enjoy your new interactive dashboard!** 🎉

Open `reports/dashboard.html` in your browser now!
