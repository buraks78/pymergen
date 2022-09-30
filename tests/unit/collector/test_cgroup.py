import os
import pytest
import tempfile
from unittest.mock import MagicMock, patch, mock_open, PropertyMock
from io import StringIO
from pymergen.collector.collector import Collector
from pymergen.collector.process import CollectorProcess
from pymergen.collector.thread import CollectorThread
from pymergen.collector.perf import CollectorPerfEvent
from pymergen.collector.perf import CollectorPerfStat
from pymergen.collector.perf import CollectorPerfProfile
from pymergen.collector.cgroup import (
    CollectorControllerGroupFile,
    CollectorControllerGroupStatParser,
    CollectorControllerGroupStatLogger,
    CollectorControllerGroup
)


class TestCollectorControllerGroupFile:
    def test_init(self):
        """Test file initialization"""
        file = CollectorControllerGroupFile("/path/to/file", "r")
        assert file._path == "/path/to/file"
        assert file._mode == "r"
        assert file._fh is None

    @patch('builtins.open')
    def test_fh_property(self, mock_open_func):
        """Test fh property initializes file handle"""
        mock_file = MagicMock()
        mock_open_func.return_value = mock_file

        file = CollectorControllerGroupFile("/path/to/file", "r")
        result = file.fh

        mock_open_func.assert_called_once_with("/path/to/file", "r")
        assert result is mock_file
        assert file._fh is mock_file

    @patch('builtins.open')
    def test_del_closes_file(self, mock_open_func):
        """Test __del__ method closes file handle"""
        mock_file = MagicMock()
        mock_file.closed = False
        mock_open_func.return_value = mock_file

        file = CollectorControllerGroupFile("/path/to/file", "r")
        _ = file.fh  # Access to initialize file handle

        # Call __del__ manually
        file.__del__()

        mock_file.close.assert_called_once()


class TestCollectorControllerGroupStatParser:
    def setup_method(self):
        # Clear singleton instances between tests
        CollectorControllerGroupStatParser._instances = {}

    def test_instance_singleton(self):
        """Test instance method creates singleton instances"""
        parser1 = CollectorControllerGroupStatParser.instance("/path/to/file", "r")
        parser2 = CollectorControllerGroupStatParser.instance("/path/to/file", "r")
        parser3 = CollectorControllerGroupStatParser.instance("/different/path", "r")

        assert parser1 is parser2
        assert parser1 is not parser3

    @patch('builtins.open')
    def test_parse_headers_two_column_format(self, mock_open_func):
        """Test parsing headers from two-column stat format"""
        mock_file = StringIO("usage_usec 76128949\nuser_usec 45340836\nsystem_usec 30788112\n")
        mock_file.close = MagicMock()
        mock_open_func.return_value = mock_file

        parser = CollectorControllerGroupStatParser.instance("/path/to/file", "r")
        headers = parser.parse_headers()

        assert headers == ["timestamp", "usage_usec", "user_usec", "system_usec"]

    @patch('builtins.open')
    def test_parse_headers_equal_sign_format(self, mock_open_func):
        """Test parsing headers from key=value format"""
        mock_file = StringIO("some avg10=0.00 avg60=0.00 avg300=0.00 total=219731\nfull avg10=0.00 avg60=0.00 avg300=0.00 total=146364\n")
        mock_file.close = MagicMock()
        mock_open_func.return_value = mock_file

        parser = CollectorControllerGroupStatParser.instance("/path/to/file", "r")
        headers = parser.parse_headers()

        assert headers == ["timestamp", "some_avg10", "some_avg60", "some_avg300", "some_total", "full_avg10", "full_avg60", "full_avg300", "full_total"]

    @patch('builtins.open')
    def test_parse_headers_invalid_format(self, mock_open_func):
        """Test parsing headers with invalid format raises exception"""
        mock_file = StringIO("invalid\n")
        mock_file.close = MagicMock()
        mock_open_func.return_value = mock_file

        parser = CollectorControllerGroupStatParser.instance("/path/to/file", "r")
        with pytest.raises(Exception) as excinfo:
            parser.parse_headers()
        assert "Unable to parse headers" in str(excinfo.value)

    @patch('builtins.open')
    def test_parse_values_two_column_format(self, mock_open_func):
        """Test parsing values from two-column stat format"""
        mock_file = StringIO("usage_usec 76128949\nuser_usec 45340836\nsystem_usec 30788112\n")
        mock_file.close = MagicMock()
        mock_open_func.return_value = mock_file

        parser = CollectorControllerGroupStatParser.instance("/path/to/file", "r")

        with patch('pymergen.collector.cgroup.datetime') as mock_datetime:
            mock_datetime.now().isoformat.return_value = "2023-01-01T00:00:00"
            values = parser.parse_values()

        assert values[0] == "2023-01-01T00:00:00" # timestamp
        assert values[1:] == ["76128949", "45340836", "30788112"]

    @patch('builtins.open')
    def test_parse_values_equal_sign_format(self, mock_open_func):
        """Test parsing values from key=value format"""
        mock_file = StringIO("some avg10=0.00 avg60=0.11 avg300=0.22 total=219731\nfull avg10=0.33 avg60=0.44 avg300=0.55 total=146364\n")
        mock_file.close = MagicMock()
        mock_open_func.return_value = mock_file

        parser = CollectorControllerGroupStatParser.instance("/path/to/file", "r")

        with patch('pymergen.collector.cgroup.datetime') as mock_datetime:
            mock_datetime.now().isoformat.return_value = "2023-01-01T00:00:00"
            values = parser.parse_values()

        assert values[0] == "2023-01-01T00:00:00" # timestamp
        assert values[1:] == ["0.00", "0.11", "0.22", "219731", "0.33", "0.44", "0.55", "146364"]


