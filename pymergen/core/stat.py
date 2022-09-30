import os
import time
import json


class StatTimer:

    def __init__(self):
        self._active = False
        self._started_at = None
        self._stopped_at = None
        self._duration = None

    @property
    def started_at(self) -> float:
        return self._started_at

    @property
    def stopped_at(self) -> float:
        return self._stopped_at

    @property
    def duration(self) -> float:
        if self._duration is None:
            self._duration = self._stopped_at - self._started_at
            self._duration = round(self._duration, 2)
        return self._duration

    def start(self) -> None:
        if self._active:
            raise Exception("Timer is already active")
        self._active = True
        self._started_at = time.time()

    def stop(self) -> None:
        if not self._active:
            raise Exception("Timer is not active")
        self._active = False
        self._stopped_at = time.time()

    def log(self, path: str) -> None:
        data = {
            "started_at": self.started_at,
            "stopped_at": self.stopped_at,
            "duration": self.duration,
        }
        log_file_path = os.path.join(path, "stat.timer.json")
        with open(log_file_path, "w") as fh:
            fh.write("{data}\n".format(data=json.dumps(data)))
            fh.flush()


class Stat:

    def __init__(self):
        self._timer = StatTimer()

    @property
    def timer(self) -> StatTimer:
        return self._timer

    def start(self) -> None:
        self._timer.start()

    def stop(self) -> None:
        self._timer.stop()

    def log(self, path: str) -> None:
        self._timer.log(path)
