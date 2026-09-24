from pathlib import Path
import sqlite3

DB_PATH = Path(__file__).parent / 'public_service_pay.db'
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS classifications (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 code TEXT NOT NULL UNIQUE,
 name_en TEXT,
 tbs_url TEXT,
 active INTEGER DEFAULT 1,
 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS classification_levels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    classification_id INTEGER NOT NULL,

    level INTEGER,

    level_code TEXT NOT NULL UNIQUE,

    FOREIGN KEY(classification_id)
        REFERENCES classifications(id)
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS pay_steps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    level_id INTEGER NOT NULL,
    step_number INTEGER NOT NULL,

    annual_salary INTEGER NOT NULL,

    effective_date TEXT,

    is_current INTEGER DEFAULT 1,

    FOREIGN KEY(level_id)
        REFERENCES classification_levels(id),

    UNIQUE(
        level_id,
        step_number,
        effective_date
    )
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS crawl_status (
 classification_code TEXT PRIMARY KEY,
 crawled INTEGER DEFAULT 0,
 last_crawled TEXT
)
""")
conn.commit()
print('Database initialized:', DB_PATH)
conn.close()