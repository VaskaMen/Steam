import datetime

import requests
import re
import json
class Currency:
    url = "https://currency-exchange.p.rapidapi.com/exchange"
    vlute_list = requests.get(f"https://www.cbr-xml-daily.ru/daily_json.js").json()
    def priceToFloat(self, price):
        price = str(price)
        price = price.replace(",", '.')
        price = price.replace(" ", '')
        price = re.findall(r'-[0-9.]+|[0-9.]+', price)
        price = price[0].replace('.', '', price[0].count('.') - 1)
        price = float(price)
        return price

    def cumvert(self, value, currency):
        if datetime.datetime.strptime(self.vlute_list['Timestamp'], '%Y-%m-%dT%H:%M:%S%z').day != datetime.datetime.today().day:
            self.vlute_list = requests.get(f"https://www.cbr-xml-daily.ru/daily_json.js").json()
        amount = self.priceToFloat(value) * self.vlute_list['Valute'][currency]['Value'] / self.vlute_list['Valute'][currency]['Nominal']
        return round(amount, 2)