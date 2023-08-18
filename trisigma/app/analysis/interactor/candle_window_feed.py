from trisigma import flag
import asyncio

class AsyncCandleWindowFeed:
    """
    An async iterator that streams the latest minute candle, and yields
    the latest sliding window every time it changes.
    """

    def __init__(self, cache, historic_candle_adapter):
        self.cache = cache
        self.historic_candle_adapter = historic_candle_adapter

    async def listen(self, instrument, *windows):
        """
        Listen for changes in the candle window, and yield the latest
        sliding window every time it changes.
        """
        assert self.cache["analytics::candle:%s" % str(instrument)], \
            "Instrument %s not found in cache" % str(instrument)
        for window in windows:
            await self._fill_window(instrument, window)
        while True:
            await flag.change(lambda: self.cache["analytics::candle:%s" % str(instrument)])
            new_candle = self.cache["analytics::candle:%s" % str(instrument)]
            [window.update(new_candle) for window in windows]
            yield tuple([window.df.copy() for window in windows])

    async def _fill_window(self, instrument, window):
        intv = window.interval
        size = window.size
        candles = self.historic_candle_adapter(
            instrument,
            interval=intv,
            limit=size)
        window.fill(candles)

