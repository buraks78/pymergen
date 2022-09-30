from typing import Dict
from pymergen.collector.collector import Collector
from pymergen.core.executor import ExecutorContext, AsyncThreadExecutor


class CollectorThread(Collector):

    DEFAULT_RAMP = 0
    DEFAULT_INTERVAL = 1

    def __init__(self):
        super().__init__()
        self._executor = None
        self._join = False
        self._ramp = self.DEFAULT_RAMP
        self._interval = self.DEFAULT_INTERVAL

    def parse(self, config: Dict) -> None:
        super().parse(config)
        self._ramp = config.get("ramp", self.DEFAULT_RAMP)
        self._interval = config.get("interval", self.DEFAULT_INTERVAL)

    @property
    def ramp(self) -> int:
        return self._ramp

    @ramp.setter
    def ramp(self, value: int) -> None:
        self._ramp = value

    @property
    def interval(self) -> int:
        return self._interval

    @interval.setter
    def interval(self, value: int) -> None:
        self._interval = value

    def start(self, parent_context: ExecutorContext) -> None:
        self._executor = AsyncThreadExecutor(self.context, parent_context.entity)
        self._executor.target = self
        self._executor.execute(parent_context)

    def stop(self) -> None:
        self._executor.execute_stop()
        # Reset value for subsequent runs
        self._join = False

    def run(self, parent_context: ExecutorContext) -> None:
        raise NotImplementedError()

    def join(self) -> None:
        self._join = True
