import os
import tempfile
import pytest
from unittest.mock import MagicMock
from pymergen.core.context import Context
from pymergen.controller.controller import Controller
from pymergen.controller.group import ControllerGroup
from pymergen.core.executor import CollectingExecutorContext


@pytest.fixture
def mock_context():
    context = MagicMock(spec=Context)
    context.run_path = "/tmp/mergen_test"
    context.logger = MagicMock()
    return context


@pytest.fixture
def temp_cgroup_stat_file():
    """Create a temporary file with mock cgroup stats content"""
    with tempfile.NamedTemporaryFile(mode='w+', delete=False) as tmp:
        tmp.write("usage_usec 76128949\n")
        tmp.write("user_usec 45340836\n")
        tmp.write("system_usec 30788112\n")
        tmp_path = tmp.name

    yield tmp_path

    # Cleanup
    if os.path.exists(tmp_path):
        os.unlink(tmp_path)


@pytest.fixture
def temp_cgroup_complex_stat_file():
    """Create a temporary file with mock complex cgroup stats content"""
    with tempfile.NamedTemporaryFile(mode='w+', delete=False) as tmp:
        tmp.write("some avg10=0.00 avg60=0.11 avg300=0.22 total=219731\n")
        tmp.write("full avg10=0.33 avg60=0.44 avg300=0.55 total=146364\n")
        tmp_path = tmp.name

    yield tmp_path

    # Cleanup
    if os.path.exists(tmp_path):
        os.unlink(tmp_path)


@pytest.fixture
def mock_controller():
    controller = MagicMock(spec=Controller)
    controller.name = "cpu"
    controller.stat_files = ["cpu.stat", "cpu.pressure"]
    return controller


@pytest.fixture
def mock_cgroup():
    cgroup = MagicMock(spec=ControllerGroup)
    cgroup.name = "test_cgroup"
    cgroup.DIR_BASE = "/sys/fs/cgroup"
    return cgroup


@pytest.fixture
def mock_collecting_executor_context(mock_cgroup, mock_controller):
    mock_cgroup.controllers = [mock_controller]

    context = MagicMock(spec=CollectingExecutorContext)
    context.cgroups = [mock_cgroup]
    context.entity = MagicMock()
    return context
