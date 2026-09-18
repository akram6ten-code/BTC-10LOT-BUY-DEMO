from flask import Flask
import os
from delta_rest_client import DeltaRestClient

app = Flask(__name__)

API_KEY = os.getenv('DELTA_API_KEY')
API_SECRET = os.getenv('DELTA_API_SECRET')
BASE_URL = "https://cdn-ind.testnet.deltaex.org"
SYMBOL = "BTCUSD"

client = DeltaRestClient(
    base_url=BASE_URL,
    api_key=API_KEY,
    api_secret=API_SECRET
)

def do_trade():
    try:
        client.set_product_leverage(product_symbol=SYMBOL, leverage=20)
        order = client.place_order(product_symbol=SYMBOL, size=10, side='buy', order_type='market_order')
        return str(order)
    except Exception as e:
        return f"ERROR: {e}"

TRADE_RESULT = do_trade()

@app.route('/')
def home():
    return f"BOT LIVE - 10 Lot Buy Done<br><br>Result: {TRADE_RESULT}"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
