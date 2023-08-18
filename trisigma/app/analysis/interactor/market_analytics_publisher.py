import pandas as pd

class MarketAnalyticsPublisher:

    def __init__(self, channel_name, cache):
        self.channel_name = channel_name
        self.cache = cache

    def send(self, instrument, result):
        result = self._serialize_result(result)
        key = 'analytics::{channel}:{instrument}'.format(
            channel=self.channel_name,
            instrument=str(instrument))
        self.cache[key] = result

    def _serialize_result(self, result):
        assert not (isinstance(result, pd.DataFrame) and len(result) > 1), \
            'result must be a single row'
        if isinstance(result, pd.Series):
            return result.to_dict()
        elif isinstance(result, pd.DataFrame):
            return result.iloc[0].to_dict()
        else:
            return result
