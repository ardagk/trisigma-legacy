from abc import ABC, abstractmethod

class Status:
    UP = 'UP'
    DOWN = 'DOWN'
    PAUSED = 'PAUSED'
    STOPPED = 'STOPPED'

class ServiceRepository (ABC):

    status = Status()

    @abstractmethod
    def service_exists(self, service): (...)

    @abstractmethod
    def declare_service(self, service): (...)

    @abstractmethod
    def remove_service(self, service): (...)

    @abstractmethod
    def update_service_status(self, service, status): (...)

    @abstractmethod
    def update_service_heartbeat(self): (...)

    @abstractmethod
    def get_service_details(self, service): (...)

    @abstractmethod
    def get_all_service_details(self): (...)

    @abstractmethod
    def workflow_exists(self, service, workflow): (...)

    @abstractmethod
    def declare_workflow(self, workflow): (...)

    @abstractmethod
    def remove_workflow(self, workflow): (...)

    @abstractmethod
    def update_workflow_status(self, workflow): (...)

    @abstractmethod
    def update_workflow_progress(self, workflow): (...)

    @abstractmethod
    def get_workflow_details(self, service, workflow): (...)

    @abstractmethod
    def get_all_workflow_details(self, service): (...)

