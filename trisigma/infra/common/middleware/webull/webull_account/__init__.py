from trisigma import dal
from . import translations
from . import config
import time

def get_orders (
        wbo,
        count: int = 200
    ) -> list:
    resp = wbo.get_history_orders(status="All", count=count)
    return resp

def process_resp (resp):
    raw_orders = resp
    orders = []
    for order in raw_orders:
        base = order['ticker']["symbol"]
        quote = order['ticker']["currencyCode"]
        if "filledTime0" in order.keys():
            update_time = int(order['filledTime0']/1000)
        else:
            update_time = int(order['createTime0']/1000)

        converted_order = {
            "time": int(order["createTime0"]/1000),
            "order_id": int(order["orderId"]),
            "pair": "%s/%s" % (base, quote),
            "side": translations.status(order["action"].upper()),
            "typ": translations.status(order["orderType"].upper()),
            "price": float(order.get('lmtPrice', '0.0')),
            "qty": float(order["totalQuantity"]),
            "filled_qty": float(order["filledQuantity"]),
            "filled_quote_qty": float(order.get('filledValue', '0.0')),
            "status": translations.status(order["status"].upper()),
            "tif": order["timeInForce"],
            "fee": 0.0,
            "fee_asset": "USD",
            "update_time": update_time,
        }
        orders.append(converted_order)
    return orders

def setup(conf):
    config.setup(conf)

def loop(callback=lambda: None):
    while True:
        for name, wbo in config.wbos.items():
            resp = get_orders(wbo)
            orders = process_resp(resp)
            dal.accounts.update_orders(orders, name, "webull")
        callback()
        time.sleep(config.LOOP_DELAY)

