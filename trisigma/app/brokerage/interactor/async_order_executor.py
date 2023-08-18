import logging
from trisigma import flag
from trisigma import value
from contextlib import asynccontextmanager


class AsyncOrderExecutor:
    def __init__(self, account, adapter, order_repository, cache):
        self.account = account
        self.account_name = account.name
        self.place_order = adapter
        self.order_repository = order_repository
        self.cache = cache

    def request(self, *args, **kwargs):
        return value.OrderRequest(*args, account_name=self.account_name, **kwargs)

    async def send(self, order_request):
        if await self.is_blocked(order_request.instrument):
            receipt = {'order_id': None, 'status': 'BLOCKED'}
        else:
            fam = order_request.instrument.family
            receipt = self.place_order(order_request)
        logging.info("New order: {request}, Receipt: {receipt}".format(
            request=order_request,
            receipt=receipt))
        self.order_repository.add_order_request(order_request)
        self.order_repository.add_order_receipt(receipt)
        return receipt

    async def buy(self, *args, **kwargs):
        kwargs['side'] = 'BUY'
        kwargs['typ'] = 'MARKET'
        req = self.request(*args, **kwargs)
        resp = await self.send(req)
        return resp

    async def sell(self, *args, **kwargs):
        kwargs['side'] = 'SELL'
        kwargs['typ'] = 'MARKET'
        req = self.request(*args, **kwargs)
        resp = await self.send(req)
        return resp

    async def bid(self, *args, **kwargs):
        kwargs['side'] = 'BUY'
        kwargs['typ'] = 'LIMIT'
        req = self.request(*args, **kwargs)
        resp = await self.send(req)
        await self._wait_for_fill(resp['order_id'])
        return resp

    async def ask(self, *args, **kwargs):
        kwargs['side'] = 'SELL'
        kwargs['typ'] = 'LIMIT'
        req = self.request(*args, **kwargs)
        resp = await self.send(req)
        await self._wait_for_fill(resp['order_id'])
        return resp

    async def _wait_for_fill(self, order_id):
        key = "orderstat:{}".format(order_id)
        ref = lambda: self.cache[key]
        while True:
            if ref() == "FILLED":
                return
            await flag.change(ref)

    async def is_blocked(self, instrument):
        key_acc = "orderblock::{account_name}".format(
            account_name=self.account_name,
            instrument=instrument)
        if self.cache[key_acc] == True:
            return True
        key_ins = "orderblock::{account_name}:{instrument}".format(
            account_name=self.account_name,
            instrument=instrument)
        if self.cache[key_ins] == True:
            return True
        return False

    @asynccontextmanager
    async def safe_entry(self, order_request):
        exit_side = 'SELL' if order_request.side == 'BUY' else 'BUY'
        exit_request = order_request.copy()
        exit_request.side = exit_side
        entry_receipt = {}
        exit_receipt = {}
        receipts = [entry_receipt, exit_receipt]
        try:
            entry_receipt = await self.send(order_request)
            yield receipts
        except Exception as e:
            logging.error("Error in safe_entry: {}, exiting...".format(e), exc_info=True)
        finally:
            try:
                exit_receipt = await self.send(exit_request.copy())
            except Exception as e:
                logging.error("Error on exit order: {}".format(e), exc_info=True)




