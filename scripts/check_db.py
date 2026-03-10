import sqlite3, os, sys

DB = 'expenses.db'
print(f"Checking DB: {os.path.abspath(DB)}")
print('Exists:', os.path.exists(DB))

if not os.path.exists(DB):
    print('Database file not found.')
    sys.exit(0)

conn = sqlite3.connect(DB)
cur = conn.cursor()

tables = ['expenses', 'additional_expenses', 'monthly_income', 'fixed_expenses', 'processed_files']
for t in tables:
    try:
        cur.execute(f"SELECT COUNT(*) FROM {t}")
        c = cur.fetchone()[0]
    except Exception as e:
        c = f'ERR: {e}'
    print(f"{t}: {c}")

# Show up to 5 latest expenses
try:
    cur.execute("SELECT id, purchase_date, business_name, billing_amount, category FROM expenses ORDER BY purchase_date DESC LIMIT 5")
    rows = cur.fetchall()
    print('\nLatest expenses (up to 5):')
    if not rows:
        print('  (none)')
    for r in rows:
        print(' ', r)
except Exception as e:
    print('Latest expenses error:', e)

conn.close()
