from typing import List, Dict
from collections import defaultdict
from pymergen.collector.process import CollectorProcess


class CollectorPerf(CollectorProcess):

    def __init__(self):
        super().__init__()
        self._cmd_parts = list()
        self._custom = list()

    @property
    def cmd(self) -> str:
        if self._cmd is not None:
            return self._cmd
        self._prepare_cmd()
        self._cmd = " ".join(self._cmd_parts)
        return self._cmd

    def parse(self, config: Dict) -> None:
        super().parse(config)
        self._custom = config.get("custom", list())

    def _prepare_cmd(self):
        self._prepare_cmd_parts()

    def _prepare_cmd_parts(self):
        if self._custom is not None:
            self._cmd_parts.extend(self._custom)


class CollectorPerfEvent(CollectorPerf):

    def __init__(self):
        super().__init__()
        self._cgroup_events = defaultdict(list)
        self._system_events = list()

    @property
    def cgroup_events(self) -> Dict:
        return self._cgroup_events

    @cgroup_events.setter
    def cgroup_events(self, events: Dict) -> None:
        self._cgroup_events = events

    def add_cgroup_event(self, cgroup: str, name: str) -> None:
        self._cgroup_events[cgroup].append(name)

    @property
    def system_events(self) -> List:
        return self._system_events

    @system_events.setter
    def system_events(self, events: List) -> None:
        self._system_events = events

    def add_system_event(self, name: str) -> None:
        self._system_events.append(name)

    def parse(self, config: Dict) -> None:
        super().parse(config)
        for e in config["events"]:
            if "cgroup" in e:
                self.add_cgroup_event(e["cgroup"], e["name"])
            else:
                self.add_system_event(e["name"])

    def _prepare_cmd_parts(self):
        for cgroup, events in self.cgroup_events.items():
            self._cmd_parts.extend(["-e", "'{{{e}}}'".format(e=",".join(events)), "-G", cgroup])
        if len(self.system_events) > 0:
            self._cmd_parts.extend(["-a", "-e", "'{{{e}}}'".format(e=",".join(self.system_events))])
        super()._prepare_cmd_parts()


class CollectorPerfStat(CollectorPerfEvent):

    def __init__(self):
        super().__init__()

    def _prepare_cmd_parts(self):
        self._cmd_parts.extend(["perf", "stat", "record"])
        self._cmd_parts.extend(["-o", "{m:context:run_path}/collector.perf_stat.data"])
        super()._prepare_cmd_parts()


class CollectorPerfProfile(CollectorPerfEvent):

    def __init__(self):
        super().__init__()

    def _prepare_cmd_parts(self):
        self._cmd_parts.extend(["perf", "record"])
        self._cmd_parts.extend(["-o", "{m:context:run_path}/collector.perf_profile.data"])
        super()._prepare_cmd_parts()
