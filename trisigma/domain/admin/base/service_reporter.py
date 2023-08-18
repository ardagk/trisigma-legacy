from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from queue import Queue
from trisigma import entity
import atexit
import logging

class BaseServiceReporter(ABC):

    meta = {}
    workflows = {}
    progress_policy = {}

    _job_queue = Queue()

    def __init__(self, name, target, service_repository, typ='generic', beat_interval = 20, beat_timeout=30):
        name = str(name)
        target = str(target)
        self.service_repository = service_repository
        self.status = self.service_repository.status
        self.service = entity.Service(name, target)
        self.BEAT_INTERVAL = beat_interval
        self.BEAT_TIMEOUT = beat_timeout
        self.service.meta = {'type': typ, 'beat_timeout': beat_timeout}
        self._job_queue.put(('VALIDATE_SERVICE', self.service))
        self._job_queue.put(('DECLARE_SERVICE', self.service))
        atexit.register(self._goodbye)

    def _goodbye(self):
        logging.critical("Service {name} - {target} is shutting down".format(
            name=self.service.name,
            target=self.service.target))

    @abstractmethod
    def start(self): (...)

    @abstractmethod
    def _worker(self): (...)

    def service_paused(self):
        self._job_queue.put(('CHANGE_SERVICE_STATUS', self.status.PAUSED))

    def service_resumed(self):
        self._job_queue.put(('CHANGE_SERVICE_STATUS', self.status.UP))

    def service_stopped(self):
        self._job_queue.put(('CHANGE_SERVICE_STATUS', self.status.STOPPED))

    def declare_workflow(self, workflow_name):
        workflow_name = str(workflow_name)
        workflow = entity.Workflow(workflow_name, self.service)
        self.workflows[workflow_name] = workflow
        self._job_queue.put(('DECLARE_WORKFLOW', workflow))

    def workflow_paused(self, workflow_name):
        workflow_name = str(workflow_name)
        workflow = self.workflows[workflow_name]
        self._job_queue.put(('CHANGE_WORKFLOW_STATUS', workflow, self.status.PAUSED))

    def workflow_resumed(self, workflow_name):
        workflow_name = str(workflow_name)
        workflow = self.workflows[workflow_name]
        self._job_queue.put(('CHANGE_WORKFLOW_STATUS', workflow, self.status.UP))

    def workflow_stopped(self, workflow_name):
        workflow_name = str(workflow_name)
        workflow = self.workflows[workflow_name]
        self._job_queue.put(('CHANGE_WORKFLOW_STATUS', workflow, self.status.STOPPED))

    def workflow_progress(self, workflow_name):
        workflow_name = str(workflow_name)
        workflow = self.workflows[workflow_name]
        self._job_queue.put(('WORKFLOW_PROGRESS', workflow))

    def set_progress_policy(self, warn_in=None, stop_in=None):
        self.progress_policy = {
            "warn_in": warn_in,
            "stop_in": stop_in}

