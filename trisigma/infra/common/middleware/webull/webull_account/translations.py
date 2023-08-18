from . import config

def status(status):
    map = {
        "MKT": "MARKET",
        "LMT": "LIMIT",
        "BUY": "BUY",
        "SELL": "SELL",
        "WORKING": "WORKING",
        "FILLED": "FILLED",
        "PARTIALLY FILLED": "PARTIALLY_FILLED",
        "N/A": "FAILED",
        "FAILED": "EXPIRED",
        "CANCELLED": "CANCELLED",
        "PENDING": "PENDING_CANCEL",
        "PENDINGCANCEL": "PENDING_CANCEL",
    }
    return map[status]

