from . import config
import requests
from datetime import datetime
import exchange_calendars as xcals
from typing import List
from cachetools import cached, TTLCache
import time

QUERY='https://quotes-gw.webullfintech.com/api/quote/charts/query'

def get_market_days_since (timestamp) -> List[int]:
    xnys = xcals.get_calendar("XNYS")
    start = str(datetime.fromtimestamp(timestamp).date())
    end = str(datetime.today().date())
    dates = xnys.schedule.loc[start:end].index
    #convert to dt "America/New_York" timezone before returning as timestamp
    dates_aware = [d.tz_localize("America/New_York") for d in dates]
    dates_ts = [int(d.timestamp()) for d in dates_aware]
    return dates_ts

def prepare_tasks (pair_tips):
    tasks = []
    sorted_tips = sorted(pair_tips.items(), key=lambda x: x[1], reverse=True)
    for pair, tip in sorted_tips:
        start_times = get_market_days_since(tip - 86400)
        [tasks.append(_get_historic_candles_request(pair, t)) for t in start_times]
    return tasks

def _get_historic_candles_request(pair, start_time):
    headers=config.wb.build_req_headers()
    params = {
        "tickerIds": get_tickerid(pair),
        "type": "m1",
        "count": 800,
        "timestamp": int(start_time),
        "extendTrading": 0
    }
    def wrapper():
        nonlocal params
        nonlocal headers
        resp = requests.get(QUERY, params=params, headers=headers)
        return resp
    return wrapper


@cached(cache=TTLCache(maxsize=1024, ttl=86400*7))
def get_tickerid(pair):
    ticker = pair.split('/')[0]
    return config.wb.get_ticker(ticker)



