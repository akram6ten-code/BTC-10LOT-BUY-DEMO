import os
from flask import Flask
from delta_rest_client import DeltaRestClient, OrderType

app = Flask(__name__)
API_KEY = os.getenv('DELTA_API_KEY')
API_SECRET = os.getenv('DELTA_API_SECRET')
BASE_URL = "https://cdn-ind.testnet.deltaex.org"
delta_client = DeltaRestClient(base_url=BASE_URL, api_key=API_KEY, api_secret=API_SECRET)

LOT_SIZE = 10
LEVERAGE = 20

@app.route('/')
def home():
    try:
        products = delta_client.get_products()
        btc = [p['symbol'] for p in products if 'BTC' in p['symbol']][:5]
        return f"BOT LIVE - Products found: {btc}"
    except Exception as e:
        return f"BOT LIVE but get_products fail: {e}"

@app.route('/buy')
def buy_now():
    logs = []
    try:
        logs.append(f"API_KEY exists: {bool(API_KEY)}")
        # 1. Balance
        try:
            bal = delta_client.get_wallet_balances()
            logs.append(f"Balance OK: {bal}")
        except Exception as e:
            logs.append(f"Balance Error: {e}")

        # 2. Product
        products = delta_client.get_products()
        prod = None
        for p in products:
            if p.get('symbol') == 'BTCUSD':
                prod = p
                break
        if not prod:
            # try BTC-PERP or first BTC
            for p in products:
                if 'BTC' in p.get('symbol','') and p.get('contract_type')=='perpetual_futures':
                    prod = p
                    break
        
        if not prod:
            return "<br>".join(logs) + "<br>BTC Product nahi mila"

        pid = prod['id']
        sym = prod['symbol']
        logs.append(f"Found {sym} ID {pid}")

        # 3. Leverage
        try:
            delta_client.set_leverage(pid, LEVERAGE)
            logs.append(f"Leverage {LEVERAGE}x set")
        except Exception as e:
            logs.append(f"Leverage Error (ignore): {e}")

        # 4. Order
        try:
            order = delta_client.place_order(product_id=pid, size=LOT_SIZE, side='buy', order_type=OrderType.MARKET)
            logs.append(f"ORDER SUCCESS: {order}")
        except Exception as e:
            logs.append(f"ORDER FAILED: {e}")
            import traceback
            logs.append(traceback.format_exc())

    except Exception as e:
        logs.append(f"MAIN ERROR: {e}")

    return "<br>".join(logs)

@app.route('/start-algo')
def start_algo():
    return buy_now()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
