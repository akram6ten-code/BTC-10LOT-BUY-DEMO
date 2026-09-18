import os, time, json, hmac, hashlib, requests, threading
from flask import Flask

app_flask = Flask(__name__)
@app_flask.route('/')
def home():
    return "Bot Live Hai!"

DELTA_API_KEY = os.getenv("DELTA_API_KEY", "").strip()
DELTA_API_SECRET = os.getenv("DELTA_API_SECRET", "").strip()
DELTA_BASE_URL = os.getenv("DELTA_BASE_URL", "https://cdn-ind.test-delta.io").strip().rstrip('/')
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()
PRODUCT_ID = int(os.getenv("PRODUCT_ID", "84"))

def generate_signature(secret, message):
    return hmac.new(secret.encode('utf-8'), message.encode('utf-8'), hashlib.sha256).hexdigest()

def delta_request(method, path, query=None, body=None):
    timestamp = str(int(time.time()))
    query_string = ""
    if query:
        query_string = "?" + "&".join([f"{k}={v}" for k,v in query.items()])
    payload = ""
    if body:
        payload = json.dumps(body, separators=(",", ":"))
    signature_data = method + timestamp + path + query_string + payload
    signature = generate_signature(DELTA_API_SECRET, signature_data)
    headers = {"api-key": DELTA_API_KEY, "timestamp": timestamp, "signature": signature, "Content-Type": "application/json"}
    url = DELTA_BASE_URL + path
    if method == "GET":
        return requests.request(method, url, params=query, headers=headers, timeout=15)
    else:
        return requests.request(method, url, params=query, data=payload, headers=headers, timeout=15)

def send_telegram(text):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": text}, timeout=10)
    except Exception as e:
        print(e)

def handle_command(text):
    text=text.lower().strip()
    if text in ["/start","/help"]:
        send_telegram(f"Bot Live! /check /balance /buy")
    elif text == "/check":
        try:
            r=delta_request("GET","/v2/wallet/balances")
            if r.status_code==200:
                send_telegram(f"DELTA KEY: OK ✅\n{r.text[:800]}")
            else:
                send_telegram(f"KEY FAIL ❌ {r.status_code}\n{r.text[:800]}")
        except Exception as e:
            send_telegram(f"ERROR {e}")
    elif text == "/buy":
        try:
            body={"product_id":PRODUCT_ID,"size":10,"side":"buy","order_type":"market_order"}
            r=delta_request("POST","/v2/orders",body=body)
            send_telegram(f"BUY {r.status_code}\n{r.text[:800]}")
        except Exception as e:
            send_telegram(f"BUY ERR {e}")

def telegram_polling():
    offset=0
    while True:
        try:
            url=f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates?timeout=30&offset={offset}"
            resp=requests.get(url,timeout=35).json()
            if resp.get("ok"):
                for upd in resp.get("result",[]):
                    offset=upd["update_id"]+1
                    txt=upd.get("message",{}).get("text","")
                    chat=str(upd.get("message",{}).get("chat",{}).get("id",""))
                    if TELEGRAM_CHAT_ID and chat!=TELEGRAM_CHAT_ID: continue
                    if txt: handle_command(txt)
        except Exception as e:
            print(e); time.sleep(5)

if __name__ == "__main__":
    threading.Thread(target=telegram_polling, daemon=True).start()
    port=int(os.environ.get("PORT",10000))
    app_flask.run(host='0.0.0.0', port=port)
