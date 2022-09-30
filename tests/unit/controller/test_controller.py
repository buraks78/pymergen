import pytest
from pymergen.controller.controller import (
    Controller, ControllerCpuset, ControllerCpu, ControllerIo, 
    ControllerMemory, ControllerHugeTlb, ControllerPids, 
    ControllerRdma, ControllerMisc
)


class TestController:
    def test_init(self):
        controller = Controller("test")
        assert controller.name == "test"
        assert controller.limits == {}
        assert controller.stat_files == []

    def test_add_limit(self):
        controller = Controller("test")
        controller.add_limit("limit1", 100)
        controller.add_limit("limit2", "value")
        assert controller.limits == {"limit1": 100, "limit2": "value"}

    def test_add_stat_file(self):
        controller = Controller("test")
        controller.add_stat_file("stat1.file")
        controller.add_stat_file("stat2.file")
        assert controller.stat_files == ["stat1.file", "stat2.file"]

    def test_limits_setter(self):
        controller = Controller("test")
        limits = {"key1": "val1", "key2": 200}
        controller.limits = limits
        assert controller.limits == limits

    def test_stat_files_setter(self):
        controller = Controller("test")
        files = ["file1", "file2"]
        controller.stat_files = files
        assert controller.stat_files == files


class TestControllerSubclasses:
    def test_controller_cpuset(self):
        cpuset = ControllerCpuset()
        assert cpuset.name == Controller.TYPE_CPUSET

    def test_controller_cpu(self):
        cpu = ControllerCpu()
        assert cpu.name == Controller.TYPE_CPU
        assert "cpu.stat" in cpu.stat_files

    def test_controller_io(self):
        io = ControllerIo()
        assert io.name == Controller.TYPE_IO
        assert "io.stat" in io.stat_files

    def test_controller_memory(self):
        memory = ControllerMemory()
        assert memory.name == Controller.TYPE_MEMORY
        assert "memory.stat" in memory.stat_files
        assert "memory.numa_stat" in memory.stat_files

    def test_controller_hugetlb(self):
        hugetlb = ControllerHugeTlb()
        assert hugetlb.name == Controller.TYPE_HUGETLB
        assert "hugetlb.1GB.numa_stat" in hugetlb.stat_files
        assert "hugetlb.2MB.numa_stat" in hugetlb.stat_files

    def test_controller_pids(self):
        pids = ControllerPids()
        assert pids.name == Controller.TYPE_PIDS

    def test_controller_rdma(self):
        rdma = ControllerRdma()
        assert rdma.name == Controller.TYPE_RDMA

    def test_controller_misc(self):
        misc = ControllerMisc()
        assert misc.name == Controller.TYPE_MISC
