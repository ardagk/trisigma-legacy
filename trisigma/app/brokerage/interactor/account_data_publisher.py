"""
# Cache port key format
`[collection]::[key1]:[key2]:...:[keyN]`

# Position key format
`position::[acc]:[asset]`

# Orderstat key format
`orderstat::[acc]:[unique_id]`

# Broker client service key format
`heartbeat::client:binance`
"""

class AccountDataPublisher(object):

    def __init__(self, account, cache):
        self.account = account
        self.cache = cache

    def update_position(self, assets):
        buffer = {}
        for asset in assets:
            assert isinstance(asset["free"], (int, float)), "free must be a number"
            assert isinstance(asset["locked"], (int, float)), "locked must be a number"
            key = "position::{account}:{asset}".format(
                account=self.account.get_global_id(),
                asset=asset["asset"])
            value = {"free": asset["free"], "locked": asset["locked"]}
            buffer[key] = value
        self.cache.update(buffer)

    def update_order_status(self, orders):
        buffer = {}
        for order_id, status in orders:
            key = "orderstat::" + str(order_id)
            value = status
            buffer[key] = value
        self.cache.update(buffer)
