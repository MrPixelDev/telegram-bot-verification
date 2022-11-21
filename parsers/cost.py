from .table_to_rows import tableDataText
import requests
from bs4 import BeautifulSoup


MUL = 1.5


def scrape_price(soup):
    data = soup.find("table", id="api_key")
    list_table = tableDataText(data)
    return list_table


def read_page(region_code):
    quote_page = f'https://sms.com/?country={region_code}'
    page = requests.get(quote_page)
    soup = BeautifulSoup(page.text, 'html.parser')
    return scrape_price(soup)


def set_cost(region_code):
    return read_page(region_code)


def set_price(svc_price):
    if svc_price < 20:
        svc_price *= (12 * MUL)
    elif 20 <= svc_price < 70:
        svc_price *= (6 * MUL)
    else:
        svc_price *= (3 * MUL)
    if 100 < svc_price < 300:
        svc_price *= MUL
    return float("%.2f" % svc_price)
