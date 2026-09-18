@app.route('/buy')
def buy():
    order = client.place_order(product_id=84, size=10, side='buy', order_type=OrderType.MARKET)
    return f"BUY HO GAYA: {order}"
