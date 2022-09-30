import os
import tempfile
import pytest
from unittest.mock import MagicMock
from pymergen.collector.collector import Collector
from pymergen.collector.thread import CollectorThread


class MockCollector(Collector):
    """A concrete implementation of the abstract Collector class for testing"""
    def __init__(self):
        super().__init__()
        self.started = False
        self.stopped = False
        self.start_context = None

    def start(self, context):
        self.started = True
        self.start_context = context

    def stop(self):
        self.stopped = True


class MockCollectorThread(CollectorThread):
    """A concrete implementation of CollectorThread for testing"""
    def __init__(self):
        super().__init__()
        self.run_called = False
        self.run_context = None

    def run(self, context):
        self.run_called = True
        self.run_context = context


@pytest.fixture
def temp_stat_dir():
    """Create a temporary directory structure mimicking cgroup stats"""
    with tempfile.TemporaryDirectory() as tmpdir:
        cgroup_dir = os.path.join(tmpdir, "test_cgroup")
        os.makedirs(cgroup_dir, exist_ok=True)

        # Create cpu.stat file
        with open(os.path.join(cgroup_dir, "cpu.stat"), "w") as f:
            f.write("usage_usec 76128949\n")
            f.write("user_usec 45340836\n")
            f.write("system_usec 30788112\n")

        # Create memory.stat file with complex format
        with open(os.path.join(cgroup_dir, "memory.stat"), "w") as f:
            f.write("anon 1234567\n")
            f.write("file 7654321\n")
            f.write("kernel 1122334\n")
            f.write("sock 5566778\n")

        # Create io.pressure file
        with open(os.path.join(cgroup_dir, "io.pressure"), "w") as f:
            f.write("some avg10=0.00 avg60=0.11 avg300=0.22 total=219731\n")
            f.write("full avg10=0.33 avg60=0.44 avg300=0.55 total=146364\n")

        yield tmpdir
