from typing import List, Dict, Union


class Controller:

    TYPE_CPUSET = "cpuset"
    TYPE_CPU = "cpu"
    TYPE_IO = "io"
    TYPE_MEMORY = "memory"
    TYPE_HUGETLB = "hugetlb"
    TYPE_PIDS = "pids"
    TYPE_RDMA = "rdma"
    TYPE_MISC = "misc"

    def __init__(self, name):
        self._name = name
        self._limits = dict()
        self._stat_files = list()

    @property
    def name(self) -> str:
        return self._name

    @property
    def limits(self) -> Dict:
        return self._limits

    @property
    def stat_files(self) -> List:
        return self._stat_files

    @stat_files.setter
    def stat_files(self, values: List) -> None:
        self._stat_files = values

    def add_stat_file(self, value: str) -> None:
        self._stat_files.append(value)

    @limits.setter
    def limits(self, values: Dict) -> None:
        self._limits = values

    def add_limit(self, key: str, value: Union[int, float, str]) -> None:
        self._limits[key] = value


class ControllerCpuset(Controller):

    def __init__(self):
        super().__init__(Controller.TYPE_CPUSET)


class ControllerCpu(Controller):

    def __init__(self):
        super().__init__(Controller.TYPE_CPU)
        self.add_stat_file("cpu.stat")


class ControllerIo(Controller):

    def __init__(self):
        super().__init__(Controller.TYPE_IO)
        self.add_stat_file("io.stat")


class ControllerMemory(Controller):

    def __init__(self):
        super().__init__(Controller.TYPE_MEMORY)
        self.add_stat_file("memory.stat")
        self.add_stat_file("memory.numa_stat")


class ControllerHugeTlb(Controller):

    def __init__(self):
        super().__init__(Controller.TYPE_HUGETLB)
        self.add_stat_file("hugetlb.1GB.numa_stat")
        self.add_stat_file("hugetlb.2MB.numa_stat")


class ControllerPids(Controller):

    def __init__(self):
        super().__init__(Controller.TYPE_PIDS)


class ControllerRdma(Controller):

    def __init__(self):
        super().__init__(Controller.TYPE_RDMA)


class ControllerMisc(Controller):

    def __init__(self):
        super().__init__(Controller.TYPE_MISC)

