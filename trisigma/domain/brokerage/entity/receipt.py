from dataclasses import dataclass

@dataclass
class Receipt:
    time: int
    order_id: int
    unique_id: int
    _mark: str

    def __init__(self, time, order_id, unique_id):
        self.time = time
        self.order_id = order_id
        self.unique_id = unique_id

    def mark(self, mark):
        self.mark = mark

    def serialize(self):
        return {
            "time": self.time,
            "order_id": self.order_id,
            "unique_id": self.unique_id,
            "mark": self.mark
        }