class TestCollectorControllerGroupStatLogger:
    def setup_method(self):
        # Clear singleton instances between tests
        CollectorControllerGroupStatLogger._instances = {}

    def test_init(self):
        """Test logger initialization"""
        logger = CollectorControllerGroupStatLogger("/path/to/file", "a")
        assert logger._path == "/path/to/file"
        assert logger._mode == "a"
        assert logger._fh is None
        assert logger._is_first_call is True

    def test_instance_singleton(self):
        """Test instance method creates singleton instances"""
        logger1 = CollectorControllerGroupStatLogger.instance("/path/to/file", "a")
        logger2 = CollectorControllerGroupStatLogger.instance("/path/to/file", "a")
        logger3 = CollectorControllerGroupStatLogger.instance("/different/path", "a")

        assert logger1 is logger2
        assert logger1 is not logger3

    def test_is_first_call_property(self):
        """Test is_first_call property toggle behavior"""
        logger = CollectorControllerGroupStatLogger.instance("/path/to/file", "a")

        # First call should return True and toggle the flag
        assert logger.is_first_call is True
        # Subsequent calls should return False
        assert logger.is_first_call is False
        assert logger.is_first_call is False

    @patch('builtins.open')
    def test_log_line(self, mock_open_func):
        """Test log_line method writes and flushes"""
        mock_file = MagicMock()
        mock_open_func.return_value = mock_file

        logger = CollectorControllerGroupStatLogger.instance("/path/to/file", "a")
        logger.log_line("test data")

        mock_file.write.assert_called_once_with("test data\n")
        mock_file.flush.assert_called_once()


