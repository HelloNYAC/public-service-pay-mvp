import pandas as pd
import requests
from bs4 import BeautifulSoup

from io import StringIO


url = (
    "https://www.canada.ca/en/"
    "treasury-board-secretariat/topics/pay/"
    "collective-agreements/pa.html"
)

html = requests.get(url, timeout=30).text

soup = BeautifulSoup(html, "lxml")

start = None

for h3 in soup.find_all("h3"):

    text = h3.get_text(" ", strip=True)

    if text.startswith(
        "PM: Programme Administration Group annual rates of pay"
    ):
        start = h3
        break

if not start:
    raise RuntimeError("PM section not found")

tables = []

node = start.find_next()

while node:

    if (
        node.name == "h3"
        and node != start
    ):
        break

    if node.name == "table":
        tables.append(node)

    node = node.find_next()

print("PM tables found:", len(tables))
print()

for i, table in enumerate(tables, start=1):

    print("=" * 60)
    print("TABLE", i)

    caption = table.find("caption")

    if caption:
        print("CAPTION:")
        print(
            caption.get_text(
                " ",
                strip=True
            )
        )

    df = pd.read_html(
        StringIO(str(table))
    )[0]


    print("=" * 60)
    print(f"TABLE {i}")

    print("Columns:")
    print(df.columns.tolist())

    print()
    print(df.head(2))
    print()