from ib_insync import *
import logging
import asyncio
import time

class BrokerageConsumerIBKR ():

    _callbacks = {}

    def __init__(self, host, port, client_id, logger=None):
        self._host = host
        self._port = port
        self._client_id = client_id
        self._ib = IB()
        self._loop = util.getLoop()
        self._logger = logger or logging.getLogger(__name__)
        self._connection_event = asyncio.Event()
        self._subscribe_all()
        self.get_position = self._allow_retries(self.get_position, 3)

    def get_loop(self):
        return self._loop

    def connect(self):
        self._loop.create_task(self._polled_connect())

    def run(self):
        self._loop.create_task(self._connectivity_report_worker(10))


    async def place_order(self, order_request):
        self._logger.info("[ORQ] Placing order")
        instrument = order_request['instrument']
        if instrument.family != 'stock':
            raise ValueError("Unsupported instrument type")
        contract = Stock(instrument.base, 'SMART', instrument.quote)
        if order_request['order_type'] == 'MARKET':
            cls = MarketOrder
            params = dict(
                action=order_request['side'].lower(),
                totalQuantity=order_request['qty']
            )
        elif order_request['order_type'] == 'LIMIT':
            cls = LimitOrder
            params = dict(
                action=order_request['side'].lower(),
                totalQuantity=order_request['qty'],
                price=order_request['price'])
        else:
            raise ValueError(f"Unknown order type: {order_request['type']}")
        if 'extra' in order_request:
            params.update(order_request['extra'])
        order = cls(**params)
        trade = self._ib.placeOrder(contract, order)
        tracking_id = trade.order.orderId
        return tracking_id

    async def modify_order(self, order_modification, account):
        raise NotImplementedError()

    async def cancel_order(self, order, account):
        raise NotImplementedError()

    async def get_position(self, asset, account):
        assert account != None
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

    def on_position_update(self, fn):
        event_name = f"position_update"
        self._add_callback(event_name, fn)
        return fn

    def on_order_update(self, fn):
        event_name = f"order_update"
        self._add_callback(event_name, fn)
        return fn

    def on_new_order(self, fn):
        event_name = f"new_order"
        self._add_callback(event_name, fn)
        return fn

    def _add_callback(self, event_name, fn):
        self._callbacks.setdefault(event_name, []).append(fn)

    def _recv_connectedEvent(self):
        self._logger.info('Connected to TWS')
        self._connection_event.set()
        pass

    def _recv_disconnectEvent(self):
        self._logger.warning('Disconnected from TWS')
        self._connection_event.clear()
        self._loop.create_task(self._polled_connect())
        pass

    def _recv_errorEvent(self, reqId, errorCode, errorString, contract):
        try:
            err_line = f"{str(errorCode)} {str(errorString)}  -  req:{str(reqId)}"
            self._logger.error(err_line)
        except Exception:
            self._logger.error('Error logging ib error event', exc_info=True)

    def _recv_accountValueEvent(self, av):
        if av.tag.startswith('TotalCashBalance') and av.currency != 'BASE':
            event_name = f"position_update"
            if event_name in self._callbacks:
                asset = av.currency
                amount = float(av.value)
                account = av.account
                self._trigger_callbacks(event_name, (account, asset, amount))

    def _recv_positionEvent(self, position):
        event_name = "position_update"
        if event_name in self._callbacks:
            asset = position.contract.symbol
            amount = float(position.position)
            account = position.account
            self._trigger_callbacks(event_name, (account, asset, amount))

    def _recv_orderStatusEvent(self, trade):
        if "order_update" in self._callbacks:
            self._trigger_callbacks("order_update", args=(trade,))

    def _recv_newOrderEvent(self, order):
        if "new_order" in self._callbacks:
            self._trigger_callbacks("new_order", args=(order,))

    def _subscribe_all(self):
        self._ib.disconnectedEvent += self._recv_disconnectEvent
        self._ib.connectedEvent += self._recv_connectedEvent
        self._ib.errorEvent += self._recv_errorEvent
        self._ib.accountValueEvent += self._recv_accountValueEvent
        self._ib.positionEvent += self._recv_positionEvent
        self._ib.orderStatusEvent += self._recv_orderStatusEvent
        self._ib.newOrderEvent += self._recv_newOrderEvent


    def _trigger_callbacks(self, event_name, args=(), kwargs={}):
        for cb in self._callbacks[event_name]:
            self._loop.create_task(cb(*args, **kwargs))

    def _allow_retries(self, func, count=1, delay=0.5):
        async def wrapper(*args, **kwargs):
            retries = 0
            while True:
                try:
                    await self._ensure_connection(timeout=1)
                    return await func(*args, **kwargs)
                except TypeError as e:
                    raise
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



