import pandas as pd
import json
from bs4 import BeautifulSoup
from datetime import datetime
import re


def parse_file(html_file):
    with open(html_file) as fi:
        soup = BeautifulSoup(fi.read(), 'html.parser')
    table = [
        [td.text.strip() for td in tr.findAll('td')]
        for tr in soup.find('div', {'class': 'FYBTable'}).find('table').findAll('tr')
    ]
    header = table[0]
    return soup.find('h2', {'class': 'ruler'}).text, [dict(zip(header, row)) for row in table[1:]]


def get_json(html_file):
    hist_type, hist = parse_file(html_file)
    if 'order' in hist_type.lower():
        return [
            get_transformed_order_entry(item)
            for item in hist if item.get('Status') in ['F', 'A', 'P']    
        ]
    if 'transfer' in hist_type.lower():
        return [
            get_transformed_transfer_entry(item)
            for item in hist
        ]
    return []


def get_transformed_transfer_entry(item):
    dt = datetime.strptime(item['Date Executed'], '%Y-%m-%d %H:%M:%S.%f')
    timestampms = int((dt - datetime(1970,1,1)).total_seconds()*1000)
    fee = re.findall('[^a-zA-Z\$]+', item['Fees'])
    fee_currency = re.findall('[a-zA-Z\$]+', item['Fees'])
    quantity = re.findall('[^a-zA-Z\$]+', item['Amount'])
    pair = re.findall('[a-zA-Z\$]+', item['Amount'])
    type_map = {
        'Deposit': 'Credit',
        'Withdrawal': 'Debit',
        'S': 'Sell',
        'B': 'Buy'
    }
    return {
        'exchange': 'fyb',
        'trade_id': int(str(item['Ticket No'])+str(timestampms)),
        'timestampms': timestampms,
        'pair': 'sgd' if pair and pair[0] == 'S$' else pair[0].lower() if pair else '',
        'price': 1.0,
        'quantity': float(quantity[0]) if quantity else 0.0,
        'fee': float(fee[0]) if fee else 0.0,
        'fee_currency': 'SGD' if fee_currency and fee_currency[0] == 'S$' else  fee_currency[0] if fee_currency else '',
        'trade_type': type_map.get(item['Type'], item['Type']),
        'raw': json.dumps(item)
    }


def get_transformed_order_entry(item):
    dt = datetime.strptime(item['Date Executed'], '%Y-%m-%d %H:%M:%S.%f')
    timestampms = int((dt - datetime(1970,1,1)).total_seconds()*1000)
    fee = re.findall('[\d\.]+', item['Commission'])
    fee_currency = 'SGD'
    price = re.findall('[\d\.]+', item['Price'])
    quantity = re.findall('[\d\.]+', item['Qty'])
    pair = 'btc_sgd'
    type_map = {
        'Deposit': 'Credit',
        'Withdrawal': 'Debit',
        'S': 'Sell',
        'B': 'Buy'
    }
    return {
        'exchange': 'fyb',
        'trade_id': int(str(item['Ticket No'])+str(timestampms)),
        'timestampms': timestampms,
        'pair': 'btc_sgd',
        'price': float(price[0]) if quantity else 0.0,
        'quantity': float(quantity[0]) if quantity else 0.0,
        'fee': float(fee[0]) if fee else 0.0,
        'fee_currency': fee_currency,
        'trade_type': type_map.get(item['Type'], item['Type']),
        'raw': json.dumps(item)
    }
