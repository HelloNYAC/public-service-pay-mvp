from pathlib import Path
from io import StringIO
import sqlite3
import re
import csv

import pandas as pd
import requests
from bs4 import BeautifulSoup

DB_PATH = Path(__file__).parent / "public_service_pay.db"

OUTPUT_CSV = (
    Path(__file__).parent /
    "payrate_inventory.csv"
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64)"
    )
}


def get_classifications(conn):

    return conn.execute(
        """
        SELECT code, tbs_url
        FROM classifications
        WHERE tbs_url IS NOT NULL
        ORDER BY code
        """
    ).fetchall()


def has_step_columns(df):

    return any(
        str(col).startswith("Step")
        for col in df.columns
    )


def detect_table_type(caption_text, df):

    columns = [
        str(c)
        for c in df.columns
    ]

    if has_step_columns(df):

        if (
            "continued" in caption_text.lower()
            or "steps 6" in caption_text.lower()
            or "steps 7" in caption_text.lower()
            or "steps 8" in caption_text.lower()
            or "steps 9" in caption_text.lower()
            or "steps 10" in caption_text.lower()
        ):
            return "STEP_CONTINUATION"

        return "STEP"

    if "Range" in columns:
        return "RANGE"

    return "OTHER"


def extract_level_code(caption_text):

    caption_text = (
        caption_text
        .replace("‐", "-")
        .replace("‑", "-")
        .replace("–", "-")
        .replace("—", "-")
    )

    patterns = [
        r'([A-Z][A-Z0-9()\-]*-\d+)',
    ]

    for pattern in patterns:

        m = re.search(
            pattern,
            caption_text
        )

        if m:
            return m.group(1)

    return None


def find_salary_heading(code, soup):

    for tag in soup.find_all(
        ["h2", "h3", "h4"]
    ):

        text = tag.get_text(
            " ",
            strip=True
        )

        if (
            code in text
            and "annual rates of pay"
            in text.lower()
        ):
            return tag

    return None


def collect_tables(start_heading):

    tables = []

    node = start_heading.find_next()

    while node:

        if (
            node.name in ["h2", "h3"]
            and node != start_heading
        ):
            break

        if node.name == "table":
            tables.append(node)

        node = node.find_next()

    return tables


def main():

    conn = sqlite3.connect(DB_PATH)

    classifications = (
        get_classifications(conn)
    )

    inventory_rows = []

    total_tables = 0

    for code, url in classifications:

        print(
            f"Scanning {code}"
        )

        try:

            page_url = (
                url.split("#")[0]
            )

            response = requests.get(
                page_url,
                headers=HEADERS,
                timeout=30
            )

            response.raise_for_status()

            soup = BeautifulSoup(
                response.text,
                "lxml"
            )

            heading = find_salary_heading(
                code,
                soup
            )

            if heading is None:

                inventory_rows.append({
                    "classification": code,
                    "caption": "",
                    "level_code": "",
                    "table_type": "NO_HEADING",
                    "columns": ""
                })

                continue

            tables = collect_tables(
                heading
            )

            for table in tables:

                total_tables += 1

                caption = (
                    table.find("caption")
                )

                caption_text = ""

                if caption:
                    caption_text = (
                        caption.get_text(
                            " ",
                            strip=True
                        )
                    )

                try:

                    df = pd.read_html(
                        StringIO(
                            str(table)
                        )
                    )[0]

                    table_type = (
                        detect_table_type(
                            caption_text,
                            df
                        )
                    )

                    level_code = (
                        extract_level_code(
                            caption_text
                        )
                    )

                    inventory_rows.append(
                        {
                            "classification": code,
                            "caption": caption_text,
                            "level_code": level_code,
                            "table_type": table_type,
                            "columns": (
                                ", ".join(
                                    map(
                                        str,
                                        df.columns
                                    )
                                )
                            )
                        }
                    )

                except Exception:

                    inventory_rows.append(
                        {
                            "classification": code,
                            "caption": caption_text,
                            "level_code": "",
                            "table_type": "PARSE_ERROR",
                            "columns": ""
                        }
                    )

        except Exception as ex:

            print()
            print("ERROR:", code)
            print(type(ex))
            print(ex)
            print()

            inventory_rows.append(
                {
                    "classification": code,
                    "caption": str(ex),
                    "level_code": "",
                    "table_type": "SCAN_ERROR",
                    "columns": ""
                }
            )

    with open(
        OUTPUT_CSV,
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=[
                "classification",
                "caption",
                "level_code",
                "table_type",
                "columns"
            ]
        )

        writer.writeheader()
        writer.writerows(
            inventory_rows
        )

    inventory_df = pd.DataFrame(
        inventory_rows
    )

    print()
    print("=" * 80)
    print("TABLE TYPE SUMMARY")
    print("=" * 80)

    print(
        inventory_df["table_type"]
        .value_counts()
    )

    print()
    print("=" * 80)
    print("BY CLASSIFICATION")
    print("=" * 80)

    print(
        inventory_df.groupby(
            "classification"
        )["table_type"]
        .value_counts()
    )


    problems = inventory_df[
        inventory_df["table_type"] != "STEP"
    ]

    print()
    print("=" * 80)
    print("NON-STEP TABLES")
    print("=" * 80)

    print(
        problems[
            [
                "classification",
                "caption",
                "table_type"
            ]
        ]
    )
    print()
    print("=" * 80)
    print(
        f"Inventory rows: "
        f"{len(inventory_rows)}"
    )

    print(
        f"Tables scanned: "
        f"{total_tables}"
    )

    print(
        f"CSV written:"
    )

    print(
        OUTPUT_CSV
    )

    conn.close()


if __name__ == "__main__":
    main()