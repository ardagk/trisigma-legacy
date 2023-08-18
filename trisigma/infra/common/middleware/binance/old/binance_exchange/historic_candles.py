from trisigma.integration.binance_exchange import config
from datetime import datetime
from typing import List

def prepare_tasks (pair_tips):
    tasks = []
    sorted_tips = sorted(pair_tips.items(), key=lambda x: x[1], reverse=True)
    end_time = datetime.today().timestamp()
    for pair, tip in sorted_tips:
        start_times = range(
            int(tip*1000),
            int(end_time*1000),
            config.COMPLETION_ROW_COUNT * 60 * 1000
        )
        [tasks.append(_get_klines_request(pair, t)) for t in start_times]
    return tasks

def _get_klines_request(pair, start_time):
    def wrapper():
        nonlocal start_time
        resp = config.spot.klines(
            symbol=pair.replace('/', ''),
            interval='1m',
            startTime=start_time,
            limit=1000,
        )
        return pair, resp
    return wrapper

def process_resp (rows: List[List]) -> List[List]:
    """Converts rows to type int,float"""
    processed_rows = [
        [
            int(r[0]/1000),
            float(r[1]),
            float(r[2]),
            float(r[3]),
            float(r[4]),
            float(r[5])
        ] for r in rows
    ]
    return processed_rows

