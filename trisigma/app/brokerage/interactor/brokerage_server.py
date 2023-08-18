class BrokerageServer():

    def __init__(self, consumer, producer):
        self._consumer = consumer
        self._producer = producer
        self._producer.req_cancel_order(self._consumer.cancel_order)
        self._producer.req_place_order(self._consumer.place_order)
        self._producer.req_modify_order(self._consumer.modify_order)
        self._producer.req_get_position(self._consumer.get_position)
        self._producer.req_get_order_status(self._consumer.get_order_status)
        self._producer.req_get_orders(self._consumer.get_orders)
        self._producer.req_subscribe_position_update(self._consumer.subscribe_position_update)
        self._producer.req_subscribe_order_update(self._consumer.subscribe_order_update)
        self._consumer.on_position_update(self._producer.publish_position_update)
        self._consumer.on_order_update(self._producer.publish_order_update)

    def connect(self):
        self._consumer.connect()
        self._producer.connect()

    def run(self):
        self._consumer.run()
        self._producer.run()


