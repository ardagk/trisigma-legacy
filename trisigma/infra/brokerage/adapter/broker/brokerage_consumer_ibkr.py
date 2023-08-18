from ib_insync import *
from trisigma import entity
import logging
import asyncio

class BrokerageConsumerIBKR ():

    _positions = {}

    _callbacks = {}
    _subsctiptions = []

    def __init__(self, host, port, client_id, logger=None):
        self._host = host
        self._port = port
        self._client_id = client_id
        self._ib = IB()
        self._loop = asyncio.get_event_loop()
        self._logger = logger or logging.getLogger(__name__)

    def connect(self):
        self._ib.connect(self._host, self._port, self._client_id)

    def run(self):
        pass

    async def place_order(self, order_request, account):
        logging.debug(f"place_order request")
        instrument = entity.Instrument.parse(order_request['instrument'])
        if instrument.family != 'stock':
            raise ValueError("Unsupported instrument type")
        contract = Stock(instrument.base, 'SMART', instrument.quote)
        if order_request['order_type'] == 'MARKET':
            order = MarketOrder(
                order_request['side'].lower(),
                order_request['qty'],
                account=account)
        elif order_request['order_type'] == 'LIMIT':
            order = LimitOrder(
                order_request['side'].lower(),
                order_request['qty'],
                order_request['price'],
                account=account)
        else:
            raise ValueError(f"Unknown order type: {order_request['type']}")
        trade = self._ib.placeOrder(contract, order)
        tracking_id = trade.order.orderId
        return tracking_id

    async def modify_order(self, order_modification, account):
        raise NotImplementedError()

    async def cancel_order(self, order, account):
        raise NotImplementedError()

    async def get_position(self, asset, account):
        for pos in self._ib.positions(account=account):
            if pos.contract.symbol == asset and pos.account == account:
                return float(pos.position)
        for aval in self._ib.accountValues(account=account):
            if aval.tag.startswith('TotalCashBalance') and aval.currency != 'BASE':
                if aval.currency == asset and aval.account == account:
                    return float(aval.value)
        return 0.0

    async def get_order_status(self, order_id, account):
        raise NotImplementedError()

    async def get_orders(self, account):
        raise NotImplementedError()

    async def subscribe_position_update(self):
        if "position_update" not in self._subsctiptions:
            self._ib.accountValueEvent += self._account_values_update
            self._ib.positionEvent += self._position_update
            self._subsctiptions.append("position_update")

    async def subscribe_order_update(self):
        raise NotImplementedError()

    def on_position_update(self, fn):
        event_name = f"position_update"
        self._add_callback(event_name, fn)
        return fn

    def on_order_update(self, fn):
        return

    def _add_callback(self, event_name, fn):
        self._callbacks.setdefault(event_name, []).append(fn)

    def _account_values_update(self, av):
        if av.tag.startswith('TotalCashBalance') and av.currency != 'BASE':
            event_name = f"position_update"
            if event_name in self._callbacks:
                asset = av.currency
                amount = float(av.value)
                account = av.account
                self._trigger_callbacks(event_name, (account, asset, amount))

    def _position_update(self, position):
        event_name = f"position_update"
        if event_name in self._callbacks:
            asset = position.contract.symbol
            amount = float(position.position)
            account = position.account
            self._trigger_callbacks(event_name, (account, asset, amount))

    def _trigger_callbacks(self, event_name, args=(), kwargs={}):
        for cb in self._callbacks[event_name]:
            self._loop.create_task(cb(*args, **kwargs))


