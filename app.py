import os
from flask import Flask
from delta_rest_client import DeltaRestClient, OrderType

app = Flask(__name__)

API_KEY = os.environ.get("DELTA_API_KEY")
API_SECRET = os.environ.get("DELTA_API_SECRET")
BASE_URL = "https://cdn-ind.testnet.deltaex.org"

client = DeltaRestClient(base_url=BASE_URL, api_key=API_KEY, api_secret=API_SECRET)

@app.route('/')
def home():
    return "BOT LIVE - DEMO FIXED"

@app.route('/check')
def check():
    try:
        bal = client.get_balances()
        return f"KEY OK: {bal}"
    except Exception as e:
        return f"KEY FAIL: {e}"

@app.route('/buy')
def buy():
    try:
        order = client.place_order(product_id=84, size=10, side='buy', order_type=OrderType.MARKET)
        return f"BUY DONE: {order}"
    except Exception as e:
        return f"ERROR: {e}"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
