from pathlib import Path
import sqlite3
DB_PATH=Path(__file__).parent/'public_service_pay.db'
conn=sqlite3.connect(DB_PATH);cur=conn.cursor()
cur.execute('CREATE TABLE IF NOT EXISTS job_titles(id INTEGER PRIMARY KEY AUTOINCREMENT, classification_id INTEGER,title TEXT,min_level INTEGER,max_level INTEGER)')
print('job_titles table ready')
conn.commit();conn.close()