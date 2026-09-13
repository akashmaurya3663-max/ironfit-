import sqlite3
from app import init_db

init_db()
conn = sqlite3.connect('gym_members.db')
count = conn.execute('SELECT COUNT(*) FROM members').fetchone()[0]
expiring = conn.execute("SELECT COUNT(*) FROM members WHERE expiry_date BETWEEN date('now') AND date('now', '+7 days')").fetchone()[0]
plans = conn.execute('SELECT plan, COUNT(*) FROM members GROUP BY plan ORDER BY plan').fetchall()
print(f'TOTAL_MEMBERS {count}')
print(f'EXPIRING_SOON {expiring}')
print(f'PLAN_BREAKDOWN {plans}')
conn.close()
