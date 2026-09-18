from flask import Flask
import os, time, hmac, hashlib, json, requests

app = Flask(__name__)

API_KEY = os.getenv('DELTA_API_KEY')
API_SECRET = os.getenv('DELTA_API_SECRET')
BASE_URL = "https://cdn-ind.testnet.deltaex.org"
SYMBOL = "BTCUSD"
PRODUCT_ID = 84  # Tere log se mila

def do_trade():
    try:
        method = "POST"
        path = "/v2/orders"
        url = BASE_URL + path
        
        body_dict = {
            "product_id": PRODUCT_ID,
            "size": 10,
            "side": "buy",
            "order_type": "market_order"
        }
        body = json.dumps(body_dict)
        timestamp = str(int(time.time()))
        
        # Signature banana
        signature_data = method + timestamp + path + body
        signature = hmac.new(API_SECRET.encode(), signature_data.encode(), hashlib.sha256).hexdigest()
        
        headers = {
            'api-key': API_KEY,
            'timestamp': timestamp,
            'signature': signature,
            'Content-Type': 'application/json'
        }
        
        print(f"BUY Order bhej raha hu ID {PRODUCT_ID} pe...")
        r = requests.post(url, data=body, headers=headers)
        print("Response:", r.text)
        return f"SUCCESS: {r.text}"
    except Exception as e:
        print("ERROR:", e)
        return f"ERROR: {e}"

TRADE_RESULT = do_trade()

@app.route('/')
def home():
    return f"BOT LIVE - 10 Lot Buy Done - ID {PRODUCT_ID}<br><br>Result: {TRADE_RESULT}"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
