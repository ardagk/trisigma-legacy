import time
import threading
from trisigma import base
import queue

class ServiceReporter(base.BaseServiceReporter):
    """Works with threads"""

    def start(self):
        self._last_heartbeat = 0
        self._worker_thread = threading.Thread(target=self._worker)
        self._worker_thread.start()
        self._main_thread = threading.current_thread()

    def _worker(self):
        while True:
            #bind to queue for 1 second
            try:
                action, *opt = self._job_queue.get(timeout=0.5)
                self._resolve_job(action, *opt)
            except queue.Empty:
                #if main exits, this thread exits
                if not self._main_thread.is_alive():
                    self.service_repository.update_service_status(
                        self.service, self.status.STOPPED)
                    break
                if self._last_heartbeat + self.BEAT_INTERVAL < time.time():
                    self._heartbeat()
                    self._last_heartbeat = time.time()
            except Exception as e:
                print(e)
                break

    def _resolve_job(self, action, *opt):
        if action == 'WORKFLOW_PROGRESS':
            self.service_repository.update_workflow_progress(opt[0])
        elif action == 'CHANGE_WORKFLOW_STATUS':
            self.service_repository.update_workflow_status(opt[0], opt[1])
        elif action == 'CHANGE_SERVICE_STATUS':
            self.service_repository.update_service_status(self.service, opt[0])
        elif action == 'DECLARE_WORKFLOW':
            self.service_repository.declare_workflow(opt[0])
        elif action == 'DECLARE_SERVICE':
            self.service_repository.declare_service(self.service)
        elif action == 'VALIDATE_SERVICE':
            if self.service_repository.service_exists(self.service):
                last_beat = self.service_repository.get_service_details(
                    self.service)['last_heartbeat']
                assert last_beat < time.time() - self.BEAT_TIMEOUT, \
                "Service already exists and is alive"
        else:
            raise ValueError(f'Unknown action {action}')

    def _heartbeat(self):
        self.service_repository.update_service_heartbeat(self.service)
