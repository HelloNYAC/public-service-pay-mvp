import re
import requests
from bs4 import BeautifulSoup

html = requests.get(
    "https://www.canada.ca/en/"
    "treasury-board-secretariat/topics/pay/"
    "collective-agreements/pa.html"
).text

soup = BeautifulSoup(html, "lxml")

for tag in soup.find_all(["h2", "h3", "h4", "h5"]):

    text = tag.get_text(" ", strip=True)

    if re.search(r"PM-\d+", text):
        print(tag.name, text)