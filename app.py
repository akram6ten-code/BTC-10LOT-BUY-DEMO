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
        # BTCUSD ka product_id nikalte hain
        products = client.get_products()
        product_id = None
        for p in products:
            if p['symbol'] == SYMBOL:
                product_id = p['id']
                break
        
        if not product_id:
            return f"ERROR: {SYMBOL} ka ID nahi mila"

        print(f"{SYMBOL} ID={product_id} pe 10 Lot BUY...")
        order = client.place_order(
            product_id=product_id,
            size=10,
            side='buy',
            order_type='market_order'
        )
        return f"SUCCESS ID {product_id}: {order}"
    except Exception as e:
        return f"ERROR: {e}"

TRADE_RESULT = do_trade()

@app.route('/')
def home():
    return f"BOT LIVE - 10 Lot Buy Done<br><br>Result: {TRADE_RESULT}"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
