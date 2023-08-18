from dataclasses import dataclass, field

@dataclass
class Service:

    name: str
    target: str
    meta: dict = field(default_factory=dict)

    def __hash__(self):
        fullname = f'{self.name}:{self.target}'
        return hash(fullname)

@dataclass
class Workflow:

    name: str
    service: Service

    def __hash__(self):
        fullname = name
        return hash(fullname)
