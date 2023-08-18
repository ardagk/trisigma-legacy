from trisigma import value
from trisigma import dtype
from trisigma import inbound
from trisigma import outbound

class CandleFeedAggregator:

    def __init__(self, agg: dtype.Agg):
        self.agg = agg

    def setup_candle_window(self, interval, size):
        self.interval = interval
        self.size = size

    @classmethod
    def plug(
            cls,
            on_new_candle: inbound.NewCandle,
            get_candles: outbound.GetCandles,
        ):
        cls.on_new_candle = on_new_candle
        cls.get_candles = get_candles

    def add_instrument(self, instrument, callback):
        window = CandleWindow(self.interval, self.size)
        candles = self.get_candles(instrument, self.interval, self.size)
        window.update(candles)
        def handle(self, instrument, candle):
            nonlocal window
            window.update(candle)
            row = {k: v[window] for k, v in self.agg.items()}
            callback(instrument, row)
        self.on_new_candle(instrument)(handle)

