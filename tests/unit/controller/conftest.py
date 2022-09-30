import pytest
from pymergen.controller.controller import Controller, ControllerCpu, ControllerMemory
from pymergen.controller.group import ControllerGroup


@pytest.fixture
def basic_controller():
    controller = Controller("test")
    return controller


@pytest.fixture
def cpu_controller():
    return ControllerCpu()


@pytest.fixture
def memory_controller():
    return ControllerMemory()


@pytest.fixture
def basic_group():
    return ControllerGroup("test_group")


@pytest.fixture
def group_with_controllers():
    group = ControllerGroup("test_group")
    cpu = ControllerCpu()
    cpu.add_limit("weight", 100)
    memory = ControllerMemory()
    memory.add_limit("limit_in_bytes", "1G")

    group.add_controller(cpu)
    group.add_controller(memory)

    return group
