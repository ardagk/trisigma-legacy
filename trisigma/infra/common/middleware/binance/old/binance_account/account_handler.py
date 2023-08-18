from typing import List, Callable
from binance.spot import Spot



import os
TIMEZONE = "utc"
coros = []
pairs = []
accounts = []
trackers = {"account": False, "exchange":False}
proxies = {}

if os.getenv("BINANCE_PROXY"):
    proxies = { 'https': os.getenv("BINANCE_PROXY")}
spots = {"main": Spot(proxies=proxies)}
spot = Spot()
position_buffer = {} #old asset position to see if changed
exch_info = {}

def setup(client):
    """Sets up the Binance client.
    """
    global exch_info
    exch_info = client.exchange_info()
    global PAIRS_TRANSLITIONS
    global ORDER_TRANSLATIONS
    keys = ["{}/{}".format(pair["baseAsset"], pair["quoteAsset"])
        for pair in exch_info["symbols"]]
    PAIRS_TRANSLITIONS = {k.replace("/", ""): k for k in keys}
    ORDER_TRANSLATIONS = {
        "FILLED": "FILLED",
        "NEW": "WORKING",
        "REJECTED": "FAILED",
        "CANCELED": "CANCELLED",
        "EXPIRED": "EXPIRED",
        "PARTIALLY_FILLED": "PARTIALLY_FILLED"
    }

def get_changed_assets (spot: Spot) -> List[str]:
    """Returns a list of assets that have changed since the last time this
    function was called.
    """
    changed_assets = []
    for asset in spot.account()["balances"]:
        if asset["asset"] not in position_buffer.keys():
            position_buffer[asset["asset"]] = asset
            if float(asset["free"]) > 0 or float(asset["locked"]) > 0:
                changed_assets.append(asset["asset"])
        else:
            if asset != position_buffer[asset["asset"]]:
                changed_assets.append(asset["asset"])
                position_buffer[asset["asset"]] = asset
    return changed_assets



def get_orders (spot: Spot, pair: str, key: Callable) -> List[dict]:
    """Returns a list of all orders for a given pair.
    """
    orders = []
    symbol = pair.replace("/", "")
    for order in spot.get_orders(symbol=symbol):
        base, quote = tuple(PAIRS_TRANSLITIONS[order["symbol"]].split("/"))
        search_key = order["clientOrderId"]
        converted_order = {
            "time": int(order["time"]/1000),
            "order_id": order["orderId"],
            "pair": "%s/%s" % (base, quote),
            "side": order["side"],
            "typ": order["type"],
            "price": float(order["price"]),
            "qty": float(order["origQty"]),
            "filled_qty": float(order["executedQty"]),
            "filled_quote_qty": float(order["cummulativeQuoteQty"]),
            "status": ORDER_TRANSLATIONS[order["status"]],
            "tif": order["timeInForce"],
            "fee": float(0),
            "fee_asset": "BNB",
            "update_time": int(order["updateTime"]/1000),
            "account": key(search_key)
        }
        orders.append(converted_order)
    return orders
