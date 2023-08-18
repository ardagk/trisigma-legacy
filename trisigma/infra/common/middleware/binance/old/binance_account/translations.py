from . import config

def pair(symbol):
    map = {k.replace("/", ""): k for k in config.PAIRS}
    return map[symbol]

def status(status):
    map = {
        "FILLED": "FILLED",
        "NEW": "WORKING",
        "REJECTED": "FAILED",
        "CANCELED": "CANCELLED",
        "EXPIRED": "EXPIRED",
        "PARTIALLY_FILLED": "PARTIALLY_FILLED"
    }
    return map[status]

