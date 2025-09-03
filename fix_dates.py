import sqlite3
from datetime import date

conn = sqlite3.connect('db.sqlite3')
cur = conn.cursor()

# Replace 'Unknown' dates with today
cur.execute("UPDATE cashflow_expense SET date=? WHERE date='Unknown'", (date.today().isoformat(),))
conn.commit()
conn.close()
print("Fixed invalid dates")
