import os, requests
from flask import Flask
from delta_rest_client import DeltaRestClient, OrderType

app = Flask(__name__)

API_KEY = os.getenv('DELTA_API_KEY')
API_SECRET = os.getenv('DELTA_API_SECRET')
BASE_URL = "https://cdn-ind.testnet.deltaex.org"
client = DeltaRestClient(base_url=BASE_URL, api_key=API_KEY, api_secret=API_SECRET)

def get_btc_product():
    # Seedha BTCUSD maang
    try:
        r = requests.get(f"{BASE_URL}/v2/products/BTCUSD", timeout=10).json()
        if r.get('success'):
            return r['result']
    except: pass
    # Fallback - symbols filter se
    try:
        r = requests.get(f"{BASE_URL}/v2/products?contract_types=perpetual_futures", timeout=10).json()
        for p in r['result']:
            if p['symbol'] == 'BTCUSD':
                return p
    except: pass
    return None

@app.route('/')
def home():
    p = get_btc_product()
    if p:
        return f"BOT LIVE - Found {p['symbol']} ID {p['id']} Price {p.get('spot_price')}"
    return "BOT LIVE but BTCUSD not found"

@app.route('/buy')
def buy():
    btc = get_btc_product()
    if not btc:
        return "FAIL: BTCUSD Future nahi mila API se"

    pid = btc['id']
    try:
        client.set_leverage(pid, 20)
    except Exception as e:
        pass

    try:
        order = client.place_order(product_id=pid, size=10, side='buy', order_type=OrderType.MARKET)
        return f"SUCCESS LONG ✅ BTCUSD 10 Lot 20x Lag Gaya!<br>Order: {order}"
    except Exception as e:
        return f"ORDER FAIL: {e}"

@app.route('/start-algo')
def start(): return buy()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
