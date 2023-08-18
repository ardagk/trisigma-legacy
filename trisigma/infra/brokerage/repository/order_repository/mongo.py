from pymongo import MongoClient
from trisigma import value

class OrderRepositoryMongo:

    DB_NAME = 'orders'

    def __init__(self, host='localhost', port=27017):
        self.client = MongoClient(host, port)
        self.db = self.client[self.DB_NAME]

    def get_order_requests(self, instrument=None, account_name=None, target=None, label=None):
        query = {}
        if instrument is not None:
            query['instrument'] = str(instrument)
        if account_name:
            query['account_name'] = account_name
        if target:
            query['target'] = target
        if label:
            query['label'] = label
        cur = self.db['order_requests'].find(query, {'_id': 0})
        result = [value.OrderRequest.from_dict(doc) for doc in cur]
        return result

    def add_order_request(self, order_request):
        self.db['order_requests'].insert_one(order_request.to_dict())

    def get_order_receipts(self, instrument=None, account=None, label=None):
        query = {}
        if instrument is not None:
            query['instrument'] = str(instrument)
        if account:
            query['account'] = account.name
        if label:
            query['label'] = label
        cur = self.db['receipts'].find(query, {'_id': 0})
        result = list(cur)
        return result

    def add_order_receipt(self, order_receipt):
        self.db['receipts'].insert_one(order_receipt.copy())


