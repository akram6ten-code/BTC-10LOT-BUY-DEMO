from flask import Flask
import os, time, hmac, hashlib, json, requests

app = Flask(__name__)

API_KEY = os.getenv('DELTA_API_KEY')
API_SECRET = os.getenv('DELTA_API_SECRET')
BASE_URL = "https://cdn-ind.testnet.deltaex.org"

def signed_request(method, path, body_dict=None):
    timestamp = str(int(time.time()))
    body = json.dumps(body_dict) if body_dict else ""
    if method == "GET" and body == "":
        signature_data = method + timestamp + path
    else:
        signature_data = method + timestamp + path + body
    
    signature = hmac.new(API_SECRET.encode(), signature_data.encode(), hashlib.sha256).hexdigest()
    headers = {'api-key': API_KEY, 'timestamp': timestamp, 'signature': signature, 'Content-Type': 'application/json'}
    url = BASE_URL + path
    if method == "GET":
        r = requests.get(url, headers=headers)
    else:
        r = requests.post(url, data=body, headers=headers)
    return r.text

@app.route('/')
def home():
    # Ye Wallet Balance check hai - Key sahi hai to chalega
    result = signed_request("GET", "/v2/wallet/balances")
    return f"BOT LIVE - KEY CHECK:<br><br>Result: {result}<br><br> Agar yaha balance dikha to KEY SAHI HAI, IP ka issue hai.<br>Agar 'invalid_api_key' dikha to KEY GALAT HAI."

@app.route('/buy')
def buy():
    body = {"product_id": 84, "size": 10, "side": "buy", "order_type": "market_order"}
    result = signed_request("POST", "/v2/orders", body)
    return f"BUY Result: {result}"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
