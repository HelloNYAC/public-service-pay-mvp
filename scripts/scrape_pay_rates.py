from pathlib import Path
import sqlite3

import pandas as pd

DB_PATH = Path(__file__).parent / "public_service_pay.db"

URL = (
    "https://www.canada.ca/en/"
    "treasury-board-secretariat/topics/pay/"
    "collective-agreements/ec.html"
)

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# 找到 EC classification
classification_id = cur.execute(
    """
    SELECT id
    FROM classifications
    WHERE code = 'EC'
    """
).fetchone()[0]

tables = pd.read_html(URL)

# EC salary tables = 1~8
salary_tables = tables[1:9]

for level_num, df in enumerate(salary_tables, start=1):

    level_code = f"EC-{level_num:02d}"

    print(level_code)

    # 创建 level
    cur.execute(
        """
        INSERT OR IGNORE INTO classification_levels (
            classification_id,
            level,
            level_code
        )
        VALUES (?, ?, ?)
        """,
        (
            classification_id,
            level_num,
            level_code
        )
    )

    level_id = cur.execute(
        """
        SELECT id
        FROM classification_levels
        WHERE classification_id = ?
          AND level = ?
        """,
        (
            classification_id,
            level_num
        )
    ).fetchone()[0]

    latest = df.iloc[-1]

    effective_date = str(
        latest["Effective Date"]
    )

    if ")" in effective_date:
        effective_date = (
            effective_date
            .split(")", 1)[1]
            .strip()
        )

    for step in range(1, 6):

        salary = int(
            latest[f"Step {step}"]
        )

        cur.execute(
            """
            INSERT OR REPLACE INTO pay_steps (
                level_id,
                step_number,
                annual_salary,
                effective_date,
                is_current
            )
            VALUES (?, ?, ?, ?, 1)
            """,
            (
                level_id,
                step,
                salary,
                effective_date
            )
        )

        print(
            f"  Step {step}: {salary}"
        )

conn.commit()

print()
print("Done")

conn.close()