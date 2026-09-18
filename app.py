import os, time, threading, requests
from datetime import datetime
from flask import Flask
from delta_rest_client import DeltaRestClient, OrderType

app = Flask(__name__)

# --- YAHAN FIX KIYA HAI - Render ke ENV se lega ---
API_KEY = os.getenv('DELTA_API_KEY')
API_SECRET = os.getenv('DELTA_API_SECRET')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
BASE_URL = "https://cdn-ind.testnet.deltaex.org"

delta_client = None
if API_KEY and API_SECRET:
    delta_client = DeltaRestClient(base_url=BASE_URL, api_key=API_KEY, api_secret=API_SECRET)

INITIAL_LOT_SIZE = 10
REENTRY_LOT_SIZE = 10
LEVERAGE = 200
TARGET_PREMIUM = 100.0

def send_telegram(message):
    if not TELEGRAM_BOT_TOKEN: return
    try:
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage", json={"chat_id": TELEGRAM_CHAT_ID, "text": message}, timeout=5)
    except: pass

def get_nearest_option(option_type):
    try:
        tickers = delta_client.get_tickers()
        best_symbol = None
        min_diff = float('inf')
        prefix = "C-BTC" if option_type == 'C' else "P-BTC"
        for t in tickers:
            symbol = t.get('symbol', '')
            if symbol.startswith(prefix):
                close_price = float(t.get('close', 0) or 0)
                if close_price == 0: continue
                diff = abs(close_price - TARGET_PREMIUM)
                if diff < min_diff:
                    min_diff = diff
                    best_symbol = symbol
        return best_symbol
    except: return None

def get_current_price(symbol):
    try:
        return float(delta_client.get_ticker(symbol).get('close', 0))
    except: return 0.0

def close_position(symbol, lot_size):
    try:
        delta_client.place_order(product_symbol=symbol, size=lot_size, side='buy', order_type=OrderType.MARKET)
        send_telegram(f"Closed: {symbol}")
    except Exception as e:
        send_telegram(f"Close Error {e}")

def execute_trade_leg(is_reentry=False):
    lot_size = REENTRY_LOT_SIZE if is_reentry else INITIAL_LOT_SIZE
    sl_pct = 0.50 if is_reentry else 0.90
    call_symbol = get_nearest_option('C')
    put_symbol = get_nearest_option('P')
    if not call_symbol or not put_symbol:
        send_telegram("Option nahi mile")
        return False, False
    for sym in [call_symbol, put_symbol]:
        try:
            delta_client.set_leverage(sym, LEVERAGE)
            delta_client.place_order(product_symbol=sym, size=lot_size, side='sell', order_type=OrderType.MARKET)
        except Exception as e:
            send_telegram(f"Order fail {sym}: {e}")
    time.sleep(2)
    call_entry = get_current_price(call_symbol)
    put_entry = get_current_price(put_symbol)
    active_legs = {
        call_symbol: {'entry': call_entry, 'current_sl': call_entry*(1+sl_pct), 'target': call_entry*0.05, 'lowest_price': call_entry, 'trailing_active': False, 'lots': lot_size},
        put_symbol: {'entry': put_entry, 'current_sl': put_entry*(1+sl_pct), 'target': put_entry*0.05, 'lowest_price': put_entry, 'trailing_active': False, 'lots': lot_size}
    }
    send_telegram(f"Trade Active: {call_symbol} & {put_symbol}")
    sl_hit_occurred = False
    while active_legs:
        if datetime.now().hour >= 17:
            for sym, data in list(active_legs.items()): close_position(sym, data['lots'])
            return False, True
        for sym in list(active_legs.keys()):
            curr_price = get_current_price(sym)
            if curr_price == 0: continue
            data = active_legs[sym]
            if curr_price < data['lowest_price']: data['lowest_price'] = curr_price
            decay_pct = (data['entry'] - curr_price) / data['entry'] if data['entry'] else 0
            if not is_reentry and decay_pct >= 0.50 and not data['trailing_active']:
                data['trailing_active'] = True
                data['current_sl'] = data['entry'] * 0.75
            if is_reentry and decay_pct >= 0.20 and not data['trailing_active']:
                data['trailing_active'] = True
                data['current_sl'] = data['entry']
            if data['trailing_active']:
                new_sl = data['lowest_price'] * 1.01
                if new_sl < data['current_sl']: data['current_sl'] = new_sl
            if curr_price >= data['current_sl']:
                close_position(sym, data['lots']); del active_legs[sym]; sl_hit_occurred = True
            elif curr_price <= data['target']:
                close_position(sym, data['lots']); del active_legs[sym]
        time.sleep(3)
    return sl_hit_occurred, False

def start_algo_logic():
    send_telegram("Algo Started")
    sl_hit, day_ended = execute_trade_leg(is_reentry=False)
    if sl_hit and not day_ended and datetime.now().hour < 13:
        time.sleep(2)
        execute_trade_leg(is_reentry=True)

@app.route('/')
def home():
    try:
        bal = delta_client.get_balances()
        return f"BOT LIVE - Key Sahi Hai! Balance: {str(bal)[:1000]}"
    except Exception as e:
        return f"BOT LIVE - Lekin API Error: {e} (IP Whitelist check karo - 3 IP wali screen pe Update dabao)"

@app.route('/start-algo')
def start_route():
    threading.Thread(target=start_algo_logic).start()
    return "Algo background me start ho gaya, Telegram dekho"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
