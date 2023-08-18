import os
from binance.spot import Spot
import json
from trisigma.integration import utils

DEFAULT_PAIRS = []
DEFAULT_ACCOUNTS = []
DEFAULT_LOOP_DELAY = 10
DEFAULT_DISPATCH_VOLUME = 3

ACCOUNTS = []
LOOP_DELAY: int
DISPATCH_VOLUME: int

PROXY: str


pairs: list
spots: dict


def setup(conf):
    global ACCOUNTS
    global LOOP_DELAY
    global DISPATCH_VOLUME
    global spots
    global pairs
    global recent_candles_tb

    pairs = conf["pairs"]
    ACCOUNTS = conf["accounts"]
    LOOP_DELAY = conf.get('loop_delay', DEFAULT_LOOP_DELAY)
    DISPATCH_VOLUME = conf.get('dispatch_volume', DEFAULT_DISPATCH_VOLUME)
    PROXY = os.getenv("PROXY", None)

    proxies = {'https': PROXY} if PROXY else {}
    for acc in ACCOUNTS:
        spots[acc] = Spot(proxies=proxies)
        creds = utils.accounts.get_credentials(acc, "binance")
        spot = Spot(
            key=creds["key"],
            secret=creds["secret"],
            proxies=proxies
        )
        spots[acc] = spot

