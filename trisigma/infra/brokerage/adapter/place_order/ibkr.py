from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.order import *
import threading
import time
import logging
import exchange_calendars as xcals
import pandas as pd

class IBapi(EWrapper, EClient):

    def __init__(self):
        EClient.__init__(self, self)

    def nextValidId(self, orderId: int):
        super().nextValidId(orderId)
        self.nextorderId = orderId

    def execDetails(self, reqId, contract, execution):
        print('Order Executed: ', reqId, contract.symbol, contract.secType,
              contract.currency, execution.execId, execution.orderId, execution.shares, execution.lastLiquidity)
    def orderStatus(self, *args):
        pass

    def openOrder(self, orderId, contract, order, orderState):
        print('OpenOrder. ID:', orderId, contract.symbol, contract.secType,
              '@', contract.exchange, order.action, order.orderType,
              order.totalQuantity, orderState.status)


    def run_forever(self, host, port, client_id):
        while True:
            self.nextorderId = None
            super().connect(host, port, client_id)
            time.sleep(1)
            super().reqAccountUpdates(True, '')
            super().run()
            if self._is_market_open():
                logging.warning("Connection to IBKR lost during market\
                hours. Reconnecting...")
            self._wait_next_interval(15,-5)

    def _wait_next_interval(self, intv, offset):
        intv_sec = (intv*60)
        next_ts = (time.time() // intv_sec + 1) * intv_sec
        delay = max(next_ts - time.time() + offset,0)
        time.sleep(delay)

    def _is_market_open(self):
        ts = time.time() + 1
        pd_ts = pd.Timestamp(ts, unit='s', tz='America/New_York')
        cal = xcals.get_calendar("XNYS")
        return bool(cal.is_open_at_time(pd_ts))


class PlaceOrderIBKR():

    def __init__(self, host='127.0.0.1', port=4002, client_id=301):
        self.app = IBapi()
        self.app_thread = threading.Thread(
            target=self.app.run_forever,
            args=(host, port, client_id),
            daemon=True)
        self.app_thread.start()

    def __call__(self, contract, order):
        self.app.placeOrder(
            self.app.nextorderId, contract, order)
        self.app.nextorderId += 1

if __name__ == '__main__':
    place_order = PlaceOrderIBKR(port=7497)
    contract = Contract()
    contract.symbol = 'AAPL'
    contract.secType = 'STK'
    contract.exchange = 'SMART'
    contract.currency = 'USD'
    order = Order()
    order.action = 'BUY'
    order.totalQuantity = 10
    order.orderType = 'MKT'
    order.eTradeOnly = False
    order.firmQuoteOnly = False
    time.sleep(3)
    resp = place_order(contract, order)
    time.sleep(3)
    pass

