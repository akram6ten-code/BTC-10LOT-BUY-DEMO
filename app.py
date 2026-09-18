import os
import time
import json
import hmac
import hashlib
import requests
import threading

# --- ENV ---
DELTA_API_KEY = os.getenv("DELTA_API_KEY", "").strip()
DELTA_API_SECRET = os.getenv("DELTA_API_SECRET", "").strip()
DELTA_BASE_URL = os.getenv("DELTA_BASE_URL", "https://cdn-ind.test-delta.io").strip().rstrip('/')
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()
PRODUCT_ID = int(os.getenv("PRODUCT_ID", "84"))
PRODUCT_SYMBOL = os.getenv("PRODUCT_SYMBOL", "BTCUSD")

print(f"Starting bot... BASE_URL={DELTA_BASE_URL} PRODUCT={PRODUCT_ID}")

def generate_signature(secret, message):
    return hmac.new(secret.encode('utf-8'), message.encode('utf-8'), hashlib.sha256).hexdigest()

def delta_request(method, path, query=None, body=None):
    # path = /v2/orders etc
    timestamp = str(int(time.time()))
    
    # Query string for signature - must be like ?product_id=84
    query_string = ""
    if query:
        # sort to be safe
        query_string = "?" + "&".join([f"{k}={v}" for k,v in query.items()])

    # Body string - EXACT bytes that will be sent - no spaces
    payload = ""
    if body:
        payload = json.dumps(body, separators=(",", ":"))

    # Signature = METHOD + timestamp + path + query_string + payload
    # Yehi line pehle galat thi, ab sahi hai
    signature_data = method + timestamp + path + query_string + payload
    signature = generate_signature(DELTA_API_SECRET, signature_data)

    headers = {
        "api-key": DELTA_API_KEY,
        "timestamp": timestamp,
        "signature": signature,
        "Content-Type": "application/json",
        "User-Agent": "python-bot"
    }

    url = DELTA_BASE_URL + path
    # print for debug
    # print(f"REQ {method} {url}{query_string} body={payload}")

    if method == "GET":
        resp = requests.request(method, url, params=query, headers=headers, timeout=15)
    else:
        # important: send exact payload string
        resp = requests.request(method, url, params=query, data=payload, headers=headers, timeout=15)
    
    return resp

def send_telegram(text):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print(f"TELEGRAM SKIP: {text}")
        return
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": text}, timeout=10)
    except Exception as e:
        print(f"Telegram send fail: {e}")

def handle_command(chat_id, text):
    text = text.strip().lower()
    
    if text in ["/start", "/help"]:
        msg = f"Bot Live hai bhai!\n\n/check - Key check\n/balance - Balance check\n/buy - {PRODUCT_SYMBOL} pe 10 LOT BUY\n/sell - 10 LOT SELL"
        send_telegram(msg)
        return

    if text == "/check":
        try:
            # wallet balance se key check karte hain - ye sabse pakka hai
            r = delta_request("GET", "/v2/wallet/balances")
            if r.status_code == 200:
                send_telegram(f"DELTA KEY: OK ✅\nStatus: {r.status_code}\nBASE: {DELTA_BASE_URL}\nPRODUCT: {PRODUCT_SYMBOL} ({PRODUCT_ID})")
            else:
                send_telegram(f"DELTA KEY: FAIL ❌\nStatus: {r.status_code}\nResponse: {r.text[:500]}")
        except Exception as e:
            send_telegram(f"CHECK ERROR: {e}")
        return

    if text == "/balance":
        try:
            r = delta_request("GET", "/v2/wallet/balances")
            send_telegram(f"BALANCE Response {r.status_code}:\n{r.text[:1000]}")
        except Exception as e:
            send_telegram(f"BALANCE ERROR: {e}")
        return

    if text == "/buy":
        try:
            body = {
                "product_id": PRODUCT_ID,
                "size": 10,
                "side": "buy",
                "order_type": "market_order"
            }
            r = delta_request("POST", "/v2/orders", body=body)
            if r.status_code == 200 or r.status_code == 201:
                send_telegram(f"BUY ORDER LAG GAYA ✅ 10 LOT\n{r.text[:1000]}")
            else:
                send_telegram(f"BUY FAIL ❌ {r.status_code}\n{r.text[:1000]}")
        except Exception as e:
            send_telegram(f"BUY ERROR: {e}")
        return

    if text == "/sell":
        try:
            body = {
                "product_id": PRODUCT_ID,
                "size": 10,
                "side": "sell",
                "order_type": "market_order"
            }
            r = delta_request("POST", "/v2/orders", body=body)
            send_telegram(f"SELL Response {r.status_code}:\n{r.text[:1000]}")
        except Exception as e:
            send_telegram(f"SELL ERROR: {e}")
        return

def telegram_polling():
    print("Telegram polling started...")
    offset = 0
    while True:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates?timeout=30&offset={offset}"
            resp = requests.get(url, timeout=35).json()
            if resp.get("ok"):
                for upd in resp.get("result", []):
                    offset = upd["update_id"] + 1
                    msg = upd.get("message", {})
                    chat = str(msg.get("chat", {}).get("id", ""))
                    txt = msg.get("text", "")
                    # agar chat_id set hai to sirf usi ko reply karo
                    if TELEGRAM_CHAT_ID and chat != TELEGRAM_CHAT_ID:
                        continue
                    if txt:
                        print(f"CMD from {chat}: {txt}")
                        handle_command(chat, txt)
        except Exception as e:
            print(f"Polling error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    if not DELTA_API_KEY or not DELTA_API_SECRET:
        print("ERROR: DELTA_API_KEY/SECRET missing")
    if not TELEGRAM_BOT_TOKEN:
        print("ERROR: TELEGRAM_BOT_TOKEN missing")
    else:
        threading.Thread(target=telegram_polling, daemon=True).start()
    
    # Render ko alive rakhne ke liye
    while True:
        time.sleep(60)
