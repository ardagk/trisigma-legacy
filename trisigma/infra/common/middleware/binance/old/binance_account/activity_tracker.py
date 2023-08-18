#script isn't used
from cachetools import cached, TTLCache

trackers = {}
def get_pair_activity (name):
    """Returns a list of pairs that have been traded recently"""
    if name in trackers.keys():
        tracker = trackers[name]
    else:
        tracker = activity_tracker(name)
        trackers[name] = tracker
    return next(tracker)

@cached(cache=TTLCache(maxsize=1024*20, ttl=120))
def get_involved_pairs():
    involved_pairs = []
    for acc in config.ACCOUNT_NAMES:
        client_keys = utils.get_clients(config.PLATFORM, acc)
        for key in client_keys:
            pairs = utils.accounts.get_involved_pairs(key)
            [involved_pairs.append((acc, pair)) for pair in pairs]
    return involved_pairs

def get_exch_info():
    exch_info = config.spot.exchange_info()
    return exch_info

exch_info = get_exch_info()
def get_account_balance(acc_name):
    spot = config.spots[acc_name]
    balances = spot.account()["balances"]
    return balances

def activity_tracker(acc):
    involved_pairs = get_involved_pairs()
    position_buffer = get_account_balance(acc)
    while True:
        new_positions = get_account_balance(name)
        changed_assets = []
        for row in new_positions:
            if row["asset"] not in position_buffer.keys():
                position_buffer[row["asset"]] = row
                if float(row["free"]) > 0 or float(row["locked"]) > 0:
                    changed_assets.append(row["asset"])
            else:
                if row != position_buffer[row["asset"]]:
                    changed_assets.append(row["asset"])
                    position_buffer[row["asset"]] = row
            involved_pairs = get_possible_pairs(changed_assets)
            yield involved_pairs
            involved_pairs = []

def get_possible_pairs (assets: List[str]) -> List[str]:
    """Returns a list of possible pairs given a list of assets. And Binance's
    exchange info.
    """
    pairs = []
    for asset in assets:
        for symbol in exch_info["symbols"]:
            if asset == symbol["baseAsset"]:
                if symbol["quoteAsset"] in assets:
                    pairs.append(symbol["symbol"])
    return pairs
