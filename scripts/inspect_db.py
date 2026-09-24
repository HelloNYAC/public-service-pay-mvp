# inspect_db.py

from pathlib import Path
import sqlite3

DB_PATH = Path(__file__).parent / "public_service_pay.db"

conn = sqlite3.connect(DB_PATH)

rows = conn.execute("""
SELECT name
FROM sqlite_master
WHERE type='table'
ORDER BY name
""").fetchall()

for row in rows:
    print(row[0])

conn.close()