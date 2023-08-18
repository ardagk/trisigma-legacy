from typing import Optional
from trisigma import entity
from dataclasses import dataclass
import time
from datetime import datetime

@dataclass
class OrderRequest:
    instrument: entity.Instrument
    side: str
    typ: str
    qty: Optional[float] = None
    quote_qty: Optional[float] = None
    price: Optional[float] = None
    tif: str = "GTC"
    label: Optional[str] = None
    account_name: Optional[str] = None
    host: Optional[str] = None
    time: Optional[int] = None

    def __post_init__(self):
        if self.time is None:
            self.time = int(time.time())

    def __str__(self):
        if self.typ == 'MARKET':
            action = self.side
            if action == 'BUY': action = 'BUY '
            ext = ''
        else:
            action = {"BUY ": "SIDE", "SELL": "ASK "}[self.side]
            ext = " @ {}".format(self.price)
        if self.qty is not None:
            amount = "{qty}(b)".format(qty=self.qty)
        else:
            amount = "{qty}(q)".format(qty=self.quote_qty)
        return "* ({time})  {action}  {amount}  {instrument}{ext}".format(
            time=datetime.utcfromtimestamp(self.time).strftime('%Y-%m-%d %H:%M:%S'),
            action=action,
            amount=amount,
            instrument=self.instrument,
            ext=ext)

    def copy(self):
        return OrderRequest(
            instrument=self.instrument,
            side=self.side,
            typ=self.typ,
            qty=self.qty,
            quote_qty=self.quote_qty,
            price=self.price,
            tif=self.tif,
            label=self.label,
            account_name=self.account_name,
            host=self.host)

    def to_dict(self):
        d = self.__dict__.copy()
        d['instrument'] = str(self.instrument)
        return d

    @staticmethod
    def from_dict(d):
        if isinstance(d['instrument'], str):
            d['instrument'] = entity.Instrument.parse(d['instrument'])
        return OrderRequest(**d)


