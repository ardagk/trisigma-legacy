import json
import exchange_calendars as xcals
import pandas as pd
from trisigma import dtype
from cachetools import cached, TTLCache
import time
import hashlib
from webull import webull, paper_webull
import requests


PLATFORM_NAME = "webull"

LATEST='https://quotes-gw.webullfintech.com/api/quote/charts/kdata/latest'
QUERY='https://quotes-gw.webullfintech.com/api/quote/charts/query'
LATEST_ROW_SIZE = 5

class WebullConnector(dtype.Middleware):

    open_accounts = {}

    def __init__ (self):
        self.wbo = webull()
        self.tickerid = cached(
            cache=TTLCache(maxsize=1024, ttl=86400*7)
          )(lambda ticker: self.wbo.get_ticker(ticker))

    def auth(self, credentials, paper=False):
        name = credentials['name']
        if name in self.open_accounts:
            return self.open_accounts[name]
        if paper:
            wbo = self.paper_account(credentials)
        else:
            wbo = self.real_account(credentials)
        self.open_accounts[name] = wbo
        return wbo

    def paper_account (self, cred):
        #XXX Access expire error is not handled
        paper_webull._loaded_did = cred["did"]
        wbo = paper_webull()
        with open(cred["refresh_token"], "r") as f:
            result = json.load(f)
            wbo._refresh_token = result['refreshToken']
            wbo._access_token = result['accessToken']
            wbo._token_expire = result['tokenExpireTime']
            wbo._uuid = result['uuid']
            n_result = wbo.refresh_login()
            result['refreshToken'] = n_result['refreshToken']
            result['accessToken'] = n_result['accessToken']
            result['tokenExpireTime'] = n_result['tokenExpireTime']
        with open(cred["refresh_token"], "w") as f:
            json.dump(result, f)
        return wbo

    def real_account (self, cred):
        raise NotImplementedError

    def historic_candle_request(self, ticker, interval, start_time, count):
        headers=self.wbo.build_req_headers()
        params = {
            "tickerIds": self.tickerid(ticker),
            "type": interval,
            "count": count,
            "timestamp": int(start_time),
            "extendTrading": 0
        }
        prepared = requests.Request(
            'GET', QUERY, params=params, headers=headers).prepare()
        return prepared

    def latest_candle_request(self, ticker):
        xnys = xcals.get_calendar("XNYS")
        #if it is not trading hours right now, we need to get the last trading day
        if xnys.is_open_at_time(pd.Timestamp.now(tz=xnys.tz)):
            start_time = pd.Timestamp.now(tz=xnys.tz).floor('T')
        else:
            start_time = xnys.previous_close(pd.Timestamp.now(tz=xnys.tz)).floor('T')

        timestamp = int(start_time.timestamp())
        headers = self.wbo.build_req_headers()
        params = {
            "tickerIds": self.tickerid(ticker),
            "type": "m1",
            "timestamp": timestamp,
            "extendTrading": 0
        }
        prepared = requests.Request(
            'GET', LATEST, params=params, headers=headers).prepare()
        return prepared