class TestCollectorControllerGroup:
    @pytest.mark.skip
    @patch('pymergen.collector.cgroup.time.sleep')
    @patch('pymergen.collector.cgroup.os.path.join')
    @patch('pymergen.collector.cgroup.CollectorControllerGroupStatLogger.instance')
    @patch('pymergen.collector.cgroup.CollectorControllerGroupStatParser.instance')
    def test_run(self, mock_parser_instance, mock_logger_instance, mock_join, mock_sleep):
        """Test the run method of CollectorControllerGroup"""
        # Setup mocks
        mock_executor = MagicMock()
        mock_executor.run_path.return_value = "/test/run/path"

        mock_join.side_effect = lambda *args: os.path.join(*args)

        mock_logger = MagicMock()
        mock_logger.is_first_call = True
        mock_logger_instance.return_value = mock_logger

        mock_parser = MagicMock()
        mock_parser.parse_headers.return_value = ["header1", "header2"]
        mock_parser.parse_values.return_value = ["value1", "value2"]
        mock_parser_instance.return_value = mock_parser

        # Create test data
        mock_controller = MagicMock()
        mock_controller.stat_files = ["stat.file1", "stat.file2"]

        mock_cgroup = MagicMock()
        mock_cgroup.name = "test_cgroup"
        mock_cgroup.DIR_BASE = "/sys/fs/cgroup"
        mock_cgroup.controllers = [mock_controller]

        mock_parent_context = MagicMock()
        mock_parent_context.cgroups = [mock_cgroup]

        # Create collector and set it up for testing
        collector = CollectorControllerGroup()
        collector.ramp = 0  # No delay for testing
        collector.interval = 0.1  # Small interval for testing
        collector._executor = mock_executor

        # Set up the join behavior - run once then exit
        def set_join():
            collector._join = True
        mock_sleep.side_effect = [None, set_join]  # First sleep does nothing, second sets join flag

        # Execute
        collector.run(mock_parent_context)

        # Verify
        assert mock_sleep.call_count == 2

        # Verify each stat file is processed
        assert mock_logger_instance.call_count == 2  # Once for each stat file
        assert mock_parser_instance.call_count == 2

        # Verify logger operations
        assert mock_logger.log_line.call_count == 4  # Two calls for each stat file (headers + values)

        # Verify expected paths were used
        expected_log_paths = [
            "/test/run/path/collector.cgroup_test_cgroup_stat_file1.log",
            "/test/run/path/collector.cgroup_test_cgroup_stat_file2.log"
        ]
        expected_stat_paths = [
            "/sys/fs/cgroup/test_cgroup/stat.file1",
            "/sys/fs/cgroup/test_cgroup/stat.file2"
        ]

        mock_logger_instance.assert_any_call(expected_log_paths[0], 'a')
        mock_logger_instance.assert_any_call(expected_log_paths[1], 'a')
        mock_parser_instance.assert_any_call(expected_stat_paths[0], 'r')
        mock_parser_instance.assert_any_call(expected_stat_paths[1], 'r')

    @patch('pymergen.collector.process.AsyncProcessExecutor')
    def test_process_collector_lifecycle(self, mock_executor_class):
        """Test full lifecycle of a process collector"""
        # Setup
        mock_executor = MagicMock()
        mock_executor_class.return_value = mock_executor

        # Create and configure collector
        collector = CollectorProcess()
        collector.context = MagicMock()
        collector.name = "test_process_collector"
        collector.cmd = "perf stat -a"

        # Start collector
        parent_context = MagicMock()
        collector.start(parent_context)

        # Verify executor was created and started
        assert collector._executor is mock_executor
        mock_executor_class.assert_called_once()
        mock_executor.execute.assert_called_once_with(parent_context)

        # Stop collector
        collector.stop()

        # Verify executor was stopped
        mock_executor.execute_stop.assert_called_once()

    @patch('pymergen.collector.process.AsyncProcessExecutor')
    def test_perf_collector_configuration(self, mock_executor_class):
        """Test configuration and command generation for perf collectors"""
        # Setup
        mock_executor = MagicMock()
        mock_executor_class.return_value = mock_executor

        # Create and configure PerfStat collector
        collector = CollectorPerfStat()
        collector.context = MagicMock()
        collector.name = "perf_stat_collector"
        collector.add_cgroup_event("test_cgroup", "cpu-cycles")
        collector.add_system_event("page-faults")

        # Verify command generation
        cmd = collector.cmd
        assert "perf stat record" in cmd
        assert "-o {m:context:run_path}/collector.perf_stat.data" in cmd
        assert "-e '{cpu-cycles}'" in cmd
        assert "-G test_cgroup" in cmd
        assert "-a" in cmd
        assert "-e '{page-faults}'" in cmd

        # Start collector
        parent_context = MagicMock()
        collector.start(parent_context)

        # Verify executor was created with correct command
        command_arg = mock_executor_class.call_args[0][1]
        assert command_arg.cmd == cmd

    def test_collector_hierarchy(self):
        """Test the inheritance hierarchy of collectors"""
        assert issubclass(CollectorProcess, Collector)
        assert issubclass(CollectorThread, Collector)
        assert issubclass(CollectorControllerGroup, CollectorThread)
        assert issubclass(CollectorPerfStat, CollectorPerfEvent)
        assert issubclass(CollectorPerfProfile, CollectorPerfEvent)