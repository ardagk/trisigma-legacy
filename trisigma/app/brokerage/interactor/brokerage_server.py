import logging

class BrokerageServer():

    def __init__(self, consumer, producer, order_repository, logger=None):
        self._consumer = consumer
        self._producer = producer
        self._order_repository = order_repository
        self._logger = logger or logging.getLogger(__name__)
        self._producer.req_cancel_order(self._consumer.cancel_order)
        self._producer.req_place_order(self._place_order_wrapper)
        self._producer.req_modify_order(self._consumer.modify_order)
        self._producer.req_get_position(self._consumer.get_position)
        self._producer.req_get_order_status(self._consumer.get_order_status)
        self._producer.req_get_orders(self._consumer.get_orders)
        self._consumer.on_position_update(self._producer.publish_position_update)
        self._consumer.on_order_update(self._producer.publish_order_update)
        self._consumer.on_new_order(self._producer.publish_new_order)

    def connect(self):
        self._consumer.connect()
        self._producer.connect()

    def run(self):
        self._consumer.run()
        self._producer.run()

    async def _place_order_wrapper(self, order_request, account):
        _order_request = order_request.copy()
        _order_request['account'] = account
        try:
            self._order_repository.add_order_request(_order_request)
        except Exception as e:
            self._logger.error('Failed to add order request to repository: {}'.format(e))
        return await self._consumer.place_order(order_request, account)

