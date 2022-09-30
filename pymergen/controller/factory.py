from pymergen.controller.controller import Controller
from pymergen.controller.controller import ControllerCpuset
from pymergen.controller.controller import ControllerCpu
from pymergen.controller.controller import ControllerIo
from pymergen.controller.controller import ControllerMemory
from pymergen.controller.controller import ControllerHugeTlb
from pymergen.controller.controller import ControllerPids
from pymergen.controller.controller import ControllerRdma
from pymergen.controller.controller import ControllerMisc


class ControllerFactory:

    @staticmethod
    def instance(name) -> Controller:
        if name == Controller.TYPE_CPUSET:
            return ControllerCpuset()
        if name == Controller.TYPE_CPU:
            return ControllerCpu()
        if name == Controller.TYPE_IO:
            return ControllerIo()
        if name == Controller.TYPE_MEMORY:
            return ControllerMemory()
        if name == Controller.TYPE_HUGETLB:
            return ControllerHugeTlb()
        if name == Controller.TYPE_PIDS:
            return ControllerPids()
        if name == Controller.TYPE_RDMA:
            return ControllerRdma()
        if name == Controller.TYPE_MISC:
            return ControllerMisc()
        raise Exception("Controller name {name} is not recognized".format(name=name))
