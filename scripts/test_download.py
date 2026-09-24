# test_download.py

import requests

url = (
    "https://www.canada.ca/en/"
    "treasury-board-secretariat/"
    "services/pay/rates-pay/"
    "rates-pay-public-service-employees.html"
)

response = requests.get(url)

print(response.status_code)

print(response.text[:500])