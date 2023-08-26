from ib_insync import *
from trisigma import entity
import logging
import asyncio
import time

class BrokerageConsumerIBKR ():

    _positions = {}

    _callbacks = {}
    _subsctiptions = []

    def __init__(self, host, port, client_id, logger=None):
        self._host = host
        self._port = port
        self._client_id = client_id
        self._ib = IB()
        self._loop = util.getLoop()
        self._logger = logger or logging.getLogger(__name__)
        self._ib.disconnectedEvent += self._on_disconnect
        self._ib.connectedEvent += self._on_connect
        self._connection_event = asyncio.Event()
        self.get_position = self._allow_retries(self.get_position, 3)

    def get_loop(self):
        return self._loop

    def connect(self):
        self._loop.create_task(self._polled_connect())

    def run(self):
        self._loop.create_task(self._connectivity_report_worker(10))

    def _allow_retries(self, func, count=1, delay=0.5):
        async def wrapper(*args, **kwargs):
            retries = 0
            while True:
                try:
                    await self._ensure_connection(timeout=1)
                    return await func(*args, **kwargs)
                except Exception as e:
                    self._logger.error('Error in %s: %s', func.__name__, e)
                    retries += 1
                    if retries > count:
                        self._logger.critical('Max retries reached for %s', func.__name__)
                        raise
                    await asyncio.sleep(delay)
        return wrapper

    async def _polled_connect(self, intv=15, max_attempts=None):
        attempt = 0
        while True:
            if max_attempts is not None and attempt >= max_attempts:
                raise ConnectionError(
                    'Max attempts reached while trying to connect to TWS')
            try:
                await self._ib.connectAsync(self._host, self._port, self._client_id)
                self._connection_event.set()
                break
            except Exception as e:
                self._logger.info('Unsuccessful auto-connect attempt: %s', e)
                attempt += 1
                await asyncio.sleep(intv)

    async def _ensure_connection(self, timeout=None):
        while True:
            if not self._ib.isConnected():
                if timeout is None:
                    await self._connection_event.wait()
                else:
                    await asyncio.wait_for(
                        self._connection_event.wait(),
                        timeout=timeout)
            if self._ib.isConnected():
                break
            else:
                await asyncio.sleep(0.3)


    async def _on_disconnect(self):
        self._logger.warning('Disconnected from TWS')
        self._connection_event.clear()
        self._loop.create_task(self._polled_connect())
        pass

    async def _on_connect(self):
        self._logger.info('Connected to TWS')
        self._connection_event.set()
        pass

    async def place_order(self, order_request, account):
        self._logger.debug(f"place_order request")
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


    async def _connectivity_report_worker(self, delay):
        conn_name = 'IBKR'
        try:
            await asyncio.sleep(delay)
            is_connected = self._ib.isConnected()
            logger = logging.getLogger('conn')
            logger.info(f'{conn_name} connected: {is_connected}')
            while True:
                time_left = time.time() % 2
                await asyncio.sleep(time_left)
                if is_connected != self._ib.isConnected():
                    is_connected = self._ib.isConnected()
                    logger.info(f'{conn_name} connected: {is_connected}')
        except Exception as e:
            self._logger.error(f'Error in {conn_name} connectivity report worker: {e}')
            raise




