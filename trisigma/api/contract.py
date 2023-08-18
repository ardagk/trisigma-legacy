from abc import ABC, abstractmethod
import json

class Serializable(ABC):
    @abstractmethod
    def serialize(self) -> dict:
        pass

    @staticmethod
    @abstractmethod
    def deserialize(data) -> object:
        pass
    def __str__(self):
        return str(self.serialize())
    def __repr__(self):
        return str(self.serialize())

    def encode(self) -> str:
        return json.dumps(self.serialize())

    @staticmethod
    def decode(data) -> object:
        return json.loads(data)
