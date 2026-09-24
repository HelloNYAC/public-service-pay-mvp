import sqlite3

conn = sqlite3.connect("public_service_pay.db")

cursor = conn.cursor()

cursor.execute("""
DELETE FROM classifications
""")

conn.commit()

print("classifications cleared")

conn.close()