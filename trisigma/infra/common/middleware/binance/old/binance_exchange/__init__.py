import time
from trisigma.integration import utils
from trisigma import dal
from . import recent_candles
from . import historic_candles
from . import config

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
        rows = historic_candles.process_resp(resp)
        dal.exchange.push(rows, pair, config.TIMEZONE)

def update_recent_candles():
    tasks = recent_candles.prepare_tasks(config.pairs)
    results = utils.workers.dispatch(
        tasks,
        config.DISPATCH_VOLUME,
    )
    for res in results:
        pair, resp = res
        rows = recent_candles.process_resp(resp)
        dal.exchange.push(rows, pair, config.TIMEZONE)

