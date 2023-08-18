from trisigma.storage.persistent import DBO
from trisigma.common.epoch import to_timestamp
from trisigma.common.epoch import to_timestamp_split
from cachetools import cached, TTLCache
import pandas as pd

PRICE_DB = "historic_price"

def get_head(instrument, rows):
    coll = f"{instrument}_1m"
    cursor = DBO(PRICE_DB, 'w').cursor(coll)
    head = cursor.find_one({})
    return head

def resample(df, interval, count=None):
    coef, unit = to_timestamp_split(interval)
    units = {60: "T", 3600: "H", 86400: "D", 604800: "W", 31536000: "Y"}
    intv = f"{coef}{units[unit]}"
    df.resample(intv).agg(
        {
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum',
        }
    )
    if count: df = df.head(count)
    return df

def search_instrument(
        base=None,
        quote=None,
        exchange=None,
        typ=None,
        dist=None
    ):
    query = {}
    if base: query['base'] = base.lower()
    if quote: query['quote'] = quote.lower()
    if exchange: query['exchange'] = exchange.lower()
    if typ: query['type'] = typ.lower()
    if dist: query['dist'] = dist.lower()
    cursor = DBO(PRICE_DB, 'w').cursor("instrument_info")
    res = cursor.find(query)
    rows = list(res)
    return rows


__valid_instruments = []
def validate_instrument(instrument):
    if instrument in __valid_instruments:
        return True
    if instrument.count("_") != 2:
        return False
    if instrument.split("_")[0] not in ['crypto', 'stock']:
        return False
    info = search_instrument(dist=instrument)
    if len(info) != 1:
        return False
    __valid_instruments.append(instrument)
    return True
