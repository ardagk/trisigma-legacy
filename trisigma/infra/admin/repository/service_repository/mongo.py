from pymongo import MongoClient
from trisigma import irepo
import time

class ServiceRepositoryMongo (irepo.ServiceRepository):

    DB_NAME = 'system'
    COLL_NAME = 'services'

    def __init__(self, host='localhost', port=27017):
        self.client = MongoClient(host, port)
        self.db = self.client[self.DB_NAME]
        self.cursor = self.client[self.DB_NAME][self.COLL_NAME]

    def service_exists(self, service):
        res = self.cursor.find_one(
            {'name': service.name, 'target': service.target})
        return bool(res)

    def declare_service(self, service):
        cur_time = int(time.time())
        init_schema = {
            "name": service.name,
            "target": service.target,
            "meta": service.meta,
            "created_at": cur_time,
            "status": self.status.UP,
            "last_heartbeat": cur_time,
            "workflows":[],
        }
        self.cursor.update_one(
            {'name': service.name, 'target': service.target},
            {'$set': init_schema},
            upsert=True)

    def remove_service(self, service):
        self.cursor.delete_one(
            {'name': service.name, 'target': service.target}
        )

    def update_service_status(self, service, status):
        self.cursor.update_one(
            {'name': service.name, 'target': service.target},
            {'$set': {'status': status}})

    def update_service_heartbeat(self, service):
        cur_time = int(time.time())
        self.cursor.update_one(
            {'name': service.name, 'target': service.target},
            {'$set': {'last_heartbeat': cur_time}})

    def get_service_details(self, service):
        result = self.cursor.find_one(
            {'name': service.name, 'target': service.target},
            {'workflows': 0, '_id': 0})
        return result

    def get_all_service_details(self):
        cursor = self.cursor.find({}, {'workflows': 0, '_id': 0})
        result = list(cursor)
        return result

    def workflow_exists(self, workflow):
        res = self.cursor.find_one(
            {'name': workflow.service.name, 'target': workflow.service.target},
            {'workflows': {'$elemMatch': {'name': workflow.name}}, '_id': 0})
        return bool(res)

    def declare_workflow(self, workflow):
        #push only if not exists, if it does, overwrite
        if self.workflow_exists(workflow):
            self.remove_workflow(workflow)
        cur_time = int(time.time())
        service = {
            'name': workflow.service.name,
            'target': workflow.service.target}
        self.cursor.update_one(
            service,
            {'$push': {'workflows': {
                'name': workflow.name,
                'created_at': cur_time,
                'status': self.status.UP,
                'last_progress': cur_time,
            }}})

    def remove_workflow(self, workflow):
        self.cursor.update_one(
            {'name': service.name, 'target': service.target},
            {'$pull': {'workflows': {'name': workflow.name}}})

    def update_workflow_status(self, workflow, status):
        service = {
            'name': workflow.service.name,
            'target': workflow.service.target}
        self.cursor.update_one(
            service,
            {'$set': {'workflows.$[elem].status': status}},
            array_filters=[{'elem.name': workflow.name}])

    def update_workflow_progress(self, workflow):
        cur_time = int(time.time())
        service = {
            'name': workflow.service.name,
            'target': workflow.service.target}
        self.cursor.update_one(
            service,
            {'$set': {'workflows.$[elem].last_progress': cur_time}},
            array_filters=[{'elem.name': workflow.name}])

    def get_all_workflow_details(self, service):
        #remove
        result = self.cursor.find_one(
            {'name': service.name, 'target': service.target},
            {'workflows': 1, '_id': 0})
        return result['workflows']

    def get_workflow_details(self, workflow):
        #only fetch the specified workflow as well as it's fields except _id
        result = self.cursor.find_one(
            {'name': workflow.service.name, 'target': workflow.service.target},
            {'workflows': {'$elemMatch': {'name': workflow.name}}, '_id': 0})
        return result
