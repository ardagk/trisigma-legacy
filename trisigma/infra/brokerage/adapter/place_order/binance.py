import math
from trisigma import entity
from trisigma import middleware
from trisigma import lib
from trisigma import files
from binance.spot import Spot

ORDER_TIMEOUT = 60
ORDER_TRANSLATIONS = {
        "MARKET": "MARKET",
        "LIMIT": "LIMIT",
        "BUY": "BUY",
        "SELL": "SELL",
        "WORKING": "WORKING",
        "FILLED": "FILLED",
        "PARTIALLY FILLED": "PARTIALLY_FILLED",
        "N/A": "FAILED",
        "FAILED": "EXPIRED",
        "CANCELLED": "CANCELLED",
        "PENDING": "PENDING_CANCEL",
        "PENDINGCANCEL": "PENDING_CANCEL",
    }

class PlaceOrderBinance:

    BASE_URL = {
        "BINANCE": "https://api.binance.com",
        "TESTNET": "https://testnet.binance.vision"}
    PROXY= {
        'https': 'socks5://localhost:3101'}

    def __init__(self, account):
        self.account = account
        creds = files.get_credentials(account.platform, account.name)
        self.client = self._auth(creds)
        self.host = creds['host']

    def _auth(self, credentials):
        client = Spot(
            credentials['api_key'],
            credentials['secret_key'],
            base_url=self.BASE_URL[credentials['host']],
            proxies=self.PROXY)
        return client

    def __call__(self, order_request):
        assert order_request.instrument.family == 'crypto', \
            "Binance only supports crypto"
        exch = self.client.exchange_info()
        symbol = "{}{}".format(
            order_request.instrument.base,
            order_request.instrument.quote)
        price = float(self.client.ticker_price(symbol=symbol)['price'])
        validator = BinanceOrderValidator(order_request, exch, price)
        args, kwargs = validator.get_args()
        resp = self.client.new_order(*args, **kwargs)
        receipt = self._prepare_receipt(
            resp, order_request)
        return receipt

    def _prepare_receipt(self, response, request):
        raw_order = response
        receipt = {
            "time": int(raw_order["transactTime"]/1000),
            "order_id": int(raw_order["orderId"]),
            "instrument": str(request.instrument),
            "side": raw_order['side'],
            "typ": ORDER_TRANSLATIONS[raw_order["type"]],
            "price": float(raw_order.get('price', '0.0')),
            "qty": float(raw_order["origQty"]),
            "filled_qty": float(raw_order["executedQty"]),
            "filled_quote_qty": float(raw_order.get('cummulativeQuoteQty', '0.0')),
            "status": ORDER_TRANSLATIONS[raw_order["status"]],
            "tif": raw_order["timeInForce"],
            "fee": 0.0,
            "fee_asset": None,
            "update_time": int(raw_order["workingTime"]/1000),
            "account": self.account.name,
            "platform": self.account.platform,
            "label": request.label,
            "unique_id": lib.get_unique_order_id(self.host, raw_order['orderId'])
        }
        return receipt


class BadSignalException (BaseException):
    def __init__ (self, title, desc, req):
        #TODO join values of all with coma
        msg = "{title}\n{desc}\n{req}".format(
                title=title,
                desc=desc,
                req=req)
        super().__init__(msg)

