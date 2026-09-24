# scrape_pay_rates_v2.py

from pathlib import Path
from io import StringIO
import sqlite3
import re

import pandas as pd
import requests
from bs4 import BeautifulSoup
import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

DB_PATH = Path(__file__).parent / "public_service_pay.db"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64)"
    )
}



SPECIAL_ANCHORS = {

        "GL": "rates-gl-aim",
        "GS": "rates-gs-sts",

        "HS": "rates-hs-hdo",

        "MD": "rates-md-mof",

        "ND": "rates-nd-dit",

        # "NU": "rates-nu-hos",

        "OE": "rates-oe-beo",

        # "SC": "rates-sc-ded",

        "SE": "rates-se-res",

        "ST": "rates-st-typ",

        "SW": "rates-sw-scw",
    }


MULTI_ANCHORS = {

    "ND": [
        "rates-nd-dit",
        "rates-nd-adv",
        "rates-nd-hme",
    ],

    "NU": [
        "rates-nu-hos",
        "rates-nu-chn",
        "rates-nu-ema",
        "rates-nu-pra",
    ],

    "OE": [
        "rates-oe-beo",
        "rates-oe-ceo",
        "rates-oe-deo",
        "rates-oe-mse",
        "rates-oe-meo",
    ],

    "SC": [
        "rates-sc-ded",
        "rates-sc-erd",
    ],

    "SE": [
        "rates-se-res",
        "rates-se-rem",
    ],

    "ST": [
        "rates-st-typ",
        "rates-st-stn",
        "rates-st-oce",
        "rates-st-scy",
        "rates-st-cor",
    ],

    "SW": [
        "rates-sw-scw",
        "rates-sw-cha",
    ],
}

HOURLY_GROUPS = {
    "GS",
    "HS",
    "SO",
    "RAD",
    "MAO",
    "SR(E)",
    "SR(W)",
    "INS",
}

# --------------------------------------------------
# utilities
# --------------------------------------------------

def normalize_text(text):

    return (
        str(text)
        .replace("‐", "-")
        .replace("‑", "-")
        .replace("–", "-")
        .replace("—", "-")
    )


def normalize_effective_date(value):

    value = str(value)

    if ")" in value:
        value = value.split(")", 1)[1].strip()

    return value


def extract_level_code(caption_text):

    caption_text = normalize_text(
        caption_text
    )
    
    gs_match = re.search(
        r'Level-(\d+)',
        caption_text,
        re.IGNORECASE
    )

    if gs_match:

        level_num = int(
            gs_match.group(1)
        )

        return f"GS-STS-{level_num:02d}"

    patterns = [

        r'([A-Z][A-Z0-9()\-]*-\d+)',

        r'(LP-00)',
        r'(LP-01)',
        r'(LP-02)',
        r'(LP-03)',
        r'(LP-04)',
        r'(LP-05)'
    ]

    for pattern in patterns:

        m = re.search(
            pattern,
            caption_text
        )

        if m:
            return m.group(1)

    return None


def has_step_columns(df):

    for col in df.columns:

        if str(col).startswith("Step"):
            return True

    return False


def find_step_columns(df):

    cols = []

    for col in df.columns:

        col_text = (
            str(col)
            .replace("\xa0", " ")
        )

        if col_text.startswith("Step"):
            cols.append(col)

    return cols


def find_effective_date_col(df):

    for col in df.columns:

        if (
            "effective"
            in str(col).lower()
        ):
            return col

    return None


# --------------------------------------------------
# database
# --------------------------------------------------

