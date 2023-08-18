import os
import datetime
from binance.spot import Spot

TIMEZONE = "utc"

DEFAULT_PAIRS = []
DEFAULT_LOOP_DELAY = 10
DEFAULT_START_DATE = "2021-01-01"
DEFAULT_DISPATCH_VOLUME = 10
DEFAULT_COMPLETION_ROW_COUNT = 700

LOOP_DELAY: int
COMPLETION_ROW_COUNT: int
DISPATCH_VOLUME: int
START_DATE: datetime.datetime
PROXY: str

pairs: list
spot: Spot

def setup(conf):
    global LOOP_DELAY
    global COMPLETION_ROW_COUNT
    global DISPATCH_VOLUME
    global START_DATE
    global spot
    global pairs
    global recent_candles_tb

    LOOP_DELAY = conf.get('loop_delay', DEFAULT_LOOP_DELAY)
    COMPLETION_ROW_COUNT = conf.get('completion_row_count', DEFAULT_COMPLETION_ROW_COUNT)
    DISPATCH_VOLUME = conf.get('dispatch_volume', DEFAULT_DISPATCH_VOLUME)
    START_DATE = datetime.datetime.strptime(conf.get('start_date', DEFAULT_START_DATE), "%Y-%m-%d")
    PROXY = os.getenv("PROXY", None)

    proxies = {'https': PROXY} if PROXY else {}
    pairs = conf.get('pairs', DEFAULT_PAIRS)
    spot = Spot(proxies=proxies)

