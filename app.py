import os, requests
from flask import Flask
from delta_rest_client import DeltaRestClient, OrderType

app = Flask(__name__)

API_KEY = os.getenv('DELTA_API_KEY')
API_SECRET = os.getenv('DELTA_API_SECRET')
BASE_URL = "https://cdn-ind.testnet.deltaex.org"
client = DeltaRestClient(base_url=BASE_URL, api_key=API_KEY, api_secret=API_SECRET)

@app.route('/')
def home():
    r = requests.get(f"{BASE_URL}/v2/products?contract_types=perpetual_futures").json()
    syms = [p['symbol'] for p in r['result'][:5]]
    return f"BOT LIVE - Perps: {syms}"

@app.route('/buy')
def buy():
    r = requests.get(f"{BASE_URL}/v2/products?contract_types=perpetual_futures").json()
    btc = None
    for p in r['result']:
        if p['symbol'] == 'BTCUSD':
            btc = p
            break
    
    if not btc:
        return "BTCUSD Future nahi mila"
    
    pid = btc['id']
    try:
        client.set_leverage(pid, 20)
    except: pass

    try:
        order = client.place_order(product_id=pid, size=10, side='buy', order_type=OrderType.MARKET)
        return f"SUCCESS: BTCUSD LONG 10 Lots 20x Lag Gaya! {order}"
    except Exception as e:
        return f"ORDER FAIL: {e}"

@app.route('/start-algo')
def start(): return buy()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