def get_classification_id(
    cur,
    code
):

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

    m = re.search(
        r"(\d+)$",
        level_code
    )

    level_num = None

    if m:
        level_num = int(
            m.group(1)
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

    if row:
        return row[0]

    return None


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


# --------------------------------------------------
# html parsing
# --------------------------------------------------

def find_salary_heading(soup, url, code):

    if code in SPECIAL_ANCHORS:

        anchor = soup.find(
            id=SPECIAL_ANCHORS[code]
        )

        if anchor:
            return anchor

    fragment = None

    if "#" in str(url):

        fragment = (
            str(url)
            .split("#", 1)[1]
        )

    if fragment:

        anchor = soup.find(
            id=fragment
        )

        if anchor:
            return anchor

    return None



def collect_tables(
    start_heading
):

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



def collect_tables_from_anchor(anchor):

    tables = []

    print(
        "ANCHOR:",
        anchor.name,
        anchor.get("id")
    )

    node = anchor

    count = 0

    while True:

        node = node.find_next()

        if node is None:
            break

        count += 1

        if (
            node.name == "span"
            and node.has_attr("id")
            and node != anchor
        ):
            print(
                "STOP AT:",
                node.get("id")
            )
            break

        if node.name == "table":

            tables.append(node)

            caption = node.find("caption")

            if caption:

                print(
                    "TABLE:",
                    caption.get_text(
                        " ",
                        strip=True
                    )
                )

    print(
        "TOTAL TABLES:",
        len(tables)
    )

    return tables

def caption_matches_classification(
    code,
    caption_text
):

    caption_text = normalize_text(
        caption_text
    )

    if code == "GS":

        return (
            caption_text.startswith("Level-")
            or caption_text.startswith("FOS-")
        )
    
    specials = {
        "DD": ["DD-"],
        "EC": ["EC-"],
        "PM": ["PM-"],
        "PG": ["PG-"],
        "IT": ["IT-"],
        "EG": ["EG-"],
    }
    

    
    if code in specials:

        return any(
            caption_text.startswith(x)
            for x in specials[code]
        )

    return caption_text.startswith(
        f"{code}-"
    )
    

# --------------------------------------------------
# main
# --------------------------------------------------

def main():

    conn = sqlite3.connect(
        DB_PATH
    )

    cur = conn.cursor()

    rows = cur.execute(
        """
        SELECT
            code,
            tbs_url
        FROM classifications
        WHERE tbs_url IS NOT NULL
        ORDER BY code
        """
    ).fetchall()

    level_count = 0
    step_count = 0

    for code, url in rows:

        if code in HOURLY_GROUPS:

            print(
                f"Skipping hourly group: {code}"
            )

            continue

        print()
        print("=" * 60)
        print(code)

        try:

            page_url = (
                url.split("#")[0]
            )

            response = requests.get(
                page_url,
                timeout=30,
                headers=HEADERS
            )

            response.raise_for_status()

            soup = BeautifulSoup(
                response.text,
                "lxml"
            )

            if code in MULTI_ANCHORS:

                tables = []

                for anchor_id in MULTI_ANCHORS[code]:

                    anchor = soup.find(
                        id=anchor_id
                    )

                    if not anchor:
                        continue

                    print(
                        f"{code} anchor: {anchor_id}"
                    )

                    tables.extend(
                        collect_tables_from_anchor(
                            anchor
                        )
                    )

            else:

                heading = find_salary_heading(
                    soup,
                    url,
                    code
                )

                if heading is None:
                    print(
                        "No annual rates heading"
                    )
                    continue

                tables = collect_tables_from_anchor(
                    heading
                )

            classification_id = (
                get_classification_id(
                    cur,
                    code
                )
            )

            for table in tables:

                caption = table.find(
                    "caption"
                )

                caption_text = ""

                if caption:
                    caption_text = (
                        caption.get_text(
                            " ",
                            strip=True
                        )
                    )
                
                caption_lower = caption_text.lower()

                if "weekly rates" in caption_lower:
                    continue

                if "daily rates" in caption_lower:
                    continue

                if "hourly rates" in caption_lower:
                    continue
                
                try:

                    df = pd.read_html(
                        StringIO(
                            str(table)
                        )
                    )[0]

                except Exception:
                    continue

                if not has_step_columns(df):

                    if code == "SC":

                        latest = df.iloc[-1]

                        annual_salary = latest["Annual"]

                        level_code = extract_level_code(
                            caption_text
                        )

                        if not level_code:
                            continue

                        level_id = get_or_create_level(
                            cur,
                            classification_id,
                            level_code
                        )

                        effective_date = normalize_effective_date(
                            latest["Effective date"]
                        )

                        try:

                            annual_salary = int(
                                str(annual_salary)
                                .replace(",", "")
                            )

                        except Exception:
                            continue

                        save_step(
                            cur,
                            level_id,
                            1,          # fake step
                            annual_salary,
                            effective_date
                        )

                        level_count += 1
                        step_count += 1

                        print(
                            f"{level_code} "
                            f"(single rate)"
                        )

                        continue

                    print(
                        "NO STEP COLUMNS:",
                        caption_text
                    )

                    continue

                print(
                    "CAPTION:",
                    repr(caption_text)
                )
                
                if not caption_matches_classification(
                    code,
                    caption_text
                ):
                    continue
                
                print(
                    "PASS FILTER:",
                    caption_text
                )
                
                level_code = extract_level_code(
                    caption_text
                )

                if (
                "Clinical Social Workers"
                in caption_text
                ):
                
                    level_code += "-CSW"

                print(
                    "LEVEL CODE:",
                    level_code
                )

                if not level_code:
                    continue

                level_id = (
                    get_or_create_level(
                        cur,
                        classification_id,
                        level_code
                    )
                )

                if not level_id:
                    continue

                level_count += 1

                latest = df.iloc[-1]

                date_col = (
                    find_effective_date_col(
                        df
                    )
                )

                if not date_col:
                    continue

                effective_date = (
                    normalize_effective_date(
                        latest[date_col]
                    )
                )

                step_columns = (
                    find_step_columns(df)
                )

                print(
                    f"{level_code} "
                    f"({len(step_columns)} steps)"
                )

                for step_col in step_columns:

                    step_num = int(
                        re.search(
                            r"(\d+)",
                            str(step_col)
                        ).group(1)
                    )

                    salary = latest[
                        step_col
                    ]
                    
                    salary_text = str(salary).strip()

                    if not re.match(
                        r'^[\d,]+(\.\d+)?$',
                        salary_text
                    ):
                        continue
                    
                    print(
                        "LEVEL:",
                        level_code,
                        "STEP:",
                        step_col,
                        "VALUE:",
                        salary
                        )

                    try:

                        salary_text = str(salary)

                        salary_text = re.sub(
                            r"[^0-9.]",
                            "",
                            salary_text
                        )

                        if not salary_text:
                            continue

                        salary = int(
                            float(salary_text)
                        )

                    except Exception:

                        print(
                            "FAILED:",
                            salary
                        )

                        continue

                    save_step(
                        cur,
                        level_id,
                        step_num,
                        salary,
                        effective_date
                    )

                    step_count += 1

            conn.commit()

        except Exception as ex:

            print(
                f"ERROR: {ex}"
            )

    conn.commit()

    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print("Levels processed :", level_count)
    print("Steps inserted   :", step_count)

    conn.close()


if __name__ == "__main__":
    main()