from typing import List
from .order import Order

class Portfolio:

    key: str
    position: List[dict]
    orders: List[Order]

    def __init__(self, key, position, orders):
        self.key = key
        self.position = position
        self.orders = orders
