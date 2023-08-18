class BrokerageAccount:

    __slots__ = ['name', 'platform']

    name: str
    platform: str

    def __init__(self, name, platform):
        self.name = name
        self.platform = platform

