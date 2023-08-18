import pytz
from trisigma import dtype
from . import config
import pymongo
from datetime import datetime

class MongoConnector(dtype.Middleware):

    def __init__ (self):
        self.client = pymongo.MongoClient(config.HOST)

    def connect(self, db, mode):
        return self.client[db]

    def exists(self, dbo, coll):
        return coll in dbo.list_collection_names()

    def create_collection(self, dbo, *args, **kwargs):
        return dbo.create_collection(*args, **kwargs)

    def mongo_datetime(self, timestamp):
        return datetime.utcfromtimestamp(timestamp).replace(tzinfo=pytz.utc)

    def mongo_timestamp(self, dt):
        # pymongo dumbass will still return timezone-naive utc,
        # so assign it first
        return int(dt.replace(tzinfo=pytz.utc).timestamp())
