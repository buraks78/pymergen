import pytest
from unittest.mock import MagicMock, patch
from pymergen.collector.process import CollectorProcess
from pymergen.entity.command import EntityCommand
from pymergen.core.executor import AsyncProcessExecutor


class TestCollectorProcess:
    def test_init(self):
        """Test process collector initialization"""
        collector = CollectorProcess()
        assert collector._name is None
        assert collector._context is None
        assert collector._executor is None
        assert collector._cmd is None
        assert collector._become_cmd is None
        assert collector._shell is False
        assert collector._shell_executable is None
        assert collector._pipe_stdout is None
        assert collector._pipe_stderr is None

    def test_parse(self):
        """Test parsing configuration"""
        collector = CollectorProcess()
        config = {
            "name": "test_collector",
            "cmd": "echo 'test'",
            "become_cmd": "sudo -i -u root",
            "shell": True,
            "shell_executable": "/bin/bash",
            "pipe_stdout": "/tmp/stdout.log",
            "pipe_stderr": "/tmp/stderr.log"
        }
        collector.parse(config)
        assert collector.name == "test_collector"
        assert collector.cmd == "echo 'test'"
        assert collector.become_cmd == "sudo -i -u root"
        assert collector.shell is True
        assert collector.shell_executable == "/bin/bash"
        assert collector.pipe_stdout == "/tmp/stdout.log"
        assert collector.pipe_stderr == "/tmp/stderr.log"

    def test_cmd_property(self):
        """Test cmd property getter and setter"""
        collector = CollectorProcess()
        assert collector.cmd is None

        collector.cmd = "echo 'test'"
        assert collector.cmd == "echo 'test'"

    def test_become_cmd_property(self):
        """Test become_cmd property getter and setter"""
        collector = CollectorProcess()
        assert collector.become_cmd is None

        collector.become_cmd = "sudo -u testuser"
        assert collector.become_cmd == "sudo -u testuser"

    def test_shell_property(self):
        """Test shell property getter and setter"""
        collector = CollectorProcess()
        assert collector.shell is False

        collector.shell = True
        assert collector.shell is True

    def test_shell_executable_property(self):
        """Test shell_executable property getter and setter"""
        collector = CollectorProcess()
        assert collector.shell_executable is None

        collector.shell_executable = "/bin/bash"
        assert collector.shell_executable == "/bin/bash"

    def test_pipe_stdout_property(self):
        """Test pipe_stdout property getter and setter"""
        collector = CollectorProcess()
        assert collector.pipe_stdout is None

        collector.pipe_stdout = "/tmp/stdout.log"
        assert collector.pipe_stdout == "/tmp/stdout.log"

    def test_pipe_stderr_property(self):
        """Test pipe_stderr property getter and setter"""
        collector = CollectorProcess()
        assert collector.pipe_stderr is None

        collector.pipe_stderr = "/tmp/stderr.log"
        assert collector.pipe_stderr == "/tmp/stderr.log"

    def test_command(self):
        """Test command method creates proper EntityCommand"""
        collector = CollectorProcess()
        collector.name = "test_collector"
        collector.cmd = "echo 'test'"
        collector.become_cmd = "sudo -u testuser"
        collector.shell = True
        collector.shell_executable = "/bin/bash"
        collector.pipe_stdout = "/tmp/stdout.log"
        collector.pipe_stderr = "/tmp/stderr.log"

        command = collector.command()
        assert isinstance(command, EntityCommand)
        assert command.name == "test_collector"
        assert command.cmd == "echo 'test'"
        assert command.become_cmd == "sudo -u testuser"
        assert command.shell is True
        assert command.shell_executable == "/bin/bash"
        assert command.pipe_stdout == "/tmp/stdout.log"
        assert command.pipe_stderr == "/tmp/stderr.log"

    @patch('pymergen.collector.process.AsyncProcessExecutor')
    def test_start(self, mock_executor_class):
        """Test start method"""
        # Setup
        mock_executor = MagicMock()
        mock_executor_class.return_value = mock_executor

        collector = CollectorProcess()
        collector.context = MagicMock()
        collector.name = "test_collector"
        collector.cmd = "echo 'test'"
        parent_context = MagicMock()

        # Execute
        collector.start(parent_context)

        # Assert
        mock_executor_class.assert_called_once()
        mock_executor.execute.assert_called_once_with(parent_context)
        assert collector._executor is mock_executor

    def test_stop(self):
        """Test stop method"""
        collector = CollectorProcess()
        collector._executor = MagicMock()

        collector.stop()

        collector._executor.execute_stop.assert_called_once()
