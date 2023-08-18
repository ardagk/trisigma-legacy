from . import config
import pymongo

class DBO:

    class Cursor:

        def __init__ (self, client, coll, mode):
            self._client = client
            self.mode = mode

        def find (self, *args, **kwargs):
            res = self._client.find(*args, **kwargs)
            return res

        def find_one (self, *args, **kwargs):
            res = self._client.find_one(*args, **kwargs)
            return res

        def insert_one (self, *args, **kwargs):
            res = self._client.insert_one(*args, **kwargs)
            return res

        def insert_many (self, *args, **kwargs):
            res = self._client.insert_many(*args, **kwargs)
            return res


    def __init__ (self, db, mode):
        self.client = pymongo.MongoClient(config.HOST)
        self.dbo = self.client[db]
        self.mode = mode

    def __getitem__ (self, key):
        return self.cursor(key)

    def cursor(self, coll):
        return self.Cursor(self.client, coll, self.mode)

    def exists(self, coll):
        return coll in self.dbo.list_collection_names()

    def create_collection(self, *args, **kwargs):
        return self.dbo.create_collection(*args, **kwargs)

