import json
import time
from trisigma import value
from webull import webull, paper_webull

class PlaceOrderWebull:

    def __init__(self, credentials):
        self.wbo = self.auth(credentials['usr'], credentials['pwd'])

    def __call__(
            self,
            order_request: value.OrderRequest,
        ):
        self._validate_request(order_request)
        kwargs = self._get_request_params(order_request)
        resp = self.wbo.place_order(**kwargs)
        receipt = self._fetch_receipt(resp['orderId'])
        return receipt

    def _validate_request(self, order_request):
        #Instrument validation
        instrument = order_request.instrument
        assert isinstance(self.wbo.get_ticker(instrument.base), int), \
            f"Base asset: {instrument.base}, isn't supported"
        assert instrument.quote == "USD", \
            f"Quote asset: {instrument.quote}, isn't supported"
        #Order type validation
        assert order_request.typ in {"MARKET", "LIMIT"}, \
            f"Order type: {order_request.typ}, isn't supported"
        #Lot size validation
        assert order_request.quantity % 1 == 0, \
            f"Fractional shares aren't supported"

    def _get_request_params(self, order_request):
        params = {
            "ticker": order_request.instrument.base.upper(),
            "side": order_request.side,
            "quantity": order_request.quantity,
            "type": {"MARKET":"mkt", "LIMIT":"lmt"}[order_request.typ]
        }
        if order_request.typ == "LIMIT":
            params["price"] = order_request.price
        return params


    def _fetch_receipt(self, order_id):
        pass

def new_token(usr, pwd):
    headers = {
        'authority': 'u1suser.webullfintech.com',
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9',
        'app': 'global',
        'app-group': 'broker',
        'appid': 'wb_web_app',
        'content-type': 'application/json',
        'device-type': 'Web',
        'did': '4e7c63555ff74fbe819aba4986ae6323',
        'hl': 'en',
        'locale': 'eng',
        'origin': 'https://app.webull.com',
        'os': 'web',
        'osv': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36',
        'ph': 'MacOS Chrome',
        'platform': 'web',
        'referer': 'https://app.webull.com/',
        'reqid': 'a4437faf5f034511qjme";v="107", "Chromium";v="107", "Not=A?Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'cross-site',
        'tz': 'America/Chicago',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36',
        'ver': '3.39.24'
    }

    data_raw = {'account': usr,
        'accountType': '1',
        'pwd': pwd,
        'deviceId': '4e7c63555ff74fbe819aba4986ae6323',
        'deviceName': 'MacOS Chrome',
        'grade': 1,
        'regionId': 1,
        'extInfo': {'verificationCode': None, 'xPos': 97}}
    url = 'https://u1suser.webullfintech.com/api/user/v1/login/account/v2'
    resp = requests.post(url, headers=headers, data=json.dumps(data_raw))
    return resp.json()

def auth(usr, pwd):
    token = new_token(usr, pwd)
    wbo = paper_webull()
    wbo._refresh_token = token['refreshToken']
    wbo._access_token = token['accessToken']
    wbo._token_expire = token['tokenExpireTime']
    wbo._uuid = token['uuid']
    return wbo
