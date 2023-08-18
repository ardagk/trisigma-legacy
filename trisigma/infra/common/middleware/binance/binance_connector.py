import os
from trisigma import dtype

from binance.spot import Spot

class BinanceConnector(dtype.Middleware):

    def __init__ (self):
        pass

    def client(self, credentials=None):
        proxy = os.getenv('BINANCE_PROXY')
        if proxy:
            proxy = {"socks5": proxy}
        if credentials:
            return Spot(
                key=credentials['api_key'],
                secret=credentials['secret_key'],
                proxies=proxy)
        else:
            return Spot(proxies=proxy)

