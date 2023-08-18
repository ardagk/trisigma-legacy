import pandas as pd
from cachetools import TTLCache

class MarketAnalyticsListener:

    def __init__(self, cache):
        self.cache = cache

    def create_pointer(self, instrument, channel_name, ttl=0.3):
        return MarketAnalyticsPointer(
            instrument, channel_name, self.cache, ttl)

class MarketAnalyticsPointer:

    def __init__(self, instrument, channel_name, cache, ttl=0.3):
        self.instrument = instrument
        self.channel_name = channel_name
        self.cache = cache
        self.ttlmemo = TTLCache(maxsize=100, ttl=ttl)

    def __getitem__(self, key):
        cachekey = 'analytics::{channel}:{instrument}'.format(
            channel=self.channel_name,
            instrument=str(self.instrument))
        if cachekey in self.ttlmemo:
            try: return self.ttlmemo[cachekey][key]
            except KeyError: pass
        value = self.cache.get(cachekey)
        self.ttlmemo[cachekey] = value
        return value[key]

    def __setitem__(self, key, value):
        raise Exception('cannot set value on a pointer')