class BinanceOrderValidator ():
    TOLERANCE = 15
    validated_filters = [
            'PRICE_FILTER',
            'PERCENT_PRICE',
            'LOT_SIZE',
            'MARKET_LOT_SIZE',
            'MIN_NOTIONAL',
            'NOTIONAL']
    ignored_filters = [
            'ICEBERG_PARTS',
            'MAX_NUM_ORDERS',
            'MAX_NUM_ALGO_ORDERS',
            'TRAILING_DELTA',
            'MAX_POSITION']


    def __init__ (self, order_request, exch, price):
        self.req = order_request
        self.price = price
        self.exchange_info = exch
        self.symbol = self.req.instrument.base + self.req.instrument.quote
        self.rules = next(
                filter(
                    lambda x: x['symbol'] == self.symbol,
                    self.exchange_info['symbols']
                    ),
                {})

    def __str__(self):

        price = self.price if self.req.price is None else self.req.price
        adapted_price = self.__price_filter(price)
        qty = self.get_qty(price)
        adapted_qty = self.__lot_size(qty)

        text = "{symbol}-{side}-{typ}-{qty}-{price}-{tif}".format(
            symbol = self.req.instrument.base,
            side = self.req.side,
            typ = self.req.typ,
            qty = adapted_qty,
            price = adapted_price,
            tif = self.req.tif
            )
        return text

    def get_args(self):
        qty = self.get_qty()
        adapted_qty = self.__min_notional(qty, tol=self.TOLERANCE)
        adapted_qty = self.__notional(adapted_qty, self.price, tol=self.TOLERANCE)
        adapted_qty = self.__lot_size(adapted_qty, tol=self.TOLERANCE)
        if self.req.typ == "MARKET":
            adapted_qty = self.__market_lot_size(adapted_qty, tol=self.TOLERANCE)

        if not math.isclose(qty, adapted_qty, rel_tol=self.TOLERANCE/100):
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
            raise BadSignalException(title, desc, self.req)


        args = (self.symbol, self.req.side, self.req.typ)
        kwargs = {"quantity": adapted_qty}

        if self.req.typ == "LIMIT":
            if self.req.price:
                limit_price = self.req.price
                adapted_limit_price = self.__price_percent_filter(limit_price, tol=self.TOLERANCE)
                adapted_limit_price = self.__price_filter(adapted_limit_price, tol=self.TOLERANCE)

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
                    raise BadSignalException(title, desc, self.req)
                else:
                    kwargs["price"] = adapted_limit_price
                    kwargs['timeInForce'] = self.req.tif

            else:
                raise BadSignalException("Missing Signal Argument", "Limit order needs a limit price", self.req)
        elif self.req.typ != "MARKET":
            raise BadSignalException("Missing Signal Argument", "Unknown order type", self.req)
        return args, kwargs

    def get_qty(self, price=None):
        price = self.price if price is None else price
        if self.req.qty:
            qty = self.req.qty
        elif self.req.quote_qty:
            if self.req.price:
                price = self.req.price
            qty = self.req.quote_qty / price
        else:
            raise BadSignalException("Missing Signal Argument", "No type of quantity provided", self.req)
        return qty

    def __get_filter(self, filter_type):
        filt = next(
                filter(
                    lambda x: x['filterType'] == filter_type.upper(),
                    self.rules['filters']),
                {}
                )
        return filt

    def __size_round(self, num, size, how='round'):
        #XXX 9 decimal rounding is a bit premature for handling floating point errors
        if size == 0:
            return num
        op = dict(round=round, floor=math.floor, ceil=math.ceil)[how]
        return round(op(num * (1/size)) / (1/size), 9)

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
            new_qty = self.__size_round(new_qty, float(lot_size['stepSize']), how='ceil')
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

    def __notional(self, qty, price, tol=None):
        #XXX tick size hasnt implemented might not be necessary
        notional = self.__get_filter("MIN_NOTIONAL")
        if not notional: return qty

        new_qty = qty
        if "minNotional" in notional.keys():
            new_qty = max(new_qty, float(notional['minNotional'])/price)
        if notional.get("applyMaxToMarket", True):
            if "maxNotional" in notional.keys():
                new_qty = min(new_qty, float(notional['maxNotional'])/price)

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
            raise BadSignalException("Signal without {}".format(var_name), "Attempted {} with 0 {}".format(filter_type, var_name), self.req)
        if tol != None and not math.isclose(old, new, rel_tol=tol/100):
            title = "{var_name} out of bounds".format(var_name=var_name)
            desc = "Filter type: {filter_type}\n\
                    old value: {old}\n\
                    new value: {new}\n\
                    tolerance: {tol}".format(
                            filter_type=filter_type,
                            old=old,
                            new=new,
                            tol=tol)

            raise BadSignalException(title, desc, self.req)
