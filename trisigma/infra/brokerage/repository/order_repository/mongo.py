from pymongo import MongoClient
from trisigma import entity

class OrderRepositoryMongo:

    DB_NAME = 'orders'

    def __init__(self, host='localhost', port=27017):
        self.client = MongoClient(host, port)
        self.db = self.client[self.DB_NAME]

    def get_order_requests(self, instrument=None, account_name=None, timespan=None):
        query = {}
        if instrument is not None:
            query['instrument'] = str(instrument)
        if account_name:
            query['account_name'] = account_name
        if timespan:
            query['time'] = {'$gt': timespan.start.timestamp(), '$lt': timespan.end.timestamp()}
        cur = self.db['order_requests'].find(query, {'_id': 0})
        result = []
        for doc in cur:
            doc['instrument'] = entity.Instrument.parse(doc['instrument'])
            result.append(doc)
        return result

    def add_order_request(self, order_request):
        order_request['instrument'] = str(order_request['instrument'])
        self.db['order_requests'].insert_one(order_request)

    def get_order_executions(self, instrument=None, account_name=None, timespan=None):
        query = {}
        if instrument is not None:
            query['instrument'] = str(instrument)
        if account_name:
            query['account_name'] = account_name
        if timespan:
            query['time'] = {'$gt': timespan.start.timestamp(), '$lt': timespan.end.timestamp()}
        cur = self.db['order_executions'].find(query, {'_id': 0})
        result = list(cur)
        return result

    def add_order_execution(self, order_execution):
        self.db['order_executions'].insert_one(order_execution)

    def add_order_misc(self, order_misc, _id_key, coll):
        """
        Upsert `order_misc` to collection `coll` by the string `_id_key`.
        """
        _id = order_misc[_id_key]
        self.db[coll].update_one(
            {_id_key: _id},
            {'$set': order_misc},
            upsert=True
        )

