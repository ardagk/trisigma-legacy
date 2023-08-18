import os
from binance.spot import Spot
from binance.error import ClientError
from trisigma import dal
from trisigma.integration import utils
import json
import math

def get_spot (key) -> Spot:
    account, platform = dal.accounts.get_client_account(key)
    creds = dal.accounts.get_credentials(account, platform)
    proxies = {'https': os.getenv("PROXY")} if  os.getenv("PROXY")else {}
    spot = Spot(key=creds['key'], secret=creds['secret'], proxies=proxies)
    return spot

def send_signal (signal):
    key = signal.get_key()
    spot = get_spot(key)

    signal.symbol = signal.symbol.replace("/", "")
    order = None
    price = float(spot.ticker_price(symbols=[signal.symbol])[0]['price'])
    handler = BinanceSignalHandler(signal, spot.exchange_info(), price)
    args, kwargs = handler.get_args()
    try:
        order = spot.new_order(*args, **kwargs)
    except ClientError as e:
        raise utils.errors.BadSignalException(f"Order has been rejected", "Respose from Binance:\n" + e.error_message, signal)
    if "orderId" in order.keys():
        receipt = {"result": "success", "order_id": order["orderId"], "resp": str(order)}
    else:
        order = json.dumps(order, indent=4)
        raise utils.errors.BadSignalException(f"Unknown signal respose", "Response from binance:\n" + order, signal)
    return receipt

def cancel_order (key, symbol, order_id) -> dict:
    spot = get_spot(key)

    try:
        if order_id == "*":
            resp = spot.cancel_open_orders(symbol=symbol)
        else:
            resp = spot.cancel_order(symbol=symbol, orderId=order_id)
        return {"result": "success", "order_id": order_id, "resp": str(resp)}
    except ClientError as e:
        if e.error_code == -2011:
            return {"result": "success", "order_id": order_id, "resp": "Order already closed"}
        else:
            raise

