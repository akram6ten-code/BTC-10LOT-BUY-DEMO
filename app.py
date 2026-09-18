import os
import time
import threading
import requests
from datetime import datetime
from flask import Flask
from delta_rest_client import DeltaRestClient, OrderType

app = Flask(__name__)

# --- Render ke Environment se Key lega ---
API_KEY = os.getenv('DELTA_API_KEY')
API_SECRET = os.getenv('DELTA_API_SECRET')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

BASE_URL = "https://testnet-api.delta.exchange"
delta_client = DeltaRestClient(base_url=BASE_URL, api_key=API_KEY, api_secret=API_SECRET)

INITIAL_LOT_SIZE = 100
REENTRY_LOT_SIZE = 50
LEVERAGE = 200
TARGET_PREMIUM = 100.0

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"Telegram Error: {e}")

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
    except Exception as e:
        send_telegram(f"Option selection error: {e}")
        return None

def get_current_price(symbol):
    try:
        ticker = delta_client.get_ticker(symbol)
        return float(ticker.get('close', 0))
    except Exception as e:
        print(f"Error getting ticker for {symbol}: {e}")
        return 0.0

def close_position(symbol, lot_size):
    try:
        delta_client.place_order(
            product_symbol=symbol,
            size=lot_size,
            side='buy',
            order_type=OrderType.MARKET
        )
        send_telegram(f"Position Closed: {symbol} | Lots: {lot_size}")
    except Exception as e:
        send_telegram(f"Error closing position {symbol}: {e}")

def execute_trade_leg(is_reentry=False):
    lot_size = REENTRY_LOT_SIZE if is_reentry else INITIAL_LOT_SIZE
    sl_pct = 0.50 if is_reentry else 0.90

    call_symbol = get_nearest_option('C')
    put_symbol = get_nearest_option('P')

    if not call_symbol or not put_symbol:
        send_telegram("Error: Suitable option contracts nahi mile.")
        return False, False

    for sym in [call_symbol, put_symbol]:
        try:
            try:
                delta_client.set_product_leverage(product_symbol=sym, leverage=LEVERAGE)
            except:
                delta_client.set_leverage(sym, LEVERAGE)
        except:
            pass
        try:
            delta_client.place_order(
                product_symbol=sym,
                size=lot_size,
                side='sell',
                order_type=OrderType.MARKET
            )
        except Exception as e:
            send_telegram(f"Order placement failed for {sym}: {e}")

    time.sleep(2)

    call_entry = get_current_price(call_symbol)
    put_entry = get_current_price(put_symbol)

    active_legs = {
        call_symbol: {'entry': call_entry, 'current_sl': call_entry * (1 + sl_pct), 'target': call_entry * 0.05, 'lowest_price': call_entry, 'trailing_active': False, 'lots': lot_size},
        put_symbol: {'entry': put_entry, 'current_sl': put_entry * (1 + sl_pct), 'target': put_entry * 0.05, 'lowest_price': put_entry, 'trailing_active': False, 'lots': lot_size}
    }

    send_telegram(f"Trade Active ({'Re-entry' if is_reentry else 'Initial'}):\nCall: {call_symbol} @ ${call_entry:.2f} ({lot_size} lots)\nPut: {put_symbol} @ ${put_entry:.2f} ({lot_size} lots)")

    sl_hit_occurred = False

    while active_legs:
        now = datetime.now()
        if now.hour >= 17:
            send_telegram("5:00 PM Exit! Closing all.")
            for sym, data in list(active_legs.items()):
                close_position(sym, data['lots'])
            return False, True

        for sym in list(active_legs.keys()):
            curr_price = get_current_price(sym)
            if curr_price == 0: continue
            data = active_legs[sym]
            if curr_price < data['lowest_price']: data['lowest_price'] = curr_price
            decay_pct = (data['entry'] - curr_price) / data['entry'] if data['entry'] else 0

            if not is_reentry:
                if decay_pct >= 0.50 and not data['trailing_active']:
                    data['trailing_active'] = True
                    data['current_sl'] = data['entry'] * 0.75
                    send_telegram(f"50% Profit on {sym}. SL at 25% profit.")
            else:
                if decay_pct >= 0.20 and not data['trailing_active']:
                    data['trailing_active'] = True
                    data['current_sl'] = data['entry']
                    send_telegram(f"20% Profit on {sym}. SL at Cost.")

            if data['trailing_active']:
                new_sl = data['lowest_price'] * 1.01
                if new_sl < data['current_sl']: data['current_sl'] = new_sl

            if curr_price >= data['current_sl']:
                send_telegram(f"SL Hit on {sym} at ${curr_price:.2f}!")
                close_position(sym, data['lots'])
                del active_legs[sym]
                sl_hit_occurred = True
            elif curr_price <= data['target']:
                send_telegram(f"95% Target Hit on {sym}!")
                close_position(sym, data['lots'])
                del active_legs[sym]
        time.sleep(3)
    return sl_hit_occurred, False

def start_algo():
    send_telegram("Algo Bot Started on Delta Testnet - Kal wala logic.")
    sl_hit, day_ended = execute_trade_leg(is_reentry=False)
    if sl_hit and not day_ended:
        if datetime.now().hour < 13:
            send_telegram("Re-entry before 1 PM...")
            time.sleep(2)
            execute_trade_leg(is_reentry=True)
        else:
            send_telegram("SL after 1 PM. No re-entry.")

# --- FLASK ROUTES ---
@app.route('/')
def home():
    try:
        ticker = delta_client.get_ticker('BTCUSD')
        return f"BOT LIVE - API OK! BTC Price: {ticker.get('close')} - IP Whitelist OK - 3 IP Saved"
    except Exception as e:
        return f"BOT LIVE - Error: {e}"

@app.route('/start-algo')
def start_algo_route():
    thread = threading.Thread(target=start_algo)
    thread.start()
    return "Algo Started! Telegram Check Karo"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
