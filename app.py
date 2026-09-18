import os
import threading
import requests
from flask import Flask
from delta_rest_client import DeltaRestClient, OrderType

app = Flask(__name__)

API_KEY = os.getenv('DELTA_API_KEY')
API_SECRET = os.getenv('DELTA_API_SECRET')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

BASE_URL = "https://cdn-ind.testnet.deltaex.org"
delta_client = DeltaRestClient(base_url=BASE_URL, api_key=API_KEY, api_secret=API_SECRET)

LOT_SIZE = 10
LEVERAGE = 20
SYMBOL_TO_TRADE = "BTCUSD"

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try: requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": message}, timeout=5)
    except: pass

def get_product_id(symbol_name):
    try:
        products = delta_client.get_products()
        for p in products:
            if p.get('symbol') == symbol_name:
                return p.get('id')
    except Exception as e:
        send_telegram(f"Product ID error: {e}")
    return None

def buy_long():
    pid = get_product_id(SYMBOL_TO_TRADE)
    if not pid:
        send_telegram(f"Product {SYMBOL_TO_TRADE} nahi mila")
        return
    try:
        delta_client.set_leverage(pid, LEVERAGE)
    except: pass

    try:
        # SAHI FIX - OrderType.MARKET (MARKET_ORDER nahi)
        delta_client.place_order(product_id=pid, size=LOT_SIZE, side='buy', order_type=OrderType.MARKET)
        send_telegram(f"LONG Placed! ✅\nSymbol: {SYMBOL_TO_TRADE}\nLots: {LOT_SIZE}\nLeverage: {LEVERAGE}x @ Market")
    except Exception as e:
        send_telegram(f"Buy Failed: {e}")

@app.route('/')
def home():
    try:
        tickers = delta_client.get_tickers()
        return f"BOT LIVE - Future Bot Ready! {len(tickers)} Tickers - {LEVERAGE}x Ready"
    except Exception as e:
        return f"BOT LIVE - Error: {e}"

@app.route('/start-algo')
@app.route('/buy')
def start_algo_route():
    threading.Thread(target=buy_long).start()
    return f"LONG {LOT_SIZE} Lots {LEVERAGE}x Placing! Telegram Dekh"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
