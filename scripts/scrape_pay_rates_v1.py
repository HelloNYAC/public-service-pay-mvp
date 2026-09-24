from pathlib import Path
from io import StringIO
import sqlite3
import re

import pandas as pd

DB_PATH = Path(__file__).parent / "public_service_pay.db"
INVENTORY_CSV = Path(__file__).parent / "payrate_inventory.csv"


def get_classification_id(cur, code):

    row = cur.execute(
        """
        SELECT id
        FROM classifications
        WHERE code = ?
        """,
        (code,)
    ).fetchone()

    if row:
        return row[0]

    return None


def get_or_create_level(
    cur,
    classification_id,
    level_code
):

    level_match = re.search(
        r"(\d+)$",
        level_code
    )

    if not level_match:
        return None

    level_num = int(
        level_match.group(1)
    )

    cur.execute(
        """
        INSERT OR IGNORE INTO
        classification_levels
        (
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

    row = cur.execute(
        """
        SELECT id
        FROM classification_levels
        WHERE level_code = ?
        """,
        (level_code,)
    ).fetchone()

    if row is None:

        print()
        print("FAILED LEVEL")
        print("classification_id =", classification_id)
        print("level_code        =", level_code)
        print()

        return None

    return row[0]


def normalize_effective_date(
    value
):

    value = str(value)

    if ")" in value:
        value = (
            value.split(
                ")",
                1
            )[1]
            .strip()
        )

    return value


def save_step(
    cur,
    level_id,
    step_number,
    salary,
    effective_date
):

    cur.execute(
        """
        INSERT OR REPLACE INTO
        pay_steps
        (
            level_id,
            step_number,
            annual_salary,
            effective_date,
            is_current
        )
        VALUES
        (
            ?, ?, ?, ?, 1
        )
        """,
        (
            level_id,
            step_number,
            salary,
            effective_date
        )
    )


def main():

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    inventory = pd.read_csv(
        INVENTORY_CSV
    )

    step_tables = inventory[
        inventory["table_type"] == "STEP"
    ]

    inserted_levels = 0
    inserted_steps = 0

    print()
    print("=" * 80)
    print("IMPORT STEP TABLES")
    print("=" * 80)

    for _, row in step_tables.iterrows():

        classification = row[
            "classification"
        ]

        level_code = row[
            "level_code"
        ]

        if (
            pd.isna(level_code)
            or not level_code
        ):
            continue

        classification_id = (
            get_classification_id(
                cur,
                classification
            )
        )

        if not classification_id:
            continue

        level_id = get_or_create_level(
            cur,
            classification_id,
            level_code
        )

        if not level_id:
            continue

        inserted_levels += 1

    conn.commit()

    print(
        f"Levels created: {inserted_levels}"
    )

    conn.close()

    print()
    print("Done.")
    print(
        "V1 currently creates "
        "classification_levels only."
    )
    print()
    print(
        "Next step:"
    )
    print(
        "Attach source HTML + parse "
        "latest row + insert pay_steps."
    )


if __name__ == "__main__":
    main()