class BinanceSignalHandler ():

    validated_filters = [
            'PRICE_FILTER',
            'PERCENT_PRICE',
            'LOT_SIZE',
            'MARKET_LOT_SIZE',
            'MIN_NOTIONAL']
    ignored_filters = [
            'ICEBERG_PARTS',
            'MAX_NUM_ORDERS',
            'MAX_NUM_ALGO_ORDERS',
            'TRAILING_DELTA',
            'MAX_POSITION']


    def __init__ (self, signal, exch, price):
        self.signal = signal
        self.price = price
        self.exchange_info = exch
        self.rules = next(
                filter(
                    lambda x: x['symbol'] == signal.symbol,
                    self.exchange_info['symbols']
                    ),
                {})

    def __str__(self):

        price = self.price if self.signal.get_limit_price() is None else self.signal.get_limit_price()
        adapted_price = self.__price_filter(price)
        qty = self.get_qty(price)
        adapted_qty = self.__lot_size(qty)

        text = "{symbol}-{side}-{typ}-{qty}-{price}-{tif}".format(
            symbol = self.signal.get_symbol(),
            side = self.signal.get_side()[0],
            typ = self.signal.get_typ()[0],
            qty = adapted_qty,
            price = adapted_price,
            tif = self.signal.get_tif()
            )
        return text

    def get_args(self):
        qty = self.get_qty()
        adapted_qty = self.__min_notional(qty, tol=1)
        adapted_qty = self.__lot_size(adapted_qty, tol=1)
        if self.signal.get_typ() == "MARKET":
            adapted_qty = self.__market_lot_size(adapted_qty, tol=1)

        if not (qty*0.99 < adapted_qty < qty*1.01):
            title = "Quantity out of bounds"
            desc = "Exchange filters applied without an error, but the\
                    final validation failed.\n\
                    Filters applied: Lot size, Min notional\n\
                    old value: {old}\n\
                    new value: {new}\n\
                    difference: {diff}\n\
                    ".format(
                            old=qty,
                            new=adapted_qty,
                            diff=abs(adapted_qty-qty)
                            )
            raise dal.errors.BadSignalException(title, desc, self.signal)


        args = (self.signal.get_symbol(), self.signal.get_side(), self.signal.get_typ())
        kwargs = {"quantity": adapted_qty}

        if self.signal.get_typ() == "LIMIT":
            if self.signal.has("limit_price"):
                limit_price = self.signal.get_limit_price()
                adapted_limit_price = self.__price_percent_filter(limit_price, tol=1)
                adapted_limit_price = self.__price_filter(adapted_limit_price, tol=1)

                if not (limit_price*0.99 < adapted_limit_price < limit_price*1.01):
                    title = "Limit price out of bounds"
                    desc = "Exchange filters applied without an error, but the\
                    final validation failed.\n\
                    Filters applied: Price filter, Percent price filter\n\
                    old value: {old}\n\
                    new value: {new}\n\
                    difference: {diff}\n\
                    ".format(
                            old=qty,
                            new=adapted_qty,
                            diff=abs(adapted_qty-qty)
                            )
                    raise dal.errors.BadSignalException(title, desc, self.signal)
                else:
                    kwargs["price"] = adapted_limit_price
                    kwargs['timeInForce'] = self.signal.get_tif()

            else:
                raise dal.errors.BadSignalException("Missing Signal Argument", "Limit order needs a limit price", self.signal)
        elif self.signal.get_typ() != "MARKET":
            raise dal.errors.BadSignalException("Missing Signal Argument", "Unknown order type", self.signal)
        return args, kwargs

    def get_qty(self, price=None):
        price = self.price if price is None else price
        if self.signal.has("qty"):
            qty = self.signal.get_qty()
        elif self.signal.has("quote_qty"):
            if self.signal.has("limit_price"):
                price = self.signal.get_limit_price()
            qty = self.signal.get_quote_qty() / price
        else:
            raise dal.errors.BadSignalException("Missing Signal Argument", "No type of quantity provided", self.signal)
        return qty

    def __get_filter(self, filter_type):
        filt = next(
                filter(
                    lambda x: x['filterType'] == filter_type.upper(),
                    self.rules['filters']),
                {}
                )
        return filt

    def __size_round(self, num, size):
        #XXX 9 decimal rounding is a bit premature for handling floating point errors
        if size == 0:
            return num
        return round(math.floor(num * (1/size)) / (1/size), 9)

    def __price_filter(self, price, tol=None):
        price_filter = self.__get_filter("PRICE_FILTER")
        if not price_filter: return price

        new_price = price
        if "minPrice" in price_filter:
            _min = float(price_filter['minPrice'])
            new_price = max(new_price, _min)
        if "maxPrice" in price_filter:
            _max = float(price_filter['maxPrice'])
            new_price = min(new_price, _max)
        if "tickSize" in price_filter:
            size = float(price_filter['tickSize'])
            new_price = self.__size_round(new_price, size)
        self.__validate(price, new_price, tol, "PRICE", "PRICE_FILTER")
        return new_price

    def __price_percent_filter(self, price, tol=None):
        percent_price = self.__get_filter("PERCENT_PRICE")
        if not percent_price: return price
        sym_price = self.price

        new_price = price
        if "multiplierUp" in percent_price:
            new_price = min(new_price, self.price * float(percent_price['multiplierUp']))
        if "multiplierDown" in percent_price:
            new_price = max(new_price, self.price * float(percent_price['multiplierDown']))

        self.__validate(price, new_price, tol, "PRICE", "PERCENT_PRICE")
        return new_price

    def __lot_size(self, qty, tol=None):
        lot_size = self.__get_filter("LOT_SIZE")
        if not lot_size: return qty

        new_qty = qty
        if "minQty" in lot_size.keys():
            new_qty = max(new_qty, float(lot_size['minQty']))
        if "maxQty" in lot_size.keys():
            new_qty = min(new_qty, float(lot_size['maxQty']))
        if "stepSize" in lot_size.keys():
            new_qty = self.__size_round(new_qty, float(lot_size['stepSize']))
        self.__validate(qty, new_qty, tol, "Quantity", "LOT_SIZE")
        return new_qty

    def __market_lot_size(self, qty, tol=None):
        # XXX there zero values
        market_lot_size = self.__get_filter("MARKET_LOT_SIZE")
        if not market_lot_size: return qty

        new_qty = qty
        if "minQty" in market_lot_size.keys():
            new_qty = max(new_qty, float(market_lot_size['minQty']))
        if "maxQty" in market_lot_size.keys():
            new_qty = min(new_qty, float(market_lot_size['maxQty']))
        if "stepSize" in market_lot_size.keys():
            new_qty = self.__size_round(new_qty, float(market_lot_size['stepSize']))

        self.__validate(qty, new_qty, tol, "Quantity", "MARKET_LOT_SIZE")
        return new_qty

    def __min_notional(self, qty, tol=None):
        #XXX tick size hasnt implemented might not be necessary
        price = self.price
        min_notional = self.__get_filter("MIN_NOTIONAL")
        if not min_notional: return qty

        new_qty = qty
        if "minPrice" in min_notional.keys():
            new_qty = max(new_qty, float(min_notional['minPrice'])/price)
        if "maxPrice" in min_notional.keys():
            new_qty = min(new_qty, float(min_notional['maxPrice'])/price)

        self.__validate(qty, new_qty, tol, "Quantity", "MIN_NOTIONAL")
        return new_qty

    def __get_all_filters(self):
        #TODO this will be moved to modifed binance exchange rules
        all_filters = []
        for rule in self.exchange_info['symbols']:
            sym = rule["symbol"]
            filters = [filt["filterType"] for filt in rule["filters"]]
            for filt in filters:
                if filt not in all_filters:
                    all_filters.append(filt)

    def __validate(self, old, new, tol, var_name, filter_type):
        if old == 0:
            raise utils.errors.BadSignalException("Signal without {}".format(var_name), "Attempted {} with 0 {}".format(filter_type, var_name), self.signal)
        diff = (abs(old - new) / old) * 100
        if tol != None and diff > tol:
            title = "{var_name} out of bounds".format(var_name=var_name)
            desc = "Filter type: {filter_type}\n\
                    old value: {old}\n\
                    new value: {new}\n\
                    difference: {diff}\n\
                    tolerance: {tol}".format(
                            filter_type=filter_type,
                            old=old,
                            new=new,
                            diff=diff,
                            tol=tol)

            raise utils.errors.BadSignalException(title, desc, self.signal)


