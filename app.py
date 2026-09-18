from flask import Flask
from delta_rest_client import DeltaRestClient, OrderType
app = Flask(__name__)
client = DeltaRestClient(base_url="https://testnet-api.delta.exchange", api_key="REPLACE_KEY", api_secret="REPLACE_SECRET")
@app.route('/')
def home():
    return "BOT LIVE"
@app.route('/check')
def check():
    try:
        b=client.get_balances()
        return f"OK {b}"
    except Exception as e:
        return f"FAIL {e}"
@app.route('/buy')
def buy():
    try:
        o=client.place_order(product_id=84, size=10, side='buy', order_type=OrderType.MARKET)
        return f"DONE {o}"
    except Exception as e:
        return f"ERROR {e}"
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
