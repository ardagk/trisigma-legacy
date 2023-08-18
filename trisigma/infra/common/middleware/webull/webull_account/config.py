import json
from trisigma import dal
from webull import paper_webull

DEFAULT_ACCOUNTS = []
DEFAULT_LOOP_DELAY = 10

ACCOUNTS = []
LOOP_DELAY: int
wbos: dict


def setup(conf):
    global ACCOUNTS
    global LOOP_DELAY
    global DISPATCH_VOLUME
    global wbos
    global pairs
    global recent_candles_tb

    wbos = {}
    pairs = conf["pairs"]
    ACCOUNTS = conf["accounts"]
    LOOP_DELAY = conf.get('loop_delay', DEFAULT_LOOP_DELAY)

    for acc in ACCOUNTS:
        creds = dal.accounts.get_credentials(acc, "webull")
        wbo = paper_auth(creds)
        wbos[acc] = wbo
