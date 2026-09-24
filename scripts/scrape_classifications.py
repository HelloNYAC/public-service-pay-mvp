from pathlib import Path
import sqlite3
import re

import requests
from bs4 import BeautifulSoup

DB_PATH = Path(__file__).parent / "public_service_pay.db"

BASE_URL = (
    "https://"
    "www.canada.ca"
)

URL = (
    "https://"
    "www.canada.ca/en/"
    "treasury-board-secretariat/services/pay/"
    "rates-pay/rates-pay-public-service-employees.html"
)

print("BASE_URL =", repr(BASE_URL))
print("URL =", repr(URL))
print()

print("Downloading page...")

response = requests.get(URL, timeout=30)
response.raise_for_status()

soup = BeautifulSoup(response.text, "lxml")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

found = 0
seen_codes = set()

for link in soup.find_all("a"):

    text = link.get_text(" ", strip=True)
    href = link.get("href")

    if not text or not href:
        continue

    if "#rates-" not in href:
        continue

    # 生成完整URL
    if href.startswith("/"):
        full_url = BASE_URL + href
    else:
        full_url = href

    text = text.strip()

    # 情况1：
    # AG Agriculture
    # CH Chemistry
    # MA Mathematics
    m = re.match(r"^([A-Z][A-Z()/-]{1,9})\s+(.+)$", text)

    if m:
        code = m.group(1).strip()
        name = m.group(2).strip()

    else:
        # 情况2：
        # EC
        # PM
        # IT
        # PR(S)
        code = text.strip()
        name = None

        if not re.fullmatch(r"[A-Z()/-]{2,10}", code):
            continue

    # 避免重复
    if code in seen_codes:
        continue

    seen_codes.add(code)

    cursor.execute(
        """
        INSERT INTO classifications
        (
            code,
            name_en,
            tbs_url
        )
        VALUES
        (
            ?,
            ?,
            ?
        )
        ON CONFLICT(code)
        DO UPDATE SET
            name_en = COALESCE(excluded.name_en, classifications.name_en),
            tbs_url = excluded.tbs_url
        """,
        (
            code,
            name,
            full_url
        )
    )

    found += 1

    print(f"{code:<10} -> {name or '[name pending]'}")
    
    print("URL =", full_url)
    if code == "EC":
        print("EC URL =", full_url)


conn.commit()

print()
print("=" * 60)
print(f"Imported {found} classifications")
print("=" * 60)

rows = cursor.execute(
    """
    SELECT code, name_en, tbs_url
    FROM classifications
    ORDER BY code
    """
).fetchall()

print()
print(f"Database contains {len(rows)} classifications")
print()

for code, name, url in rows[:20]:
    print(code, "|", name, "|", url)

conn.close()
