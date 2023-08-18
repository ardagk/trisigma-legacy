from . import config
from typing import List


def prepare_tasks (pairs):
    tasks = [_recent_kline_request(pair) for pair in pairs]
    return tasks

def _recent_kline_request (pair):
    def wrapper():
        nonlocal pair
        resp = config.spot.klines(pair, interval='1m')
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


