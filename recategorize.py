"""
Recategorize all expenses in the database based on updated config
"""
import sys
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

from database import ExpenseDatabase
from expense_processor import ExpenseProcessor

db = ExpenseDatabase()
processor = ExpenseProcessor()

# Get all expenses
df = db.get_all_expenses()
print(f"Found {len(df)} total expenses in database")
print("Recategorizing...")

# Recategorize
df['category'] = df['business_name'].apply(processor.categorize_expense)

# Update database
conn = db.get_connection()
for idx, row in df.iterrows():
    conn.execute(
        'UPDATE expenses SET category = ? WHERE id = ?',
        (row['category'], row['id'])
    )

conn.commit()
conn.close()

print("✓ Recategorization complete!")

# Show summary
from collections import Counter
category_counts = Counter(df['category'])
print("\nNew category distribution:")
for category, count in sorted(category_counts.items(), key=lambda x: -x[1]):
    print(f"  {category:25s} {count:3d} transactions")
