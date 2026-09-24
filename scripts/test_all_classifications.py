from pathlib import Path
from io import StringIO
import sqlite3
import re

import pandas as pd
import requests
from bs4 import BeautifulSoup

DB_PATH = Path(__file__).parent / "public_service_pay.db"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64)"
    )
}


def get_classifications(cur):
    return cur.execute(
        """
        SELECT code, tbs_url
        FROM classifications
        WHERE tbs_url IS NOT NULL
        ORDER BY code
        """
    ).fetchall()


def extract_level(caption_text):

    match = re.search(
        r"([A-Z]+)-(\d+)",
        caption_text
    )

    if not match:
        return None

    return {
        "classification": match.group(1),
        "level": int(match.group(2)),
        "level_code": (
            f"{match.group(1)}-"
            f"{int(match.group(2)):02d}"
        )
    }


def has_step_columns(df):

    for col in df.columns:

        if str(col).startswith("Step"):
            return True

    return False


def find_salary_heading(code, soup):

    headings = []

    for tag in soup.find_all(["h2", "h3", "h4"]):

        text = tag.get_text(
            " ",
            strip=True
        )

        if (
            code in text
            and "annual rates of pay"
            in text.lower()
        ):
            headings.append(tag)

    if not headings:
        return None

    return headings[0]


def collect_tables_from_section(start_heading):

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


def analyze_table(table):

    caption = table.find("caption")

    caption_text = ""

    if caption:
        caption_text = caption.get_text(
            " ",
            strip=True
        )

    try:

        df = pd.read_html(
            StringIO(str(table))
        )[0]

    except Exception:

        return {
            "caption": caption_text,
            "type": "ERROR"
        }

    if has_step_columns(df):

        level_info = extract_level(
            caption_text
        )

        return {
            "caption": caption_text,
            "type": "STEP",
            "level": level_info
        }

    cols = [
        str(c)
        for c in df.columns
    ]

    if "Range" in cols:

        return {
            "caption": caption_text,
            "type": "RANGE"
        }

    return {
        "caption": caption_text,
        "type": "OTHER"
    }


def main():

    conn = sqlite3.connect(DB_PATH)

    rows = get_classifications(conn)

    total = 0
    success = 0
    failures = 0

    print()
    print("=" * 100)
    print("CLASSIFICATION DISCOVERY SCAN")
    print("=" * 100)

    for code, url in rows:

        total += 1

        print()
        print("=" * 80)
        print(code)
        print("=" * 80)

        try:

            page_url = url.split("#")[0]

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

            if not heading:

                print(
                    "No annual rates heading found"
                )

                failures += 1
                continue

            tables = collect_tables_from_section(
                heading
            )

            step_tables = 0
            range_tables = 0
            other_tables = 0

            print(
                f"Tables found: {len(tables)}"
            )

            for table in tables:

                result = analyze_table(
                    table
                )

                kind = result["type"]

                if kind == "STEP":

                    step_tables += 1

                    print(
                        f"STEP   | "
                        f"{result['caption']}"
                    )

                elif kind == "RANGE":

                    range_tables += 1

                    print(
                        f"RANGE  | "
                        f"{result['caption']}"
                    )

                else:

                    other_tables += 1

                    print(
                        f"OTHER  | "
                        f"{result['caption']}"
                    )

            print()
            print(
                f"SUMMARY -> "
                f"STEP={step_tables}, "
                f"RANGE={range_tables}, "
                f"OTHER={other_tables}"
            )

            success += 1

        except Exception as ex:

            failures += 1

            print(
                f"ERROR: {ex}"
            )

    print()
    print("=" * 100)
    print("FINAL SUMMARY")
    print("=" * 100)

    print(f"Total classifications : {total}")
    print(f"Successful scans      : {success}")
    print(f"Failed scans          : {failures}")

    conn.close()


if __name__ == "__main__":
    main()