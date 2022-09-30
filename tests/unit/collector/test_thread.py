import pytest
from unittest.mock import MagicMock, patch
from pymergen.collector.thread import CollectorThread
from pymergen.core.executor import AsyncThreadExecutor


class TestCollectorThread:
    def test_init(self):
        """Test thread collector initialization"""
        collector = CollectorThread()
        assert collector._name is None
        assert collector._context is None
        assert collector._executor is None
        assert collector._join is False
        assert collector._ramp == CollectorThread.DEFAULT_RAMP
        assert collector._interval == CollectorThread.DEFAULT_INTERVAL

    def test_parse(self):
        """Test parsing configuration"""
        collector = CollectorThread()
        config = {
            "name": "test_collector",
            "ramp": 5,
            "interval": 10
        }
        collector.parse(config)
        assert collector.name == "test_collector"
        assert collector.ramp == 5
        assert collector.interval == 10

    def test_parse_defaults(self):
        """Test parsing configuration with defaults"""
        collector = CollectorThread()
        config = {
            "name": "test_collector"
        }
        collector.parse(config)
        assert collector.name == "test_collector"
        assert collector.ramp == CollectorThread.DEFAULT_RAMP
        assert collector.interval == CollectorThread.DEFAULT_INTERVAL

    def test_ramp_property(self):
        """Test ramp property getter and setter"""
        collector = CollectorThread()
        assert collector.ramp == CollectorThread.DEFAULT_RAMP

        collector.ramp = 5
        assert collector.ramp == 5

    def test_interval_property(self):
        """Test interval property getter and setter"""
        collector = CollectorThread()
        assert collector.interval == CollectorThread.DEFAULT_INTERVAL

        collector.interval = 10
        assert collector.interval == 10

    @patch('pymergen.collector.thread.AsyncThreadExecutor')
    def test_start(self, mock_executor_class):
        """Test start method"""
        # Setup
        mock_executor = MagicMock()
        mock_executor_class.return_value = mock_executor

        collector = CollectorThread()
        collector.context = MagicMock()
        parent_context = MagicMock()
        parent_context.entity = MagicMock()

        # Execute
        collector.start(parent_context)

        # Assert
        mock_executor_class.assert_called_once_with(collector.context, parent_context.entity)
        assert mock_executor.target is collector
        mock_executor.execute.assert_called_once_with(parent_context)
        assert collector._executor is mock_executor

    def test_stop(self):
        """Test stop method"""
        collector = CollectorThread()
        collector._executor = MagicMock()
        collector._join = True

        collector.stop()

        collector._executor.execute_stop.assert_called_once()
        assert collector._join is False

    def test_run_not_implemented(self):
        """Test that run method raises NotImplementedError"""
        collector = CollectorThread()
        with pytest.raises(NotImplementedError):
            collector.run(MagicMock())

    def test_join(self):
        """Test join method"""
        collector = CollectorThread()
        assert collector._join is False

        collector.join()

        assert collector._join is True
