from trisigma import base
import logging

class BrokerageConsumerRabbitMQ(base.BaseConsumerRabbitMQ):

    def __init__(self, target_agent, logger=None, **conn_params):
        target_agent = f"brokerage::{target_agent}"
        self._logger = logger or logging.getLogger(__name__)
        super().__init__(target_agent, logger=logger, **conn_params)

    async def place_order(self, order_request):
        self._logger.info("[ORQ] Dispatching order request")
        order_request['instrument'] = str(order_request['instrument'])
        params = dict(order_request=order_request)
        return await self.request("place_order", params)

    async def modify_order(self, order_modification, account):
        params = dict(order_modification=order_modification, account=account)
        return await self.request("modify_order", params)

    async def cancel_order(self, order, account):
        params = dict(order=order, account=account)
        return await self.request("cancel_order", params)

    async def get_position(self, asset, account):
        params = dict(asset=asset, account=account)
        return await self.request("get_position", params)

    async def get_order_status(self, order_id, account):
        params = dict(order_id=order_id, account=account)
        return await self.request("get_order_status", params)

    async def get_orders(self, account):
        params = dict(account=account)
        return await self.request("get_orders", params)

    def on_position_update(self, fn):
        event_name = f"position_update"
        self.subscribe(event_name, fn)
        return fn

    def on_order_update(self, fn):
        event_name = f"order_update"
        self.subscribe(event_name, fn)
        return fn

    def on_new_order(self, fn):
        event_name = f"new_order"
        self.subscribe(event_name, fn)
        return fn

