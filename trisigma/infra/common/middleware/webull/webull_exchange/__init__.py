import time
from trisigma import dal
from trisigma.integration import utils
from . import recent_candles
from . import historic_candles
from . import config
from typing import List
import exchange_calendars as xcals
import pandas as pd

def is_market_open():
    ts = time.time()
    pd_ts = pd.Timestamp(ts, unit='s', tz='America/New_York')
    cal = xcals.get_calendar("XNYS")
    return bool(cal.is_open_at_time(pd_ts))

def loop(callback=lambda: None):
    while True:
        update_recent_candles()
        callback()
        time.sleep(config.LOOP_DELAY)

def setup (conf):
    config.setup(conf)

def complete_missing_candles():
    pair_tips = dal.exchange.get_pair_tips(config.pairs, config.START_DATE)
    tasks = historic_candles.prepare_tasks(pair_tips)
    results = utils.workers.dispatch(
        tasks,
        config.DISPATCH_VOLUME,
        desc = "Filling gaps in historic candles"
    )
    for res in results:
        pair, resp = res
        rows = process_resp(resp)
        dal.exchange.push(rows, pair, config.TIMEZONE)

def update_recent_candles():
    tasks = recent_candles.prepare_tasks(config.pairs)
    results = utils.workers.dispatch(
        tasks,
        config.DISPATCH_VOLUME,
    )
    for res in results:
        pair, resp = res
        rows = process_resp(resp)
        dal.exchange.push(rows, pair, config.TIMEZONE)


def process_resp (resp) -> List[List]:
    """Converts rows to type int,float"""
    if resp.status_code != 200:
        try:
            msg = resp.json()
        except:
            msg = resp.text
        raise Exception(f"Error fetching candles: {msg}")
    raw_data = resp.json()["data"]
    rows = []
    for row_str in raw_data:
        r = [float(x) for x in row_str.split(',')[:-1]]
        rows.append(
            [
                int(r[0]),
                float(r[1]),
                float(r[3]),
                float(r[4]),
                float(r[2]),
                float(r[6])
            ]
        )
    return rows

