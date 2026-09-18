from flask import Flask
from delta_rest_client import DeltaRestClient, OrderType

app = Flask(__name__)

DELTA_API_KEY = "KCdIJwHwIFkcVFLynabxJ0kkL1gLZ5"
DELTA_API_SECRET = "NEHJCYK5fihJpCeaJh7X6xQgxn7jYpGmWpzrAOj15F9vRcQa2yAqtYFYw47I"
BASE_URfrom flask import Flask
from delta_rest_client import DeltaRestClient, OrderType

app = Flask(__name__)

# YAHAN APNI ASLI KEY DAAL
API_KEY = "yahan apni testnet api key daal"
DELTA_API_KEY = "KCdIJwHwIFkcVFLynabxJ0kkL1gLZ5"
DELTA_API_SECRET = "NEHJCYK5fihJpCeaJh7X6xQgxn7jYpGmWpzrAOj15F9vRcQa2yAqtYFYw47I"

client = DeltaRestClient(base_url=BASE_URL, api_key=API_KEY, api_secret=API_SECRET)

@app.route('/')
def home():
    return "BOT LIVE"

@app.route('/check')
def check():
    try:
        bal = client.get_balances()
        return f"KEY SAHI HAI ✅: {bal}"
    except Exception as e:
        return f"KEY GALAT ❌: {e}"

@app.route('/buy')
def buy():
    try:
        order = client.place_order(product_id=84, size=10, side='buy', order_type=OrderType.MARKET)
        return f"BUY HO GAYA ✅: {order}"
    except Exception as e:
        return f"ERROR ❌: {e}"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)L = "https://testnet-api.delta.exchange"

client = DeltaRestClient(base_url=BASE_URL, api_key=API_KEY, api_secret=API_SECRET)

@app.route('/')
def home():
    return "BOT LIVE"

@app.route('/check')
def check():
    try:
        bal = client.get_balances()
        return f"KEY SAHI HAI ✅: {bal}"
    except Exception as e:
        return f"KEY GALAT ❌: {e}"

@app.route('/buy')
def buy():
    try:
        order = client.place_order(product_id=84, size=10, side='buy', order_type=OrderType.MARKET)
        return f"BUY HO GAYA ✅: {order}"
    except Exception as e:
        return f"ERROR ❌: {e}"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
