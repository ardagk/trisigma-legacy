import schedule
import queue
import asyncio
import time

class AgentHealthchecker:

    HEALTH_INFO_PATH = '/tmp/agent_health.txt'

    _checklist = {}
    _results = {}
    _is_running = False
    _task_queue = queue.Queue()

    def __init__(self, service_name, healthcheck_repository, delay=0, poll_interval=0.1):
        self._health_title = f'agent:{service_name}'
        self._delay = delay
        self._healthcheck_repository = healthcheck_repository
        self._scheduler = schedule.Scheduler()
        self._last_result_hash = None
        self._poll_interval = poll_interval
        with open(self.HEALTH_INFO_PATH, 'w') as f:
            f.write('UNHEALTHY')

    def add_condition(self, name, condition, period):
        assert not self._is_running, 'Cannot add condition while running'
        self._checklist[name] = lambda: condition()
        self._results[name] = None
        self._task_queue.put(name)
        self._scheduler.every(period).seconds.do(
            lambda: self._task_queue.put(name))

    async def start(self):
        if len(self._checklist) == 0:
            print('No healthcheck conditions')
            return
        self._is_running = True
        await asyncio.sleep(self._delay)
        while True:
            await asyncio.sleep(self._poll_interval)
            for name in self._pending_checks():
                result = await self._check(name)
                self._results[name] = result
            if self._result_hash() != self._last_result_hash:
                self._last_result_hash = self._result_hash()
                await self._report_results()

    def _pending_checks(self):
        self._scheduler.run_pending()
        while not self._task_queue.empty():
            yield self._task_queue.get()

    def _result_hash(self):
        return hash(tuple(self._results.items()))

    async def _check(self, name):
        try:
            fn = self._checklist[name]
            if asyncio.iscoroutinefunction(fn):
                return bool(await fn())
            else:
                return bool(fn())
        except:
            return False

    async def _report_results(self):
        overall_result = all(self._results.values())
        overall_result_str = 'HEALTHY' if overall_result else 'UNHEALTHY'
        with open(self.HEALTH_INFO_PATH, 'w') as f:
            f.write(overall_result_str)
        self._healthcheck_repository.push_result(
            int(time.time()), self._health_title, overall_result, self._results)


