# count_classifications.py

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "public_service_pay.db"

conn = sqlite3.connect(DB_PATH)

cursor = conn.cursor()

count = cursor.execute(
    """
    SELECT COUNT(*)
    FROM classifications
    """
).fetchone()[0]

print(f"Total classifications: {count}")

conn.close()