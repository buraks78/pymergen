import pytest
from pymergen.controller.factory import ControllerFactory
from pymergen.controller.controller import (
    Controller, ControllerCpu, ControllerMemory, ControllerCpuset, 
    ControllerIo, ControllerHugeTlb, ControllerPids, ControllerRdma, ControllerMisc
)


class TestControllerFactory:
    def test_instance_cpu(self):
        controller = ControllerFactory.instance(Controller.TYPE_CPU)
        assert isinstance(controller, ControllerCpu)
        assert controller.name == Controller.TYPE_CPU

    def test_instance_memory(self):
        controller = ControllerFactory.instance(Controller.TYPE_MEMORY)
        assert isinstance(controller, ControllerMemory)
        assert controller.name == Controller.TYPE_MEMORY

    def test_instance_cpuset(self):
        controller = ControllerFactory.instance(Controller.TYPE_CPUSET)
        assert isinstance(controller, ControllerCpuset)
        assert controller.name == Controller.TYPE_CPUSET

    def test_instance_all_types(self):
        controllers = [
            (Controller.TYPE_CPU, ControllerCpu),
            (Controller.TYPE_MEMORY, ControllerMemory),
            (Controller.TYPE_CPUSET, ControllerCpuset),
            (Controller.TYPE_IO, ControllerIo),
            (Controller.TYPE_HUGETLB, ControllerHugeTlb),
            (Controller.TYPE_PIDS, ControllerPids),
            (Controller.TYPE_RDMA, ControllerRdma),
            (Controller.TYPE_MISC, ControllerMisc)
        ]

        for controller_type, controller_class in controllers:
            controller = ControllerFactory.instance(controller_type)
            assert isinstance(controller, controller_class)
            assert controller.name == controller_type

    def test_instance_invalid_type(self):
        with pytest.raises(Exception) as exc_info:
            ControllerFactory.instance("invalid_type")
        assert "Controller name invalid_type is not recognized" in str(exc_info.value)
