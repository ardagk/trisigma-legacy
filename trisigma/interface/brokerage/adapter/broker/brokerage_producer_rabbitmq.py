from trisigma import base
from trisigma import entity

class BrokerageProducerRabbitMQ (base.BaseProducerRabbitMQ):

    def __init__(self, agent_name, prefetch_count=5, logger=None, **kwargs):
        agent_name = f"brokerage::{agent_name}"
        super().__init__(agent_name, prefetch_count, logger, **kwargs)

    def req_place_order(self, fn):
        async def wrapper(order_request, account):
            order_request['instrument'] = entity.Instrument.parse(
                order_request['instrument'])
            params = dict(order_request=order_request, account=account)
            return await fn(**params)
        super().register("place_order")(wrapper)
        return wrapper

    def req_modify_order(self, fn):
        super().register("modify_order")(fn)
        return fn

    def req_cancel_order(self, fn):
        super().register("cancel_order")(fn)
        return fn

    def req_get_position(self, fn):
        super().register("get_position")(fn)
        return fn

    def req_get_order_status(self, fn):
        super().register("get_order_status")(fn)
        return fn

    def req_get_orders(self, fn):
        super().register("get_orders")(fn)
        return fn

    async def publish_position_update(self, asset, position, account):
        event_name = f"position_update.{account}"
        data = dict(account=account, asset=asset, position=position)
        await super().publish(event_name, data)

    async def publish_order_update(self, order_update, account):
        event_name = f"order_update.{account}"
        data = dict(account=account, order_update=order_update)
        await super().publish(event_name, data)

    async def publish_new_order(self, new_order, account):
        event_name = f"order_update.{account}"
        data = dict(account=account, new_order=new_order)
        await super().publish(event_name, data)



