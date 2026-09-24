# debug_ec.py

import requests
from bs4 import BeautifulSoup

url = (
    "https://www.canada.ca/en/"
    "treasury-board-secretariat/services/pay/"
    "rates-pay/rates-pay-public-service-employees.html"
)

html = requests.get(url).text

soup = BeautifulSoup(html, "lxml")

for link in soup.find_all("a"):

    text = link.get_text(strip=True)

    if text == "EC":

        print("TEXT:")
        print(text)

        print()
        print("HREF:")
        print(repr(link.get("href")))

        break