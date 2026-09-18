import os, time, json, hmac, hashlib, requests, threading
from flask import Flask

flask_app = Flask(__name__)
@flask_app.route('/')
def home():
    return "BOT LIVE HAI!"

DELTA_API_KEY = os.getenv("DELTA_API_KEY", "").strip()
DELTA_API_SECRET = os.getenv("DELTA_API_SECRET", "").strip()
DELTA_BASE_URL = os.getenv("DELTA_BASE_URL", "https://cdn-ind.test-delta.io").strip()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()
PRODUCT_ID = 84

def generate_signature(secret, message):
    return hmac.new(secret.encode('utf-8'), message.encode('utf-8'), hashlib.sha256).hexdigest()

def delta_request(method, path, query=None, body=None):
    ts = str(int(time.time()))
    qs = ""
    if query:
        qs = "?" + "&".join([f"{k}={v}" for k,v in query.items()])
    payload = json.dumps(body, separators=(",", ":")) if body else ""
    sig_data = method + ts + path + qs + payload
    sig = generate_signature(DELTA_API_SECRET, sig_data)
    headers = {"api-key": DELTA_API_KEY, "timestamp": ts, "signature": sig, "Content-Type": "application/json"}
    url = DELTA_BASE_URL + path
    if method == "GET":
        return requests.request(method, url, params=query, headers=headers, timeout=15)
    else:
        return requests.request(method, url, params=query, data=payload, headers=headers, timeout=15)

def send_telegram(text):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": text}, timeout=10)
    except:
        pass

def handle(text):
    t=text.lower().strip()
    if t in ["/start","/help","/check"]:
        try:
            r=delta_request("GET","/v2/wallet/balances")
            if r.status_code==200:
                send_telegram(f"DELTA KEY: OK ✅ LIVE HOGAYA\n{r.text[:500]}")
            else:
                send_telegram(f"KEY FAIL ❌ {r.status_code}\n{r.text[:500]}")
        except Exception as e:
            send_telegram(f"ERR {e}")
    elif t=="/buy":
        try:
            body={"product_id":PRODUCT_ID,"size":10,"side":"buy","order_type":"market_order"}
            r=delta_request("POST","/v2/orders",body=body)
            send_telegram(f"BUY {r.status_code}\n{r.text[:800]}")
        except Exception as e:
            send_telegram(f"BUY ERR {e}")

def polling():
    offset=0
    while True:
        try:
            url=f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates?timeout=30&offset={offset}"
            j=requests.get(url,timeout=35).json()
            if j.get("ok"):
                for upd in j.get("result",[]):
                    offset=upd["update_id"]+1
                    txt=upd.get("message",{}).get("text","")
                    if txt: handle(txt)
        except: time.sleep(5)

threading.Thread(target=polling, daemon=True).start()

# YE LINE SABSE IMPORTANT HAI - PORT KHOLEGA
port = int(os.environ.get("PORT", 10000))
flask_app.run(host='0.0.0.0', port=port)
