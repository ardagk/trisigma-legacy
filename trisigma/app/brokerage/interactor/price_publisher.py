class PricePublisher:

    def __init__(self, cache):
        self.cache = cache
        self.candle_buffer = {}

    def publish_candle(self, instrument, candle):
        prev_candle = self.candle_buffer.get(str(instrument), candle)
        if candle['time'] != prev_candle['time']:
            key = "analytics::candle:%s" % str(instrument)
            self.cache[key] = candle
        self.candle_buffer[str(instrument)] = candle

    def publish_price(self, instrument, price):
        key = "analytics::price:%s" % str(instrument)
        self.cache[key] = price
