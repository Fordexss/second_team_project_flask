import requests
from flask import Flask

app = Flask(__name__)

API_KEY = '2dd294f1-4f8b-45f6-8b40-a2bacb7a3e8b'
url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest'


def get_crypto_price(base, symbol='USD'):
    parameters = {
        'symbol': base.upper(),
        'convert': symbol.upper()
    }

    headers = {
        'Accepts': 'application/json',
        'X-CMC_PRO_API_KEY': API_KEY,
    }

    response = requests.get(url, headers=headers, params=parameters)
    data = response.json()

    if response.status_code == 200:
        prices = data['data']
        return round(prices[base.upper()]['quote'][symbol.upper()]['price'], 10)
    else:
        return None


@app.route('/')
def index():
    return 'Введіть у URL адресному рядку пару валют, наприклад: /ltc_btc'


@app.route('/<pair>')
def get_symbol_price(pair):
    currencies = pair.split('_')
    if len(currencies) == 2:
        base = currencies[0]
        symbol = currencies[1]
        price = get_crypto_price(base, symbol)
        if price:
            return f'Ціна {base.upper()} до {symbol.upper()}: {price} {symbol.upper()}'
    return 'Таких даних немає'


if __name__ == '__main__':
    app.run(debug=True)
