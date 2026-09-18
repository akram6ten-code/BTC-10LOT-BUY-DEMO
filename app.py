from flask import Flask
from delta_rest_client import DeltaRestClient, OrderType

app = Flask(__name__)

# YE TERE KEYS HAI - YAHI RAHEGA
API_KEY = "bWnbXhQp0Bw2sK8rV9jT4mZ1nY3"
API_SECRET = "gH7fK9pL2qR5tW8xY0zA3cD6eJ1iU4oM2bN5vB8cX0kZ3jL6"
BASE_URL = "https://testnet-api.delta.exchange"

client = DeltaRestClient(base_url=BASE_URL, api_key=API_KEY, api_secret=API_SECRET)

@app.route('/')
def home():
    return "BOT LIVE"

@app.route('/buy')
def buy():
    try:
        order = client.place_order(product_id=84, size=10, side='buy', order_type=OrderType.MARKET)
        return f"BUY HO GAYA: {order}"
    except Exception as e:
        return f"ERROR: {e}"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
