import pandas as pd
import json
import re
from datetime import datetime


def get_transformed(item):
    def str_to_float(value):
        if value is None:
            return 0.0
        return float(re.sub('[^\d\.]', '', value))
    dt = datetime.strptime(item['Date']+' '+item['Time (UTC)'], '%Y-%m-%d %H:%M:%S.%f')
    timestampms = int((dt - datetime(1970,1,1)).total_seconds()*1000)
    amounts = {
        x: str_to_float(item[x+' Amount'])
        for x in ['USD', 'BTC', 'ETH']
    }
    if item['Type'] not in ['Buy', 'Sell']:
        price = 1.0
    elif amounts['BTC']:
        price = amounts['USD'] / amounts['BTC']
    elif amounts['ETH'] and amounts['USD']:
        price = amounts['USD'] / amounts['ETH']
    elif amounts['ETH'] and amounts['BTC']:
        price = amounts['BTC'] / amounts['ETH']
    quantity = amounts['ETH'] or amounts['BTC'] or amounts['USD']
    if item['Trading Fee (BTC)']:
        fee = str_to_float(item['Trading Fee (BTC)'])
        fee_currency = 'BTC'
    else:
        fee = str_to_float(item['Trading Fee (USD)'])
        fee_currency = 'USD'
    pair_map = {
        'USD': 'usd',
        'BTC': 'btc',
        'ETH': 'eth',
        'BTCUSD': 'btc_usd',
        'ETHUSD': 'eth_usd',
        'ETHBTC': 'eth_btc'
    }
    return {
        'exchange': 'gemini',
        'trade_id': int(item['Trade ID'] or timestampms),
        'timestampms': timestampms,
        'pair': pair_map.get(item['Symbol'], item['Symbol']),
        'price': price,
        'quantity': quantity,
        'fee': fee,
        'fee_currency': fee_currency,
        'trade_type': item['Type'],
        'raw': json.dumps(item)
    }


def get_json(csvfile, sep=';'):
    transformed = []
    df = pd.read_csv(csvfile, sep=sep)
    for item in json.loads(df.to_json(orient='records')):
        if item['USD Amount'] == 'Totals':
            continue
        transformed.append(get_transformed(item))
    return transformed
