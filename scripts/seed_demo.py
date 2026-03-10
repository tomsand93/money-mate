"""
Create a small demo SQLite database with fake expenses for testing and demos.
Usage: python scripts/seed_demo.py
"""
import sqlite3
from datetime import datetime
import os

DB = os.environ.get('DATABASE_FILE', 'expenses.db')

def seed():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    # Create tables by executing the app's DB init logic using a minimal set of queries
    cur.execute('''
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        purchase_date DATE NOT NULL,
        business_name TEXT,
        billing_amount REAL NOT NULL,
        category TEXT NOT NULL,
        source_file TEXT,
        processed_date TIMESTAMP
    )
    ''')

    cur.execute('''
    CREATE TABLE IF NOT EXISTS monthly_income (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        year INTEGER NOT NULL,
        month INTEGER NOT NULL,
        income_amount REAL NOT NULL
    )
    ''')

    # Insert demo income
    cur.execute("INSERT OR REPLACE INTO monthly_income (id, year, month, income_amount) VALUES (1, 2025, 11, 12000)")

    # Insert demo expenses
    demo = [
        ('2025-11-05', 'SuperMarket LTD', 300.5, 'סופרמרקט'),
        ('2025-11-08', 'Coffee Place', 25.0, 'אוכל בחוץ'),
        ('2025-11-12', 'Electric Co', 120.0, 'חשבונות ומנויים'),
        ('2025-11-18', 'Cinema', 50.0, 'בילויים'),
        ('2025-11-21', 'Amazon', 150.0, 'קניות אונליין')
    ]

    for d in demo:
        cur.execute('INSERT INTO expenses (purchase_date, business_name, billing_amount, category, source_file, processed_date) VALUES (?, ?, ?, ?, ?, ?)',
                    (d[0], d[1], d[2], d[3], 'demo', datetime.now()))

    conn.commit()
    conn.close()
    print('Seeded demo DB at:', DB)

if __name__ == '__main__':
    seed()
