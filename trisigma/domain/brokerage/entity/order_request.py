"""

import json
from typing import Optional
from hashlib import sha1
import time

class OrderRequest:

    symbol: Optional[str]
    typ: Optional[str]
    side: Optional[str]
    qty: Optional[float]
    quote_qty: Optional[float]
    limit_price: Optional[float]
    tif: Optional[str]

    __sender_signature: Optional[str] = None
    __signed_at: Optional[int] = None

    def __init__(
        self,
        typ=None,
        side=None,
        qty=None,
        symbol=None,
        quote_qty=None,
        limit_price=None,
        tif="GTC"
    ):
        self.symbol = symbol
        self.side = side
        self.typ = typ
        self.qty = qty
        self.quote_qty = quote_qty
        self.limit_price = limit_price
        self.tif = tif
    def __str__(self):
        text = ""
        if self.has("symbol"): text += f"sym: {self.get_symbol()}, "
        if self.has("typ"): text += f"typ: {self.get_typ()}, "
        if self.has("side"): text += f"side: {self.get_side()}, "
        if self.has("qty"): text += f"qty: {self.get_qty()}, "
        if self.has("quote_qty"): text += f"quote_qty: {self.get_quote_qty()}, "
        if self.has("limit_price"): text += f"limit_price: {self.get_limit_price()}, "
        if self.has("tif"): text += f"tif: {self.get_tif()}, "
        return text
    def get_symbol(self):
        return self.symbol
    def get_side(self):
        return self.side
    def get_typ(self):
        return self.typ
    def get_qty(self):
        return self.qty
    def get_quote_qty(self):
        return self.quote_qty
    def get_limit_price(self):
        return self.limit_price
    def get_tif(self):
        return self.tif
    def has(self, key):
        attr = getattr(self, key)
        return attr is not None
    def is_valid(self):
        validity = (
            self.has("symbol")
            and self.has("side")
            and self.has("typ")
            and (self.has("qty") != self.has("quote_qty"))
            and self.has("limit_price") == (self.get_typ() == "LIMIT")
        )
        return validity
    def encode(self) -> str:
        return json.dumps(self.__dict__).replace(" ", "").replace("\"", "\\\"")


    def get_key(self):
        return self.__sender_signature

    @property
    def signature(self):
        return self.__sender_signature

    @signature.setter
    def signature(self, _):
        raise AttributeError("Signature is read-only")

    def is_signed(self):
        return self.__sender_signature is not None

    def __hash_state(self):
        fields = ["symbol", "side", "typ", "qty", "quote_qty", "limit_price", "tif"]
        mangled = ''
        for field in fields:
            mangled += str(getattr(self, field))
        return sha1(mangled.encode()).hexdigest()

    def sign(self, key: str):
        if self.is_signed():
            raise Exception("Signal is already signed")
        self.__signature = key
        self.__signed_at = int(time.time()*1000)
        mangled = self.__hash_state() + self.__signature + str(self.__signed_at)
        self.__signature_checksum = sha1(mangled.encode()).hexdigest()

    def checksum(self):
        if not self.is_signed():
            raise Exception("Signal is not signed")
        mangled = self.__hash_state() + self.__signature + str(self.__signed_at)
        checksum = sha1(mangled.encode()).hexdigest()
        if self.__signature_checksum != checksum:
            raise Exception("Signature is invalid")

    @staticmethod
    def decode(data: str) -> "Signal":
        return Signal(**json.loads(data))







from trisigma import entity

class OrderRequest:

    instrument: entity.Instrument
    qty: float
    side: str
    typ: str

    def __init__(self, instrument, quantity, side, typ, price=None):
        assert side in ["BUY", "SELL"]
        assert typ in ["MARKET", "LIMIT"]
        assert (price is None) != (typ == "LIMIT")
        self.instrument = instrument
        self.qty = quantity
        self.side = side
        self.typ = typ
        self.price = price

    def __repr__(self):
        return f"OrderRequest({self.instrument}, {self.qty}, {self.side}, {self.typ}, {self.price})"

    def __str__(self):
        msg = f"(self.typ) {self.side} {self.qty} {self.instrument}"
        msg += f" @ {self.price}" if self.typ == "LIMIT" else ""
        return msg

    @staticmethod
    def buy(instrument, quantity):
        return OrderRequest(instrument, quantity, "BUY", "MARKET")

    @staticmethod
    def sell(instrument, quantity):
        return OrderRequest(instrument, quantity, "SELL", "MARKET")

    @staticmethod
    def bid(instrument, quantity, price):
        return OrderRequest(instrument, quantity, "BUY", "LIMIT", price=price)

    @staticmethod
    def ask(instrument, quantity, price):
        return OrderRequest(instrument, quantity, "SELL", "LIMIT", price=price)

    def serialize(self):
        return {
            "instrument": str(self.instrument),
            "qty": self.qty,
            "side": self.side
        }

    @staticmethod
    def deserialize(data):
        return OrderRequest(
            entity.Instrument.parse(data["instrument"]),
            data["qty"],
            data["side"])
   """
