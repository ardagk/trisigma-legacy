import time
from .historic_candles import get_tickerid
from . import config
import requests

LATEST='https://quotes-gw.webullfintech.com/api/quote/charts/kdata/latest'

def prepare_tasks (pairs):
    tasks = []
    for pair in pairs:
        tasks.append(_get_latest_candles_request(pair))
    return tasks

def _get_latest_candles_request(ticker):
    num=60
    t = (int(time.time()) // num) * num  - (num*config.LATEST_ROW_SIZE)
    url = LATEST
    #4 pair per group
    params = {
        "tickerIds": get_tickerid(ticker),
        "type": "m1",
        "timestamp": t,
        "extendTrading": 0
    }
    headers = config.wb.build_req_headers()
    def wrapper():
        nonlocal url
        nonlocal params
        nonlocal headers
        resp = requests.get(url, params=params, headers=headers)
        return resp
    return wrapper
